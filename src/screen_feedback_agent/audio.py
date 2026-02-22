"""Audio detection and transcription."""

from __future__ import annotations

import subprocess
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SpeechSegment:
    """A segment of detected speech with timing and text."""
    start: float
    end: float
    text: str


def detect_speech_segments_whisper(
    audio_path: Path,
    model_size: str = "base",
    padding_before: float = 2.0,
    padding_after: float = 2.0,
    merge_gap: float = 1.0,
    min_duration: float = 0.5,
    verbose: bool = False,
) -> list[SpeechSegment]:
    """Detect speech segments using Whisper transcription with VAD.

    Uses faster-whisper with Silero VAD to detect only human speech,
    ignoring clicks, keyboard sounds, and background noise.

    Args:
        audio_path: Path to input audio/video file
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
        padding_before: Seconds to add before speech start
        padding_after: Seconds to add after speech end
        merge_gap: Maximum gap between segments to merge
        min_duration: Minimum speech duration to include
        verbose: Print debug output

    Returns:
        List of SpeechSegment with start, end, and text
    """
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, compute_type="int8")
    segments, info = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            min_speech_duration_ms=500,
            min_silence_duration_ms=300,
        ),
    )

    speech_segments = []
    for segment in segments:
        if segment.end - segment.start >= min_duration:
            speech_segments.append(SpeechSegment(
                start=max(0, segment.start - padding_before),
                end=segment.end + padding_after,
                text=segment.text.strip(),
            ))

    merged = merge_speech_segments(speech_segments, merge_gap)

    if verbose:
        print(f"Detected {len(merged)} speech segments (Whisper + VAD)")
        for i, seg in enumerate(merged):
            print(f"  {i + 1}. {seg.start:.1f}s - {seg.end:.1f}s ({seg.end - seg.start:.1f}s)")
            print(f"     {seg.text[:80]}...")

    return merged


def merge_speech_segments(
    segments: list[SpeechSegment],
    gap_threshold: float = 1.0,
) -> list[SpeechSegment]:
    """Merge SpeechSegments that are close together.

    Adjacent segments within gap_threshold seconds are combined,
    concatenating their text.
    """
    if not segments:
        return []

    merged = [SpeechSegment(
        start=segments[0].start,
        end=segments[0].end,
        text=segments[0].text,
    )]
    for seg in segments[1:]:
        prev = merged[-1]
        if seg.start <= prev.end + gap_threshold:
            merged[-1] = SpeechSegment(
                start=prev.start,
                end=max(prev.end, seg.end),
                text=f"{prev.text} {seg.text}",
            )
        else:
            merged.append(SpeechSegment(
                start=seg.start,
                end=seg.end,
                text=seg.text,
            ))

    return merged


# --- Legacy FFmpeg-based detection (kept for fallback) ---


def detect_speech_segments(
    video_path: Path,
    silence_threshold: float = -30.0,
    min_silence_duration: float = 0.5,
    padding: float = 2.0,
    verbose: bool = False,
) -> list[tuple[float, float]]:
    """Detect speech segments using FFmpeg silence detection.

    This is the legacy method that captures any audio including clicks.
    Prefer detect_speech_segments_whisper() for voice-only detection.

    Args:
        video_path: Path to input video
        silence_threshold: Silence threshold in dB (default: -30dB)
        min_silence_duration: Minimum silence duration in seconds
        padding: Seconds to add before/after each segment
        verbose: Print debug output

    Returns:
        List of (start, end) tuples for speech segments
    """
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-af", f"silencedetect=noise={silence_threshold}dB:d={min_silence_duration}",
        "-f", "null", "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    silence_starts = re.findall(r"silence_start: ([\d.]+)", output)
    silence_ends = re.findall(r"silence_end: ([\d.]+)", output)

    duration = get_video_duration(video_path)

    speech_segments = []
    prev_end = 0.0

    for start, end in zip(silence_starts, silence_ends):
        start_f, end_f = float(start), float(end)
        if prev_end < start_f:
            seg_start = max(0, prev_end - padding)
            seg_end = min(duration, start_f + padding)
            speech_segments.append((seg_start, seg_end))
        prev_end = end_f

    if prev_end < duration:
        speech_segments.append((max(0, prev_end - padding), duration))

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
    """Merge tuple segments that are close together."""
    if not segments:
        return []

    merged = [segments[0]]
    for start, end in segments[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + gap_threshold:
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
