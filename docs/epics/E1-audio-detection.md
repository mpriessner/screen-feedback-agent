# EPIC 1: Audio Detection & Segmentation

## Goal
Detect speech segments in video and extract timestamps for clipping.

## Stories

### E1-S1: FFmpeg Silence Detection
**Points:** 2

Implement silence detection using FFmpeg's `silencedetect` filter.

**Acceptance Criteria:**
- [ ] Function takes video path, returns list of (start, end) tuples
- [ ] Configurable silence threshold (default: -30dB)
- [ ] Configurable minimum silence duration (default: 0.5s)
- [ ] Padding configurable (default: 2s before/after)
- [ ] Unit tests with sample audio

**Technical Notes:**
```bash
ffmpeg -i video.mp4 -af silencedetect=noise=-30dB:d=0.5 -f null -
```
Parse output for `silence_start` and `silence_end` markers.

---

### E1-S2: Whisper Transcription
**Points:** 3

Integrate Whisper for transcription with timestamps.

**Acceptance Criteria:**
- [ ] Extract audio from video (ffmpeg)
- [ ] Transcribe using faster-whisper (or openai-whisper)
- [ ] Return segments with: text, start_time, end_time
- [ ] Support for multiple languages (auto-detect)
- [ ] Cache transcription results

**Dependencies:** E1-S1 (for comparison/validation)

---

### E1-S3: Segment Merger
**Points:** 2

Merge adjacent speech segments and apply padding.

**Acceptance Criteria:**
- [ ] Merge segments closer than X seconds (configurable)
- [ ] Apply start/end padding without exceeding video bounds
- [ ] Combine FFmpeg detection with Whisper timestamps
- [ ] Output final segment list for clipping

---

## Definition of Done
- All stories complete with tests
- Can process a 10-minute video and output segment list
- Accuracy validated against manual annotation
