# E4-S2: Markdown Output Generator

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E4-S2                                  |
| **Title**    | Markdown Output Generator              |
| **Epic**     | E4 — CLI & Output Generation           |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E3-S3 (parsed AnalysisOutput)      |

---

## Overview

Generate well-formatted, human-readable Markdown output from the structured `AnalysisOutput`. The output includes a summary, categorized tasks with priorities, timestamps referencing the original video, and the full transcription.

This is the primary deliverable of the tool — the Markdown file that users open, read, and act on. Quality of formatting directly affects user experience and adoption.

---

## Acceptance Criteria

- [ ] Function `generate_markdown()` produces a complete Markdown document from `AnalysisOutput`
- [ ] Document includes: header with generation timestamp, summary, bugs section, enhancements section, questions section, transcription
- [ ] Each task shows: numbered title, priority badge, description, location (if available), suggested fix or acceptance criteria
- [ ] Empty sections are omitted entirely (not shown as "0 items")
- [ ] Timestamps from original video are included alongside each task (when available from segments)
- [ ] Transcription section shows timestamped transcript
- [ ] Output is valid GitHub-Flavored Markdown (parseable by CommonMark)
- [ ] Output can be rendered in any Markdown viewer without issues
- [ ] Function `generate_markdown_string()` returns a string; separate function writes to file
- [ ] Unit tests compare output against golden files

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/output.py` — refine existing `generate_markdown()` and `format_task()`

### Function Signatures

```python
def generate_markdown(
    analysis: AnalysisOutput,
    transcription: str,
    video_name: str | None = None,
    segments: list[tuple[float, float]] | None = None,
) -> str:
    """Generate formatted Markdown report.

    Args:
        analysis: Structured analysis output
        transcription: Full transcription text (timestamped)
        video_name: Original video filename for the header
        segments: Original segment timestamps for reference

    Returns:
        Complete Markdown document as string
    """

def write_markdown(
    content: str,
    output_path: Path,
) -> None:
    """Write Markdown content to file."""

def format_task(index: int, task: Task) -> list[str]:
    """Format a single task as Markdown lines."""

def _format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS or HH:MM:SS format."""

def _format_priority_badge(priority: str) -> str:
    """Return priority as a styled badge string."""
```

### External Dependencies

None beyond standard library (`datetime`, `pathlib`).

---

## Implementation Steps

1. **Implement `_format_timestamp()`** — convert float seconds to `MM:SS` (or `HH:MM:SS` for videos >1 hour).
2. **Implement `_format_priority_badge()`** — return styled priority: `**High**` / `Medium` / `*Low*` (or use emoji: `[!]` / `[-]` / `[~]`).
3. **Refine `format_task()`**:
   a. Include numbered title with priority badge.
   b. Add description field.
   c. Add location field (only if non-None).
   d. Add suggested fix field (only if non-None).
   e. For enhancements: format acceptance criteria as a bulleted list if present.
   f. Add horizontal rule between tasks.
4. **Refine `generate_markdown()`**:
   a. Header: `# Screen Feedback Analysis` with generation date, video name.
   b. Summary section: `## Summary` with analysis summary text.
   c. Bugs section: `## Bugs (N)` — omit if zero bugs.
   d. Enhancements section: `## Enhancements (N)` — omit if zero.
   e. Questions section: `## Questions (N)` — omit if zero.
   f. Segment timestamps section: `## Video Segments` — list of original time ranges if provided.
   g. Transcription section: `## Full Transcription` in a fenced code block.
5. **Implement `write_markdown()`** — write string to file with UTF-8 encoding.
6. **Update CLI** — `cli.py` calls `write_markdown()` instead of `output_path.write_text()`.

### Edge Cases

- **No bugs, no enhancements, no questions** — only show summary and transcription.
- **Very long transcription** — include in full (no truncation in file output).
- **Special Markdown characters in task text** — escape backticks and pipes in user-generated content.
- **Unicode in transcription** — ensure UTF-8 encoding throughout.
- **Missing video_name** — use "Unknown video" as fallback.

---

## Testing Requirements

### Unit Tests — `tests/test_output_markdown.py`

```python
def test_generate_markdown_complete():
    """Full analysis produces complete Markdown with all sections."""

def test_generate_markdown_no_bugs():
    """Output omits bugs section when there are no bugs."""

def test_generate_markdown_no_enhancements():
    """Output omits enhancements section when there are none."""

def test_generate_markdown_empty_analysis():
    """Empty analysis produces minimal output with summary only."""

def test_format_task_with_all_fields():
    """Task with all fields renders correctly."""

def test_format_task_minimal():
    """Task with only required fields renders correctly."""

def test_format_timestamp_seconds():
    """Timestamp formatting for various durations."""
    assert _format_timestamp(65.0) == "01:05"
    assert _format_timestamp(3661.0) == "1:01:01"
    assert _format_timestamp(0.0) == "00:00"

def test_format_priority_badge():
    """Priority badges are formatted consistently."""

def test_write_markdown_creates_file(tmp_path):
    """Markdown is written to disk correctly."""

def test_generate_markdown_includes_timestamp():
    """Output includes generation timestamp."""

def test_generate_markdown_includes_video_name():
    """Output includes the original video filename."""

def test_generate_markdown_valid_commonmark():
    """Output is valid CommonMark Markdown (no syntax errors)."""
```

### Golden File Tests

Create `tests/fixtures/golden_output/` with expected Markdown outputs for specific inputs. Compare generated output against these files.

---

## Example Usage

```python
from screen_feedback_agent.output import generate_markdown, write_markdown
from screen_feedback_agent.gemini import AnalysisOutput, Task

analysis = AnalysisOutput(
    summary="The user reviewed the dashboard and found 2 bugs.",
    bugs=[
        Task(
            title="Search doesn't clear on X click",
            description="The X button in search bar is non-functional.",
            priority="High",
            location="src/components/SearchBar.tsx",
            suggested_fix="Add onClick handler to clear button.",
        ),
    ],
    enhancements=[
        Task(
            title="Add dark mode toggle",
            description="User wants dark mode in settings.",
            priority="Low",
        ),
    ],
    questions=[],
)

markdown = generate_markdown(
    analysis,
    transcription="[00:05] So this search bar doesn't clear when I...",
    video_name="dashboard-review.mp4",
)

write_markdown(markdown, Path("tasks.md"))
```

**Expected output (tasks.md):**
```markdown
# Screen Feedback Analysis
*Generated: 2026-02-22 16:00 | Video: dashboard-review.mp4*

---

## Summary
The user reviewed the dashboard and found 2 bugs.

## Bugs (1)

### 1. Search doesn't clear on X click — Priority: **High**

**Description:** The X button in search bar is non-functional.

**Location:** `src/components/SearchBar.tsx`

**Suggested Fix:** Add onClick handler to clear button.

---

## Enhancements (1)

### 1. Add dark mode toggle — Priority: *Low*

**Description:** User wants dark mode in settings.

---

## Full Transcription

```
[00:05] So this search bar doesn't clear when I...
```
```
