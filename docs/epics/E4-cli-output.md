# EPIC 4: CLI & Output Generation

## Goal
Create user-friendly CLI and generate actionable output files.

## Stories

### E4-S1: CLI Framework
**Points:** 2

Set up CLI with Click/Typer.

**Acceptance Criteria:**
- [ ] Main command: `sfa analyze <video>`
- [ ] Options: `--output`, `--project`, `--verbose`
- [ ] Config file support (~/.config/sfa/config.yaml)
- [ ] Environment variable support (GEMINI_API_KEY)
- [ ] Help text and examples

**Commands:**
```bash
sfa analyze video.mp4                    # Basic analysis
sfa analyze video.mp4 -o tasks.md        # Custom output
sfa analyze video.mp4 --project ~/repo   # With context
sfa config set gemini_api_key xxx        # Configuration
```

---

### E4-S2: Markdown Output Generator
**Points:** 2

Generate well-formatted Markdown output.

**Acceptance Criteria:**
- [ ] Clear sections: Summary, Bugs, Enhancements
- [ ] Each task has: title, description, priority
- [ ] Include timestamps referencing original video
- [ ] Include relevant transcription snippets
- [ ] Emoji indicators for task types

**Output Structure:**
```markdown
# Screen Feedback Analysis
Generated: 2026-02-22 16:00

## 📋 Summary
[AI-generated overview]

## 🐛 Bugs (3)
### 1. [Title] — Priority: High
...

## ✨ Enhancements (2)
### 1. [Title] — Priority: Medium
...

## ❓ Questions (1)
### 1. [Title]
...

## 📝 Full Transcription
[Timestamped transcript]
```

---

### E4-S3: Progress & Logging
**Points:** 1

User-friendly progress indication.

**Acceptance Criteria:**
- [ ] Progress bar for long operations
- [ ] Stage indicators (Extracting → Transcribing → Analyzing)
- [ ] Time estimates
- [ ] Verbose mode for debugging
- [ ] Clean error messages

---

## Story Files

- [E4-S1: CLI Framework](../stories/E4-S1-cli-framework.md)
- [E4-S2: Markdown Output Generator](../stories/E4-S2-markdown-output-generator.md)
- [E4-S3: Progress & Logging](../stories/E4-S3-progress-and-logging.md)

## Definition of Done
- `pip install` works
- `sfa analyze` produces correct output
- User can configure API key easily
