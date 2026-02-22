# 🎬 Screen Feedback Agent

Convert screen recordings with voice commentary into structured coding tasks.

**Problem:** You're using a tool, spot bugs or want changes, and naturally comment on them while screen recording. Turning those observations into actionable dev tasks is tedious.

**Solution:** Drop a video → get structured prompts ready for AI coding agents.

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Screen Video   │ ──▶ │  Extract Speech  │ ──▶ │  Clip Segments  │
│  + Voice Notes  │     │  (FFmpeg+Whisper)│     │  (2s padding)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Coding Prompt  │ ◀── │  Gemini Analysis │ ◀── │ Combined Video  │
│  (Markdown)     │     │  (Vision + Text) │     │  (Condensed)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Features

- 🎤 **Speech Detection** — FFmpeg silence detection + Whisper transcription
- ✂️ **Smart Clipping** — Extracts only relevant segments (2s before/after speech)
- 🎥 **Video Compression** — Condensed video for efficient API usage
- 🤖 **Gemini Analysis** — Vision model understands screen content + your comments
- 📝 **Structured Output** — Markdown with actionable coding tasks

## Quick Start

```bash
# Install
pip install screen-feedback-agent

# Analyze a video
sfa analyze recording.mp4 --output tasks.md

# With project context
sfa analyze recording.mp4 --project ~/repos/my-app --output tasks.md
```

## WhatsApp Integration (via Clawdbot)

Drop a video into your Clawdbot WhatsApp chat:
```
📎 recording.mp4
"analyze this screen recording"
```

Clawdbot will process the video and return structured coding tasks.

## Output Example

```markdown
# Screen Feedback Analysis

## Summary
Review of KnowledgeBase app navigation and search functionality.

## Tasks

### 🐛 Bug: Search results don't update on backspace
**Priority:** High
**Location:** `src/components/SearchBar.tsx`
**Description:** When deleting characters from search query, results list doesn't refresh until Enter is pressed.
**Suggested Fix:** Add debounced onChange handler instead of onSubmit only.

### ✨ Enhancement: Add keyboard shortcuts for navigation
**Priority:** Medium
**Description:** User mentioned wanting Cmd+K for search, arrow keys for navigation.
**Acceptance Criteria:**
- Cmd+K focuses search bar
- Arrow up/down navigates results
- Enter opens selected item
```

## Requirements

- Python 3.10+
- FFmpeg
- Whisper (openai-whisper or faster-whisper)
- Gemini API key

## License

MIT
