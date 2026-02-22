# Project Brief: Screen Feedback Agent

## Vision
Transform screen recordings with voice commentary into actionable coding tasks that AI agents can execute.

## Problem Statement
When reviewing software, we naturally:
1. Navigate through the UI
2. Encounter bugs or areas for improvement
3. Verbally comment on what should change

Currently, turning these observations into structured tasks requires:
- Rewatching the video
- Manually transcribing comments
- Writing up tickets/stories
- Context-switching between review and documentation

## Solution
A tool that:
1. Takes a screen recording with voice commentary
2. Detects speech segments automatically
3. Clips and condenses the video to relevant parts
4. Sends to Gemini Vision API for analysis
5. Outputs structured, actionable coding tasks

## User Flow

### Primary Flow (CLI)
```
User records screen → runs `sfa analyze video.mp4` → gets tasks.md
```

### Secondary Flow (WhatsApp/Clawdbot)
```
User drops video in WhatsApp → Clawdbot processes → returns tasks in chat
```

## Technical Approach

### Audio/Speech Detection
- FFmpeg `silencedetect` filter for segment boundaries
- Whisper for transcription (provides text + timing)
- Configurable silence threshold and padding

### Video Processing
- FFmpeg for clipping and concatenation
- Compression for API efficiency
- Preserve enough quality for screen content readability

### AI Analysis
- Gemini 2.0 Flash (or Pro) with video input
- Structured prompt for consistent output
- Optional: project context (README, file structure) for better suggestions

### Output Format
- Markdown with structured sections
- Machine-parseable for further automation
- Human-readable for direct use

## Success Criteria
1. ✅ Processes 30-min video in <5 minutes
2. ✅ Accurately detects 90%+ of speech segments
3. ✅ Generated tasks are actionable without rewatching video
4. ✅ Works via CLI and WhatsApp integration

## Out of Scope (v1)
- Real-time processing
- Multi-speaker detection
- Automatic PR creation
- Video hosting/storage

## Timeline
Target: MVP in 1 week (4-5 EPICs)
