"""Audio detection and transcription."""

import subprocess
import re
from pathlib import Path


def detect_speech_segments(
    video_path: Path,
    silence_threshold: float = -30.0,
    min_silence_duration: float = 0.5,
    padding: float = 2.0,
    verbose: bool = False,
) -> list[tuple[float, float]]:
    """Detect speech segments using FFmpeg silence detection.
    
    Args:
        video_path: Path to input video
        silence_threshold: Silence threshold in dB (default: -30dB)
        min_silence_duration: Minimum silence duration in seconds
        padding: Seconds to add before/after each segment
        verbose: Print debug output
        
    Returns:
        List of (start, end) tuples for speech segments
    """
    # Run FFmpeg silence detection
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-af", f"silencedetect=noise={silence_threshold}dB:d={min_silence_duration}",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr
    
    # Parse silence markers
    silence_starts = re.findall(r"silence_start: ([\d.]+)", output)
    silence_ends = re.findall(r"silence_end: ([\d.]+)", output)
    
    # Get video duration
    duration = get_video_duration(video_path)
    
    # Convert silence periods to speech periods
    speech_segments = []
    prev_end = 0.0
    
    for start, end in zip(silence_starts, silence_ends):
        start_f, end_f = float(start), float(end)
        if prev_end < start_f:
            # There's speech between previous silence end and current silence start
            seg_start = max(0, prev_end - padding)
            seg_end = min(duration, start_f + padding)
            speech_segments.append((seg_start, seg_end))
        prev_end = end_f
    
    # Handle trailing speech
    if prev_end < duration:
        speech_segments.append((max(0, prev_end - padding), duration))
    
    # Merge overlapping segments
    merged = merge_segments(speech_segments)
    
    if verbose:
        print(f"Detected {len(merged)} speech segments")
        for i, (s, e) in enumerate(merged):
            print(f"  {i+1}. {s:.1f}s - {e:.1f}s ({e-s:.1f}s)")
    
    return merged


def merge_segments(
    segments: list[tuple[float, float]],
    gap_threshold: float = 1.0,
) -> list[tuple[float, float]]:
    """Merge segments that are close together."""
    if not segments:
        return []
    
    merged = [segments[0]]
    for start, end in segments[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + gap_threshold:
            # Merge with previous
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    
    return merged


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def transcribe_audio(
    video_path: Path,
    segments: list[tuple[float, float]] | None = None,
    verbose: bool = False,
) -> str:
    """Transcribe audio using Whisper.
    
    TODO: Implement with faster-whisper
    """
    # Placeholder - will be implemented in E1-S2
    raise NotImplementedError("Whisper transcription not yet implemented")
