# EPIC 5: Clawdbot Integration

## Goal
Enable video analysis via WhatsApp drag-and-drop through Clawdbot.

## Stories

### E5-S1: Clawdbot Skill Package
**Points:** 2

Create Clawdbot skill wrapper.

**Acceptance Criteria:**
- [ ] SKILL.md with usage instructions
- [ ] Skill triggers on video + "analyze" keyword
- [ ] Downloads video from WhatsApp media
- [ ] Calls sfa CLI
- [ ] Returns formatted response

**Skill Structure:**
```
skills/screen-feedback-agent/
├── SKILL.md
├── scripts/
│   └── analyze.sh
└── prompts/
    └── trigger.md
```

---

### E5-S2: WhatsApp Media Handler
**Points:** 2

Handle video files from WhatsApp messages.

**Acceptance Criteria:**
- [ ] Detect video attachments in messages
- [ ] Download to temp directory
- [ ] Support common formats (mp4, mov, webm)
- [ ] Size limit handling (warn if >100MB)
- [ ] Cleanup after processing

---

### E5-S3: Response Formatting
**Points:** 1

Format output for WhatsApp/chat context.

**Acceptance Criteria:**
- [ ] Condensed format for chat (not full Markdown)
- [ ] Key findings summary
- [ ] Option to get full report
- [ ] Link to detailed output file (if hosted)

**Chat Output:**
```
🎬 Analyzed 12:34 of screen recording

Found:
🐛 3 bugs (1 high priority)
✨ 2 enhancement requests
❓ 1 question

Top priority:
• Search doesn't update on backspace [HIGH]

Reply "full report" for complete analysis.
```

---

## Definition of Done
- Drop video in WhatsApp → get analysis
- Works with Clawdbot skill system
- Response within 5 minutes for typical video
