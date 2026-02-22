# E1-S2: Whisper Transcription

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E1-S2                                  |
| **Title**    | Whisper Transcription                  |
| **Epic**     | E1 — Audio Detection & Segmentation    |
| **Status**   | TODO                                   |
| **Points**   | 3                                      |
| **Dependencies** | E1-S1 (for segment timestamps)     |

---

## Overview

Integrate `faster-whisper` to transcribe audio from video files, producing timestamped text segments. The transcription supplements silence detection with actual speech content and provides text for Gemini's analysis prompt.

This story is critical because the transcription quality directly impacts the accuracy of the AI-generated coding tasks — Gemini uses the transcript alongside the video to understand what the user is requesting.

---

## Acceptance Criteria

- [ ] Function `transcribe_audio()` accepts a video path and returns a `TranscriptionResult` with full text and timestamped segments
- [ ] Audio is extracted from video to a temporary WAV file via FFmpeg before transcription
- [ ] Uses `faster-whisper` with configurable model size (default: `base`)
- [ ] Language is auto-detected by default, but can be overridden
- [ ] Each returned segment contains: `text`, `start_time`, `end_time`
- [ ] Optional: only transcribe within given time ranges (from E1-S1 segments) to save processing time
- [ ] Transcription results are cached to disk (keyed by video file hash + model) to avoid re-processing
- [ ] Gracefully handles videos with no audio track
- [ ] Memory usage stays reasonable for long videos (streaming/chunked processing)
- [ ] Unit tests pass with sample audio fixtures

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/audio.py` — replace `transcribe_audio()` placeholder with full implementation

### New Data Structures

```python
from dataclasses import dataclass

@dataclass
class TranscriptionSegment:
    """A single transcription segment with timing."""
    text: str
    start_time: float
    end_time: float

@dataclass
class TranscriptionResult:
    """Complete transcription output."""
    full_text: str
    segments: list[TranscriptionSegment]
    language: str
    language_probability: float
```

### Function Signatures

```python
def transcribe_audio(
    video_path: Path,
    segments: list[tuple[float, float]] | None = None,
    model_size: str = "base",
    language: str | None = None,
    cache_dir: Path | None = None,
    verbose: bool = False,
) -> TranscriptionResult:
    """Transcribe audio using faster-whisper."""

def extract_audio(
    video_path: Path,
    output_path: Path,
    start: float | None = None,
    end: float | None = None,
) -> None:
    """Extract audio track from video to WAV file."""

def _get_cache_key(video_path: Path, model_size: str) -> str:
    """Generate cache key from file hash and model."""

def _load_cached_transcription(cache_dir: Path, cache_key: str) -> TranscriptionResult | None:
    """Load transcription from cache if available."""

def _save_cached_transcription(cache_dir: Path, cache_key: str, result: TranscriptionResult) -> None:
    """Save transcription to cache."""
```

### External Dependencies

- `faster-whisper>=1.0` (already in pyproject.toml)
- `ffmpeg` (system dependency — for audio extraction)
- Standard library: `hashlib`, `json`, `tempfile`

---

## Implementation Steps

1. **Define data classes** — add `TranscriptionSegment` and `TranscriptionResult` to `audio.py`.
2. **Implement `extract_audio()`** — run `ffmpeg -i <video> -vn -acodec pcm_s16le -ar 16000 -ac 1 <output.wav>`. Support optional `start`/`end` for partial extraction. Raise `RuntimeError` if the video has no audio stream.
3. **Implement cache logic** — compute SHA-256 of the first 1MB + file size + model name as cache key. Store results as JSON in `cache_dir` (default: `~/.cache/sfa/transcriptions/`).
4. **Implement `transcribe_audio()`**:
   a. Check cache first; return early if hit.
   b. Extract audio to temp WAV.
   c. If `segments` is provided, extract only those time ranges and concatenate (or transcribe each range separately and merge).
   d. Initialize `faster-whisper` model: `WhisperModel(model_size, device="auto", compute_type="int8")`.
   e. Run transcription: `model.transcribe(audio_path, language=language)`.
   f. Collect segments into `TranscriptionSegment` objects.
   g. Build `TranscriptionResult` with joined full text, segments list, detected language.
   h. Save to cache.
   i. Clean up temp files.
5. **Wire into pipeline** — update `video.py:extract_and_combine_segments()` to call `transcribe_audio()` instead of returning placeholder text.
6. **Handle edge cases** (see below).

### Edge Cases

- **No audio track**: `ffmpeg` extraction fails → detect with `ffprobe` first, return empty `TranscriptionResult` with a warning
- **Very long video (>1hr)**: Process in chunks to limit memory; `faster-whisper` streams by default, so this should work naturally
- **Whisper model not downloaded**: `faster-whisper` auto-downloads on first use; ensure network access or pre-download in setup
- **Non-English audio**: Auto-detection handles this; `language_probability` indicates confidence
- **Segments parameter with no speech**: If all segments are empty/silent, return empty transcription

---

## Testing Requirements

### Unit Tests — `tests/test_audio_transcription.py`

```python
def test_extract_audio_creates_wav(sample_video_with_speech, tmp_path):
    """Audio extraction produces a valid WAV file."""

def test_extract_audio_partial(sample_video_with_speech, tmp_path):
    """Partial extraction respects start/end times."""

def test_extract_audio_no_audio_track(sample_video_no_audio):
    """Raises RuntimeError for video with no audio."""

def test_transcribe_returns_segments(sample_video_with_speech):
    """Transcription returns non-empty segments with timing info."""

def test_transcribe_full_text_matches_segments(sample_video_with_speech):
    """Full text is the concatenation of segment texts."""

def test_transcribe_with_segment_filter(sample_video_with_speech):
    """Passing segments parameter limits transcription scope."""

def test_transcribe_caching(sample_video_with_speech, tmp_path):
    """Second call with same video returns cached result."""

def test_transcribe_language_detection(sample_video_with_speech):
    """Language field is populated with detected language code."""

def test_cache_key_changes_with_model(sample_video_with_speech):
    """Different model sizes produce different cache keys."""
```

### Test Fixtures

Reuse fixtures from E1-S1. Add:
- `tests/fixtures/no_audio.mp4` — video-only file (no audio stream)

### Integration Tests

- Transcribe a known 10-second audio clip and assert the output contains expected keywords.
- Verify cache hit on second run (measure timing or check cache file exists).

---

## Example Usage

```python
from pathlib import Path
from screen_feedback_agent.audio import transcribe_audio, detect_speech_segments

video = Path("recording.mp4")
segments = detect_speech_segments(video)

result = transcribe_audio(video, segments=segments, model_size="base", verbose=True)

print(f"Language: {result.language} ({result.language_probability:.0%})")
print(f"Segments: {len(result.segments)}")
for seg in result.segments:
    print(f"  [{seg.start_time:.1f}s - {seg.end_time:.1f}s] {seg.text}")

# Language: en (98%)
# Segments: 5
#   [0.0s - 3.2s] So this button here doesn't work when I click it
#   [3.2s - 7.1s] It should open a modal but nothing happens
#   ...
```
