# E1-S3: Segment Merger

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E1-S3                                  |
| **Title**    | Segment Merger                         |
| **Epic**     | E1 — Audio Detection & Segmentation    |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E1-S1, E1-S2                       |

---

## Overview

Combine speech segments from FFmpeg silence detection (E1-S1) with Whisper transcription timestamps (E1-S2) into a single, optimized segment list. Adjacent or overlapping segments are merged, padding is applied, and the final list defines exactly which portions of the video to clip.

This story bridges detection and processing — its output is the authoritative input for video clipping in Epic 2.

---

## Acceptance Criteria

- [ ] Function `merge_segments()` merges overlapping or adjacent segments within a configurable gap threshold
- [ ] Function `combine_detection_sources()` takes FFmpeg segments and Whisper segments, unions them, and produces a merged result
- [ ] Padding is applied after merging (not before) to avoid unnecessary expansion
- [ ] Final segments never overlap and are sorted by start time
- [ ] Final segment boundaries are clamped to `[0, video_duration]`
- [ ] Function `calculate_coverage()` returns statistics: total speech time, total silence removed, compression ratio
- [ ] Handles edge case where one source returns empty and the other does not
- [ ] Handles edge case where both sources return empty (returns empty list)
- [ ] Unit tests cover all merge scenarios

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/audio.py` — refine existing `merge_segments()`, add `combine_detection_sources()` and `calculate_coverage()`

### Function Signatures

```python
def merge_segments(
    segments: list[tuple[float, float]],
    gap_threshold: float = 1.0,
) -> list[tuple[float, float]]:
    """Merge segments that are closer than gap_threshold seconds."""

def combine_detection_sources(
    ffmpeg_segments: list[tuple[float, float]],
    whisper_segments: list[tuple[float, float]],
    video_duration: float,
    padding: float = 2.0,
    gap_threshold: float = 1.0,
) -> list[tuple[float, float]]:
    """Combine segments from FFmpeg and Whisper into a unified list."""

@dataclass
class SegmentCoverage:
    """Statistics about segment coverage."""
    total_speech_seconds: float
    total_video_seconds: float
    segments_count: int
    compression_ratio: float  # speech_time / video_time

def calculate_coverage(
    segments: list[tuple[float, float]],
    video_duration: float,
) -> SegmentCoverage:
    """Calculate coverage statistics for a segment list."""
```

### Data Structures

```python
@dataclass
class SegmentCoverage:
    total_speech_seconds: float
    total_video_seconds: float
    segments_count: int
    compression_ratio: float
```

### External Dependencies

None beyond standard library.

---

## Implementation Steps

1. **Refine `merge_segments()`** — the existing implementation is functional; add input validation (sort segments by start time first, handle empty list).
2. **Implement `combine_detection_sources()`**:
   a. Concatenate both segment lists.
   b. Sort by start time.
   c. Call `merge_segments()` with the configured `gap_threshold`.
   d. Apply padding: widen each segment by `padding` seconds on both sides.
   e. Clamp all boundaries to `[0, video_duration]`.
   f. Call `merge_segments()` again to collapse any overlaps introduced by padding.
   g. Return the final list.
3. **Implement `calculate_coverage()`** — sum segment durations, compute ratio vs. total video duration.
4. **Update pipeline** — in `pipeline.py`, after both detection sources run, call `combine_detection_sources()` to produce the final segment list.

### Edge Cases

- **One source empty** — e.g., Whisper finds no speech but FFmpeg detects some. Union still works; non-empty source dominates.
- **Both sources empty** — return empty list. Pipeline should handle this gracefully (skip clipping step, report "no speech detected").
- **Fully overlapping sources** — both return identical segments. Merge produces same result — no duplication.
- **Tiny gap between segments** — e.g., 0.3s gap with `gap_threshold=1.0` → segments are merged.
- **Very long video with many segments** — performance is O(n log n) due to sorting; no concern for practical video lengths.

---

## Testing Requirements

### Unit Tests — `tests/test_segment_merger.py`

```python
def test_merge_overlapping():
    """Overlapping segments are combined into one."""
    assert merge_segments([(0, 5), (3, 8)]) == [(0, 8)]

def test_merge_adjacent_within_threshold():
    """Segments within gap_threshold are merged."""
    assert merge_segments([(0, 5), (5.5, 10)], gap_threshold=1.0) == [(0, 10)]

def test_merge_separate_segments():
    """Segments beyond gap_threshold remain separate."""
    assert merge_segments([(0, 5), (8, 10)], gap_threshold=1.0) == [(0, 5), (8, 10)]

def test_merge_empty():
    """Empty input returns empty list."""
    assert merge_segments([]) == []

def test_merge_single_segment():
    """Single segment returns unchanged."""
    assert merge_segments([(2, 5)]) == [(2, 5)]

def test_merge_unsorted_input():
    """Unsorted segments are sorted before merging."""
    assert merge_segments([(5, 10), (0, 3)]) == [(0, 3), (5, 10)]

def test_combine_both_sources():
    """FFmpeg and Whisper segments are unioned and merged."""
    ffmpeg = [(0, 5), (10, 20)]
    whisper = [(3, 12)]
    result = combine_detection_sources(ffmpeg, whisper, video_duration=30.0, padding=0)
    assert result == [(0, 20)]

def test_combine_one_source_empty():
    """Works when one source returns no segments."""
    result = combine_detection_sources([(0, 5)], [], video_duration=10.0, padding=0)
    assert result == [(0, 5)]

def test_combine_both_empty():
    """Returns empty when both sources empty."""
    result = combine_detection_sources([], [], video_duration=10.0, padding=0)
    assert result == []

def test_combine_with_padding():
    """Padding expands segments and clamps to bounds."""
    result = combine_detection_sources(
        [(5, 10)], [], video_duration=20.0, padding=2.0
    )
    assert result == [(3.0, 12.0)]

def test_combine_padding_clamps_to_zero():
    """Padding at video start clamps to 0."""
    result = combine_detection_sources(
        [(1, 5)], [], video_duration=10.0, padding=3.0
    )
    assert result[0][0] == 0.0

def test_calculate_coverage():
    """Coverage statistics are correct."""
    cov = calculate_coverage([(0, 10), (20, 30)], video_duration=60.0)
    assert cov.total_speech_seconds == 20.0
    assert cov.compression_ratio == pytest.approx(1/3)
    assert cov.segments_count == 2
```

### Integration Tests

- Run full detection pipeline on a test video and verify the merged segment list is consistent (no overlaps, within bounds).

---

## Example Usage

```python
from screen_feedback_agent.audio import (
    detect_speech_segments,
    transcribe_audio,
    combine_detection_sources,
    calculate_coverage,
    get_video_duration,
)
from pathlib import Path

video = Path("recording.mp4")
duration = get_video_duration(video)

# Get segments from both sources
ffmpeg_segments = detect_speech_segments(video)
whisper_result = transcribe_audio(video)
whisper_segments = [(s.start_time, s.end_time) for s in whisper_result.segments]

# Combine and merge
final_segments = combine_detection_sources(
    ffmpeg_segments, whisper_segments,
    video_duration=duration,
    padding=2.0,
    gap_threshold=1.0,
)

# Check coverage
coverage = calculate_coverage(final_segments, duration)
print(f"Speech: {coverage.total_speech_seconds:.0f}s / {coverage.total_video_seconds:.0f}s")
print(f"Compression: {coverage.compression_ratio:.0%}")
print(f"Segments: {coverage.segments_count}")
# Speech: 180s / 600s
# Compression: 30%
# Segments: 8
```
