# Story E6-S1: Improved Speech Detection (Voice Only)

## Header
- **Story ID:** E6-S1
- **Title:** Improved Speech Detection — Voice Only, No Clicks
- **Epic:** E6 - Enhanced Analysis Pipeline
- **Status:** TODO
- **Points:** 3
- **Dependencies:** E1-S1, E1-S2

## Overview
Current silence detection captures ANY audio including mouse clicks, keyboard sounds, and background noise. We need to detect only actual human speech segments, ignoring mechanical sounds.

**Why this matters:** Martin's test video included click sounds that were incorrectly classified as "speech", resulting in a barely-condensed video (53s vs 57s original).

## Acceptance Criteria
- [ ] Only human voice triggers segment inclusion
- [ ] Mouse clicks, keyboard sounds ignored
- [ ] Minimum speech duration: 0.5s (ignore brief sounds)
- [ ] Padding: 2s before speech start, 2s after speech end
- [ ] Adjacent segments within 1s merged into single segment
- [ ] Silent gaps > 3s are cut out entirely

## Technical Specification

### Approach: Whisper-Based Segmentation
Instead of FFmpeg silence detection, use Whisper's word-level timestamps to identify speech segments.

```python
# src/screen_feedback_agent/audio.py

from faster_whisper import WhisperModel
from dataclasses import dataclass

@dataclass
class SpeechSegment:
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
) -> list[SpeechSegment]:
    """
    Detect speech segments using Whisper transcription.
    
    Returns segments where actual words were spoken,
    ignoring clicks and background noise.
    """
    model = WhisperModel(model_size, compute_type="int8")
    segments, info = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        vad_filter=True,  # Voice Activity Detection
        vad_parameters=dict(
            min_speech_duration_ms=500,
            min_silence_duration_ms=300,
        )
    )
    
    speech_segments = []
    for segment in segments:
        if segment.end - segment.start >= min_duration:
            speech_segments.append(SpeechSegment(
                start=max(0, segment.start - padding_before),
                end=segment.end + padding_after,
                text=segment.text.strip()
            ))
    
    # Merge overlapping/adjacent segments
    return merge_segments(speech_segments, merge_gap)
```

### VAD (Voice Activity Detection) Parameters
- `min_speech_duration_ms=500`: Ignore sounds < 0.5s
- `min_silence_duration_ms=300`: Don't split on brief pauses
- `vad_filter=True`: Enable Silero VAD preprocessing

## Implementation Steps
1. Install `faster-whisper` with VAD support
2. Create `detect_speech_segments_whisper()` function
3. Add segment merging logic
4. Update pipeline to use Whisper-based detection
5. Add tests with audio containing clicks vs speech

## Testing Requirements

### Unit Tests
```python
def test_ignores_click_sounds():
    """Mouse clicks should not create segments."""
    # Audio with only clicks, no speech
    segments = detect_speech_segments_whisper("tests/fixtures/clicks_only.wav")
    assert len(segments) == 0

def test_detects_speech():
    """Human voice creates segments."""
    segments = detect_speech_segments_whisper("tests/fixtures/speech_sample.wav")
    assert len(segments) > 0
    assert all(s.text for s in segments)

def test_merges_adjacent():
    """Segments within 1s are merged."""
    # Audio: "Hello" [0.8s pause] "World"
    segments = detect_speech_segments_whisper("tests/fixtures/short_pause.wav")
    assert len(segments) == 1  # Merged into one
```

## Example Usage
```python
segments = detect_speech_segments_whisper(
    "recording.mp4",
    padding_before=2.0,
    padding_after=2.0,
    merge_gap=1.0
)

for seg in segments:
    print(f"{seg.start:.1f}s - {seg.end:.1f}s: {seg.text[:50]}...")
```
