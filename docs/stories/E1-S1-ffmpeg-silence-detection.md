# E1-S1: FFmpeg Silence Detection

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E1-S1                                  |
| **Title**    | FFmpeg Silence Detection               |
| **Epic**     | E1 — Audio Detection & Segmentation    |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | None                               |

---

## Overview

Implement speech segment detection by inverting FFmpeg's `silencedetect` audio filter output. The function takes a video file, runs silence detection, and returns a list of time ranges where speech is present.

This is the foundational building block for the entire pipeline — all downstream processing (clipping, transcription, analysis) depends on accurate segment boundaries.

---

## Acceptance Criteria

- [ ] Function `detect_speech_segments()` accepts a video path and returns `list[tuple[float, float]]` of speech segments
- [ ] Silence threshold is configurable (default: `-30dB`)
- [ ] Minimum silence duration is configurable (default: `0.5s`)
- [ ] Padding before/after each segment is configurable (default: `2.0s`)
- [ ] Padding never produces negative start times or exceeds video duration
- [ ] Helper `get_video_duration()` correctly retrieves duration via `ffprobe`
- [ ] Handles videos with no silence (returns single segment covering full duration)
- [ ] Handles fully silent videos (returns empty list)
- [ ] Handles videos where speech starts at the very beginning or ends at the very end
- [ ] Returns segments sorted by start time with no overlaps
- [ ] Unit tests pass with sample audio fixtures
- [ ] Verbose mode prints detected segment count and timestamps

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/audio.py` — refine existing `detect_speech_segments()` and `get_video_duration()`

### Function Signatures

```python
def detect_speech_segments(
    video_path: Path,
    silence_threshold: float = -30.0,
    min_silence_duration: float = 0.5,
    padding: float = 2.0,
    verbose: bool = False,
) -> list[tuple[float, float]]:
    """Detect speech segments by inverting FFmpeg silence detection."""

def get_video_duration(video_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
```

### Data Structures

No new classes needed. Input/output uses primitive types (`Path`, `float`, `list[tuple[float, float]]`).

### External Dependencies

- `ffmpeg` and `ffprobe` must be installed on the system (not a Python package)
- Standard library: `subprocess`, `re`, `pathlib`

---

## Implementation Steps

1. **Validate input** — assert `video_path` exists and is a file.
2. **Get video duration** — call `ffprobe` to retrieve total duration; raise `RuntimeError` if ffprobe fails or returns non-numeric output.
3. **Run silence detection** — execute `ffmpeg -i <video> -af silencedetect=noise=<threshold>dB:d=<min_dur> -f null -`. Capture stderr (FFmpeg writes info messages to stderr).
4. **Parse silence markers** — use regex to extract all `silence_start: <float>` and `silence_end: <float>` pairs from stderr output.
5. **Handle mismatched pairs** — if there is one more `silence_start` than `silence_end`, the final silence extends to the video end; append `duration` as the final silence end.
6. **Invert to speech segments** — iterate silence intervals and collect the gaps as speech. Include speech before the first silence and after the last silence.
7. **Apply padding** — widen each speech segment by `padding` seconds on both sides, clamping to `[0, duration]`.
8. **Merge overlapping segments** — call `merge_segments()` to collapse overlaps introduced by padding.
9. **Return sorted segment list.**

### Edge Cases

- **No silence at all**: FFmpeg outputs no `silence_start` markers → return `[(0.0, duration)]`
- **Entire video is silent**: The single silence interval covers `[0, duration]` → no speech gaps → return `[]`
- **Single short speech burst**: One gap between two silence regions → return one segment
- **FFmpeg not installed**: `subprocess.run` raises `FileNotFoundError` → let it propagate with a descriptive message
- **Corrupted/unreadable video**: FFmpeg returns non-zero exit code → raise `RuntimeError`

---

## Testing Requirements

### Unit Tests — `tests/test_audio_silence.py`

```python
def test_detect_speech_basic(sample_video_with_speech):
    """Speech segments are correctly detected from a video with known silence gaps."""

def test_detect_speech_no_silence(sample_video_continuous_speech):
    """Video with no silence returns single full-duration segment."""

def test_detect_speech_all_silent(sample_silent_video):
    """Fully silent video returns empty list."""

def test_padding_clamps_to_bounds(sample_video_with_speech):
    """Padding does not produce negative start or exceed duration."""

def test_custom_threshold(sample_video_with_speech):
    """Different threshold values change detection results."""

def test_get_video_duration(sample_video_with_speech):
    """Duration is returned as a positive float."""

def test_verbose_output(sample_video_with_speech, capsys):
    """Verbose mode prints segment info to stdout."""

def test_ffmpeg_not_found(monkeypatch):
    """Raises FileNotFoundError when ffmpeg is not on PATH."""
```

### Test Fixtures

Create a `tests/fixtures/` directory with:
- `speech_with_gaps.mp4` — 30-second video: 5s speech, 3s silence, 10s speech, 5s silence, 7s speech (generate with ffmpeg synthetic audio)
- `continuous_speech.mp4` — 10s of continuous tone (no silence)
- `silence_only.mp4` — 10s of pure silence

Fixture generation script (`tests/generate_fixtures.sh`):
```bash
# Speech with gaps (sine tone = speech, silence = gaps)
ffmpeg -y -f lavfi -i "sine=frequency=440:duration=5" -f lavfi -i "anullsrc=d=3" \
  -f lavfi -i "sine=frequency=440:duration=10" -f lavfi -i "anullsrc=d=5" \
  -f lavfi -i "sine=frequency=440:duration=7" \
  -filter_complex "[0][1][2][3][4]concat=n=5:v=0:a=1" \
  -c:a aac tests/fixtures/speech_with_gaps.mp4

# Continuous speech
ffmpeg -y -f lavfi -i "sine=frequency=440:duration=10" -c:a aac tests/fixtures/continuous_speech.mp4

# Silence only
ffmpeg -y -f lavfi -i "anullsrc=d=10" -c:a aac tests/fixtures/silence_only.mp4
```

### Integration Tests

- Process a real short screen recording end-to-end (manual validation for CI, automated for segment count).

---

## Example Usage

```python
from pathlib import Path
from screen_feedback_agent.audio import detect_speech_segments

video = Path("recording.mp4")

# Default settings
segments = detect_speech_segments(video)
# [(0.0, 7.0), (10.0, 22.0), (27.0, 30.0)]

# Stricter detection
segments = detect_speech_segments(
    video,
    silence_threshold=-25.0,
    min_silence_duration=1.0,
    padding=1.0,
    verbose=True,
)
# Detected 2 speech segments
#   1. 0.0s - 6.0s (6.0s)
#   2. 11.0s - 21.0s (10.0s)
```
