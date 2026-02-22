"""Snap keyword screenshot extraction.

Detects when the user says "snap" (or alternatives) during a recording
and extracts the video frame at that exact moment.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .audio import SpeechSegment


@dataclass
class Snapshot:
    """A screenshot captured at a snap keyword moment."""
    timestamp: float
    image_path: Path
    context: str  # What user said around the snap


SNAP_KEYWORDS = ["snap", "screenshot", "capture", "here"]


def detect_snap_moments(
    segments: list[SpeechSegment],
    keywords: list[str] | None = None,
) -> list[tuple[float, str]]:
    """Find timestamps where the user says a snap keyword.

    Uses linear interpolation within each segment to estimate the
    timestamp of the keyword based on word position.

    Args:
        segments: Speech segments with timing and text
        keywords: Keywords to detect (default: SNAP_KEYWORDS)

    Returns:
        List of (timestamp, surrounding_context) tuples
    """
    if keywords is None:
        keywords = SNAP_KEYWORDS

    snap_moments = []

    for segment in segments:
        text_lower = segment.text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                words = segment.text.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        # Estimate timestamp via linear interpolation
                        word_ratio = i / max(len(words), 1)
                        timestamp = segment.start + (segment.end - segment.start) * word_ratio

                        # Get surrounding context (3 words before/after)
                        start_idx = max(0, i - 3)
                        end_idx = min(len(words), i + 4)
                        context = " ".join(words[start_idx:end_idx])

                        snap_moments.append((timestamp, context))

    return snap_moments


def extract_frame(
    video_path: Path,
    timestamp: float,
    output_dir: Path,
) -> Path:
    """Extract a single frame from video at timestamp.

    Uses FFmpeg to extract a high-quality PNG frame.

    Args:
        video_path: Path to source video
        timestamp: Time in seconds to extract frame
        output_dir: Directory to save the frame

    Returns:
        Path to extracted PNG image
    """
    output_path = output_dir / f"snap_{timestamp:.2f}.png"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "1",  # Highest quality
        str(output_path),
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def extract_all_snapshots(
    video_path: Path,
    segments: list[SpeechSegment],
    output_dir: Path,
    keywords: list[str] | None = None,
) -> list[Snapshot]:
    """Extract all snap-triggered screenshots from video.

    Args:
        video_path: Path to source video
        segments: Speech segments from Whisper detection
        output_dir: Directory to save extracted frames
        keywords: Keywords to detect (default: SNAP_KEYWORDS)

    Returns:
        List of Snapshot objects with timestamps, paths, and context
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    snap_moments = detect_snap_moments(segments, keywords=keywords)
    snapshots = []

    for timestamp, context in snap_moments:
        image_path = extract_frame(video_path, timestamp, output_dir)
        snapshots.append(Snapshot(
            timestamp=timestamp,
            image_path=image_path,
            context=context,
        ))

    return snapshots


def cleanup_snapshots(snapshots: list[Snapshot]) -> None:
    """Remove temporary snapshot image files.

    Args:
        snapshots: List of snapshots whose image files should be deleted
    """
    for snap in snapshots:
        if snap.image_path.exists():
            snap.image_path.unlink()
