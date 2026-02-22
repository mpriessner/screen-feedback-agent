# E2-S1: Segment Extraction

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E2-S1                                  |
| **Title**    | Segment Extraction                     |
| **Epic**     | E2 — Video Processing & Clipping       |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E1-S3 (final segment list)         |

---

## Overview

Extract individual video clips from the source recording based on the segment timestamps produced by Epic 1. Each segment is written to a temporary file preserving original quality, ready for concatenation.

This story handles the core FFmpeg clipping logic — getting precise, artifact-free cuts from the source video.

---

## Acceptance Criteria

- [ ] Function `extract_segment()` extracts a single time range from a video to an output file
- [ ] Function `extract_all_segments()` processes a full segment list, writing clips to a temp directory
- [ ] Uses `-c copy` (stream copy) by default for speed; falls back to re-encoding when copy produces artifacts
- [ ] Handles segments at the very beginning (start=0) and very end (end=duration) of the video
- [ ] Reports progress via a callback function for each completed segment
- [ ] Temp files are created in a configurable temp directory
- [ ] Raises clear error if FFmpeg fails on any segment
- [ ] No leftover temp files on error (cleanup on failure)
- [ ] Unit tests validate extraction accuracy

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/video.py` — refine existing `extract_segment()`, add `extract_all_segments()`

### Function Signatures

```python
from typing import Callable

ProgressCallback = Callable[[int, int], None]  # (current, total)

def extract_segment(
    video_path: Path,
    start: float,
    end: float,
    output_path: Path,
    use_copy: bool = True,
    verbose: bool = False,
) -> None:
    """Extract a single segment from video.

    Args:
        video_path: Source video file
        start: Start time in seconds
        end: End time in seconds
        output_path: Where to write the clip
        use_copy: Use stream copy (fast) vs re-encode (accurate)
        verbose: Print FFmpeg command details
    """

def extract_all_segments(
    video_path: Path,
    segments: list[tuple[float, float]],
    output_dir: Path | None = None,
    progress_callback: ProgressCallback | None = None,
    verbose: bool = False,
) -> list[Path]:
    """Extract all segments to individual files.

    Args:
        video_path: Source video file
        segments: List of (start, end) tuples
        output_dir: Directory for temp files (default: system temp)
        progress_callback: Called with (current_index, total_count) after each segment
        verbose: Print debug output

    Returns:
        List of paths to extracted segment files, in order
    """
```

### External Dependencies

- `ffmpeg` (system)
- Standard library: `subprocess`, `tempfile`, `pathlib`

---

## Implementation Steps

1. **Refine `extract_segment()`**:
   a. Build FFmpeg command. For copy mode: `ffmpeg -y -ss <start> -i <video> -t <duration> -c copy <output>`. Note: `-ss` before `-i` for fast seeking.
   b. For re-encode mode: `ffmpeg -y -i <video> -ss <start> -t <duration> -c:v libx264 -c:a aac <output>`. Note: `-ss` after `-i` for frame-accurate seeking.
   c. Run command, capture stdout/stderr.
   d. Check return code; raise `RuntimeError` with stderr on failure.
   e. Verify output file exists and has non-zero size.
2. **Implement `extract_all_segments()`**:
   a. Create output directory (temp or provided).
   b. Loop over segments with index.
   c. Generate output path: `segment_{i:03d}.mp4`.
   d. Call `extract_segment()` for each.
   e. Call `progress_callback(i+1, total)` after each extraction.
   f. On any failure, clean up all previously created files before re-raising.
   g. Return ordered list of paths.
3. **Update `extract_and_combine_segments()`** in `video.py` to use the new `extract_all_segments()` function.

### Edge Cases

- **Zero-duration segment** — `start == end`. Skip it (log a warning), don't call FFmpeg.
- **Very short segment (<0.1s)** — FFmpeg may produce empty/corrupt output. Set a minimum duration threshold (0.1s); skip shorter segments with a warning.
- **Segment at video boundary** — `start=0` or `end=duration`. Works normally, just ensure no off-by-one in duration calculation.
- **Stream copy produces glitchy output** — keyframe misalignment. Detect by checking output file is playable (optional) or let user pass `use_copy=False`.
- **Disk space exhaustion** — extraction of many segments fills disk. Not handled directly; rely on OS errors.

---

## Testing Requirements

### Unit Tests — `tests/test_video_extraction.py`

```python
def test_extract_single_segment(sample_video, tmp_path):
    """Extracts a segment and output file exists with expected duration."""

def test_extract_segment_copy_mode(sample_video, tmp_path):
    """Copy mode produces output quickly without re-encoding."""

def test_extract_segment_reencode_mode(sample_video, tmp_path):
    """Re-encode mode produces frame-accurate output."""

def test_extract_segment_at_start(sample_video, tmp_path):
    """Segment starting at 0.0 works correctly."""

def test_extract_segment_at_end(sample_video, tmp_path):
    """Segment ending at video duration works correctly."""

def test_extract_all_segments(sample_video, tmp_path):
    """Multiple segments are extracted to separate files."""

def test_extract_all_progress_callback(sample_video, tmp_path):
    """Progress callback is called for each segment."""

def test_extract_zero_duration_skipped(sample_video, tmp_path):
    """Zero-duration segments are skipped with warning."""

def test_extract_all_cleanup_on_error(sample_video, tmp_path, monkeypatch):
    """Temp files are cleaned up when extraction fails mid-way."""

def test_extract_ffmpeg_failure(tmp_path):
    """RuntimeError raised when FFmpeg fails."""
```

### Test Fixtures

Reuse video fixtures from E1. The `speech_with_gaps.mp4` (30s video) works for segment extraction tests.

---

## Example Usage

```python
from pathlib import Path
from screen_feedback_agent.video import extract_all_segments

video = Path("recording.mp4")
segments = [(0.0, 7.0), (10.0, 22.0), (27.0, 30.0)]

def on_progress(current, total):
    print(f"Extracting segment {current}/{total}")

clip_files = extract_all_segments(
    video, segments,
    progress_callback=on_progress,
    verbose=True,
)
# Extracting segment 1/3
# Extracting segment 2/3
# Extracting segment 3/3

print(clip_files)
# [Path('/tmp/sfa_xyz/segment_000.mp4'),
#  Path('/tmp/sfa_xyz/segment_001.mp4'),
#  Path('/tmp/sfa_xyz/segment_002.mp4')]
```
