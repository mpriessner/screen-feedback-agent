# E5-S1: Clawdbot Skill Package

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E5-S1                                  |
| **Title**    | Clawdbot Skill Package                 |
| **Epic**     | E5 — Clawdbot Integration              |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E4-S1 (CLI must be functional)     |

---

## Overview

Create a Clawdbot skill wrapper that enables video analysis via the Clawdbot platform. The skill defines trigger conditions, provides a SKILL.md with usage instructions, and includes scripts that invoke the `sfa` CLI for processing.

This story enables the secondary user flow — dropping a video in WhatsApp and getting analysis results back in chat.

---

## Acceptance Criteria

- [ ] Skill directory created at `skills/screen-feedback-agent/` with proper structure
- [ ] `SKILL.md` contains clear usage instructions, trigger keywords, and examples
- [ ] Skill triggers on messages containing a video attachment + the keyword "analyze" (case-insensitive)
- [ ] `scripts/analyze.sh` downloads the video, runs `sfa analyze`, and outputs the result
- [ ] `prompts/trigger.md` defines the trigger detection prompt for Clawdbot
- [ ] Script handles temporary file cleanup after processing
- [ ] Script returns a non-zero exit code on failure with a user-friendly error message
- [ ] Skill works with the Clawdbot skill system's expected conventions
- [ ] Integration test validates the skill can be loaded by Clawdbot

---

## Technical Specification

### Files to Create

```
skills/screen-feedback-agent/
├── SKILL.md
├── scripts/
│   └── analyze.sh
└── prompts/
    └── trigger.md
```

### File Contents

#### SKILL.md

```markdown
# Screen Feedback Agent

Analyze screen recordings with voice commentary and extract structured coding tasks.

## Trigger
Send a video with the word "analyze" in the message.

## Usage
- Send a screen recording video in chat
- Include "analyze" in your message
- Optionally mention a project name for context

## Examples
- [video] "analyze this"
- [video] "analyze for project dashboard"
- [video] "can you analyze this recording?"

## Output
Returns a summary of findings:
- Bugs found
- Enhancement requests
- Questions for clarification

Reply "full report" after analysis to get the complete detailed report.
```

#### scripts/analyze.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

# Arguments from Clawdbot:
# $1 - Path to downloaded video file
# $2 - Original message text (optional)
# $3 - Project context hint (optional)

VIDEO_PATH="${1:?Video path required}"
MESSAGE="${2:-}"
PROJECT_HINT="${3:-}"

# Validate video exists
if [[ ! -f "$VIDEO_PATH" ]]; then
    echo "Error: Video file not found: $VIDEO_PATH" >&2
    exit 1
fi

# Create temp directory for output
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

OUTPUT_FILE="$TMPDIR/analysis.md"

# Build sfa command
SFA_CMD="sfa analyze '$VIDEO_PATH' -o '$OUTPUT_FILE'"

if [[ -n "$PROJECT_HINT" ]]; then
    SFA_CMD="$SFA_CMD --project '$PROJECT_HINT'"
fi

# Run analysis
eval "$SFA_CMD"

# Output result (Clawdbot captures stdout)
cat "$OUTPUT_FILE"
```

#### prompts/trigger.md

```markdown
Detect if the user wants to analyze a screen recording.

Trigger when ALL of these are true:
1. The message includes a video attachment
2. The message text contains "analyze" or similar intent words
   (e.g., "review", "check this recording", "what's in this video")

Do NOT trigger for:
- Video messages without analysis intent
- Text-only messages mentioning "analyze"
- Image attachments (only video)

Extract:
- project_hint: If the user mentions a project name, extract it
```

### External Dependencies

- `sfa` CLI must be installed and on PATH
- `GEMINI_API_KEY` must be set in the environment
- Clawdbot skill system (external)

---

## Implementation Steps

1. **Create directory structure** — `skills/screen-feedback-agent/` with subdirectories.
2. **Write `SKILL.md`** — follow Clawdbot's skill documentation format. Include trigger description, usage examples, and expected output format.
3. **Write `prompts/trigger.md`** — define the NLP trigger conditions for Clawdbot to detect when this skill should activate.
4. **Write `scripts/analyze.sh`**:
   a. Accept video path and optional message text as arguments.
   b. Validate the video file exists and is a supported format.
   c. Create a temporary output directory.
   d. Run `sfa analyze` with appropriate flags.
   e. Output the result to stdout for Clawdbot to capture.
   f. Clean up temp files in a trap handler.
   g. Handle errors with user-friendly messages.
5. **Make script executable** — `chmod +x scripts/analyze.sh`.
6. **Test manually** — run the script with a sample video to verify end-to-end.

### Edge Cases

- **Video file path has spaces** — ensure proper quoting in the shell script.
- **`sfa` not on PATH** — script checks for `sfa` command, shows install instructions if missing.
- **GEMINI_API_KEY not set** — `sfa` reports this; script passes through the error.
- **Very large video** — processing takes >5 minutes. Clawdbot may timeout. Script should output an initial "Processing..." message to keep the connection alive.
- **Script killed mid-processing** — trap handler cleans up temp files.

---

## Testing Requirements

### Unit Tests — `tests/test_skill_package.py`

```python
def test_skill_directory_structure():
    """Skill directory has expected structure."""
    skill_dir = Path("skills/screen-feedback-agent")
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "scripts" / "analyze.sh").exists()
    assert (skill_dir / "prompts" / "trigger.md").exists()

def test_analyze_script_executable():
    """analyze.sh has executable permission."""
    script = Path("skills/screen-feedback-agent/scripts/analyze.sh")
    assert os.access(script, os.X_OK)

def test_analyze_script_missing_video():
    """Script exits with error when video path is missing."""

def test_analyze_script_nonexistent_video():
    """Script exits with error for nonexistent video file."""

def test_skill_md_contains_trigger():
    """SKILL.md documents the trigger keyword."""
    content = Path("skills/screen-feedback-agent/SKILL.md").read_text()
    assert "analyze" in content.lower()

def test_trigger_prompt_has_conditions():
    """Trigger prompt defines video + keyword conditions."""
    content = Path("skills/screen-feedback-agent/prompts/trigger.md").read_text()
    assert "video" in content.lower()
    assert "analyze" in content.lower()
```

### Integration Tests

- With `sfa` installed and API key set, run `scripts/analyze.sh` with a test video and verify it produces valid Markdown output on stdout.

---

## Example Usage

```bash
# Direct invocation (for testing)
./skills/screen-feedback-agent/scripts/analyze.sh ~/recordings/review.mp4

# With message context
./skills/screen-feedback-agent/scripts/analyze.sh ~/recordings/review.mp4 "analyze this for the dashboard project"

# Clawdbot invokes automatically when:
# User sends: [video attachment] "analyze this"
```
