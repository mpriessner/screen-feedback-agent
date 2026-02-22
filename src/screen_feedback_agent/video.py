"""Video processing and clipping."""

import subprocess
import tempfile
from pathlib import Path


def extract_and_combine_segments(
    video_path: Path,
    segments: list[tuple[float, float]],
    output_path: Path | None = None,
    verbose: bool = False,
) -> tuple[Path, str]:
    """Extract video segments and combine into condensed output.
    
    Args:
        video_path: Path to input video
        segments: List of (start, end) tuples
        output_path: Optional output path (default: temp file)
        verbose: Print debug output
        
    Returns:
        Tuple of (condensed_video_path, transcription)
    """
    if not segments:
        raise ValueError("No segments to extract")
    
    # Create temp directory for segments
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        segment_files = []
        
        # Extract each segment
        for i, (start, end) in enumerate(segments):
            segment_file = tmpdir_path / f"segment_{i:03d}.mp4"
            extract_segment(video_path, start, end, segment_file, verbose=verbose)
            segment_files.append(segment_file)
        
        # Create concat file list
        concat_file = tmpdir_path / "concat.txt"
        with open(concat_file, "w") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")
        
        # Concatenate segments
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".mp4"))
        
        concatenate_segments(concat_file, output_path, verbose=verbose)
    
    # TODO: Transcribe in E1-S2
    transcription = "[Transcription will be generated here]"
    
    return output_path, transcription


def extract_segment(
    video_path: Path,
    start: float,
    end: float,
    output_path: Path,
    verbose: bool = False,
) -> None:
    """Extract a single segment from video."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", str(video_path),
        "-t", str(end - start),
        "-c", "copy",  # Fast copy without re-encoding
        str(output_path)
    ]
    
    if verbose:
        print(f"Extracting {start:.1f}s - {end:.1f}s")
    
    subprocess.run(cmd, capture_output=True, check=True)


def concatenate_segments(
    concat_file: Path,
    output_path: Path,
    verbose: bool = False,
) -> None:
    """Concatenate video segments."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path)
    ]
    
    if verbose:
        print(f"Concatenating to {output_path}")
    
    subprocess.run(cmd, capture_output=True, check=True)


def compress_video(
    video_path: Path,
    output_path: Path,
    max_size_mb: int = 50,
    verbose: bool = False,
) -> Path:
    """Compress video for API upload.
    
    TODO: Implement in E2-S3
    """
    raise NotImplementedError("Video compression not yet implemented")
