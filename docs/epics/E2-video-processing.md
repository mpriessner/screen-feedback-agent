# EPIC 2: Video Processing & Clipping

## Goal
Extract and combine video segments into a condensed output file.

## Stories

### E2-S1: Segment Extraction
**Points:** 2

Extract individual video segments based on timestamps.

**Acceptance Criteria:**
- [ ] Function takes video path + segment list
- [ ] Extracts each segment to temp file
- [ ] Preserves video quality (configurable)
- [ ] Handles edge cases (segment at start/end of video)
- [ ] Progress callback for long videos

**Technical Notes:**
```bash
ffmpeg -i input.mp4 -ss START -to END -c copy segment_N.mp4
```
Use `-c copy` for speed when possible, re-encode only if needed.

---

### E2-S2: Segment Concatenation
**Points:** 2

Combine extracted segments into single condensed video.

**Acceptance Criteria:**
- [ ] Concatenate segments in order
- [ ] Add visual separator between segments (optional)
- [ ] Include timestamp overlay (optional)
- [ ] Output in format suitable for Gemini API
- [ ] Cleanup temp files

**Technical Notes:**
```bash
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
```

---

### E2-S3: Video Compression
**Points:** 2

Optimize video size for API upload while preserving readability.

**Acceptance Criteria:**
- [ ] Target file size configurable (default: <50MB)
- [ ] Maintain resolution sufficient for screen text
- [ ] Compress audio appropriately
- [ ] Report compression ratio

**Technical Notes:**
- Max 1080p resolution
- H.264 with CRF ~28
- AAC audio 64kbps

---

## Story Files

- [E2-S1: Segment Extraction](../stories/E2-S1-segment-extraction.md)
- [E2-S2: Segment Concatenation](../stories/E2-S2-segment-concatenation.md)
- [E2-S3: Video Compression](../stories/E2-S3-video-compression.md)

## Definition of Done
- End-to-end: segments → condensed video
- Output plays correctly and is API-ready
- Processing time < 2x realtime for 1080p input
