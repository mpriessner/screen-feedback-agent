# E2-S2: Segment Concatenation

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E2-S2                                  |
| **Title**    | Segment Concatenation                  |
| **Epic**     | E2 — Video Processing & Clipping       |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E2-S1 (extracted segment files)    |

---

## Overview

Combine individually extracted video segments into a single condensed video file. Optionally add visual separators (brief fade-to-black) and timestamp overlays between segments so viewers can orient themselves in the original recording.

This produces the final condensed video that gets uploaded to Gemini for analysis.

---

## Acceptance Criteria

- [ ] Function `concatenate_segments()` joins a list of video files into one output file
- [ ] Uses FFmpeg concat demuxer with `-c copy` for speed when segments share the same codec
- [ ] Falls back to concat filter with re-encoding when codecs differ
- [ ] Optional: insert a brief visual separator (0.5s black frame) between segments
- [ ] Optional: burn timestamp overlay showing original video time for each segment
- [ ] Output format is MP4 with H.264/AAC (compatible with Gemini API)
- [ ] All temporary files (concat list, intermediate files) are cleaned up after completion
- [ ] Raises clear error if no segment files are provided
- [ ] Unit tests verify output is a valid, playable video

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/video.py` — refine existing `concatenate_segments()`, add separator and overlay support

### Function Signatures

```python
def concatenate_segments(
    segment_files: list[Path],
    output_path: Path,
    add_separators: bool = False,
    add_timestamps: bool = False,
    original_timestamps: list[tuple[float, float]] | None = None,
    verbose: bool = False,
) -> Path:
    """Concatenate video segments into a single file.

    Args:
        segment_files: Ordered list of segment video paths
        output_path: Where to write the combined video
        add_separators: Insert black frames between segments
        add_timestamps: Burn original timestamps as overlay text
        original_timestamps: Original (start, end) for each segment (needed for overlay)
        verbose: Print debug output

    Returns:
        Path to the combined video file
    """

def _create_concat_file(segment_files: list[Path], output_path: Path) -> Path:
    """Create FFmpeg concat demuxer input file."""

def _create_separator(duration: float, width: int, height: int, output_path: Path) -> None:
    """Create a black-frame video clip for use as separator."""
```

### External Dependencies

- `ffmpeg` (system)
- Standard library: `subprocess`, `tempfile`, `pathlib`

---

## Implementation Steps

1. **Validate inputs** — assert `segment_files` is non-empty, all files exist.
2. **Simple concat path (no separators/timestamps)**:
   a. Create concat file listing: `file '<path>'\n` for each segment.
   b. Run: `ffmpeg -y -f concat -safe 0 -i concat.txt -c copy <output>`.
3. **With separators**:
   a. Probe the first segment for resolution (`ffprobe` → width, height).
   b. Generate a 0.5s black separator clip matching that resolution.
   c. Interleave separator clips between each segment in the concat list.
   d. Re-encode if the separator has different codec parameters: use concat filter instead of demuxer.
4. **With timestamp overlays**:
   a. Requires re-encoding. Build an FFmpeg filter_complex that:
      - Concatenates all segments.
      - Draws text overlay per segment showing `[MM:SS - MM:SS]` from the original recording.
   b. Use `drawtext` filter: `drawtext=text='[05\:30 - 07\:15]':x=10:y=10:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5`.
   c. Apply each drawtext filter for the correct time range within the concatenated output.
5. **Write to output path** — verify output exists and is non-zero size.
6. **Cleanup** — remove concat list file and any separator clips.

### Edge Cases

- **Single segment** — just copy/re-encode directly, no concat needed.
- **Mismatched codecs between segments** — copy mode fails. Detect this from FFmpeg error, retry with re-encode.
- **Very many segments (100+)** — FFmpeg handles large concat lists fine, but may be slow with re-encoding. Log a warning.
- **Missing original_timestamps when add_timestamps=True** — raise `ValueError`.

---

## Testing Requirements

### Unit Tests — `tests/test_video_concatenation.py`

```python
def test_concatenate_two_segments(extracted_segments, tmp_path):
    """Two segments are combined into one playable file."""

def test_concatenate_single_segment(extracted_segments, tmp_path):
    """Single segment produces valid output."""

def test_concatenate_with_separators(extracted_segments, tmp_path):
    """Output duration includes separator time between segments."""

def test_concatenate_empty_list_raises(tmp_path):
    """ValueError raised for empty segment list."""

def test_concat_file_format(extracted_segments, tmp_path):
    """Concat demuxer file has correct format."""

def test_cleanup_temp_files(extracted_segments, tmp_path):
    """No leftover temp files after concatenation."""

def test_output_is_valid_mp4(extracted_segments, tmp_path):
    """Output can be probed with ffprobe successfully."""

def test_timestamps_require_original_timestamps(extracted_segments, tmp_path):
    """ValueError raised when add_timestamps=True but no original_timestamps."""
```

### Test Fixtures

Create a `conftest.py` fixture that extracts two 5-second segments from the test video, providing them as `extracted_segments`.

---

## Example Usage

```python
from pathlib import Path
from screen_feedback_agent.video import concatenate_segments

segment_files = [
    Path("/tmp/sfa/segment_000.mp4"),
    Path("/tmp/sfa/segment_001.mp4"),
    Path("/tmp/sfa/segment_002.mp4"),
]

# Simple concatenation
output = concatenate_segments(segment_files, Path("condensed.mp4"))

# With visual separators and timestamps
output = concatenate_segments(
    segment_files,
    Path("condensed.mp4"),
    add_separators=True,
    add_timestamps=True,
    original_timestamps=[(0.0, 7.0), (10.0, 22.0), (27.0, 30.0)],
    verbose=True,
)
```
