# E5-S3: Response Formatting

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E5-S3                                  |
| **Title**    | Response Formatting                    |
| **Epic**     | E5 — Clawdbot Integration              |
| **Status**   | TODO                                   |
| **Points**   | 1                                      |
| **Dependencies** | E3-S3 (AnalysisOutput), E4-S2 (Markdown generator) |

---

## Overview

Format analysis output for WhatsApp/chat contexts where full Markdown reports are too verbose. Produce a concise summary suitable for chat, with an option for users to request the full detailed report.

This story ensures the WhatsApp user experience is quick, scannable, and actionable — users get the key findings in seconds and can drill down if needed.

---

## Acceptance Criteria

- [ ] Function `format_chat_summary()` produces a concise chat message from `AnalysisOutput`
- [ ] Summary includes: video duration, finding counts by category, top priority item
- [ ] Uses emoji for visual scanning (bug, enhancement, question indicators)
- [ ] Message length stays under 1000 characters (WhatsApp readability)
- [ ] Function `format_full_chat_report()` produces a more detailed (but still chat-friendly) version
- [ ] "Reply full report" call-to-action included in summary
- [ ] Handles edge case of zero findings ("No issues found!")
- [ ] Handles edge case of many findings (truncates list, shows count)
- [ ] Output avoids Markdown syntax that WhatsApp doesn't support (no headers, no code blocks)
- [ ] Unit tests verify formatting for various input scenarios

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/output.py` — refine existing `format_chat_summary()`, add `format_full_chat_report()`

### Function Signatures

```python
def format_chat_summary(
    analysis: AnalysisOutput,
    video_duration: float,
    max_length: int = 1000,
) -> str:
    """Format concise summary for chat contexts.

    Args:
        analysis: Structured analysis output
        video_duration: Original video duration in seconds
        max_length: Maximum message length in characters

    Returns:
        Chat-friendly summary string
    """

def format_full_chat_report(
    analysis: AnalysisOutput,
    video_duration: float,
    max_tasks_per_section: int = 5,
) -> str:
    """Format detailed report for chat (triggered by 'full report' reply).

    Args:
        analysis: Structured analysis output
        video_duration: Original video duration in seconds
        max_tasks_per_section: Max items to show per section

    Returns:
        Detailed chat-friendly report string
    """

def _format_chat_task(task: Task, index: int) -> str:
    """Format a single task for chat display.

    Returns a single line like:
        1. Search bar X button broken [HIGH]
    """

def _format_duration_human(seconds: float) -> str:
    """Format duration for human display.

    Examples: '2:34', '12:05', '1:05:30'
    """
```

### External Dependencies

None beyond standard library.

---

## Implementation Steps

1. **Refine `format_chat_summary()`**:
   a. Header line: video emoji + analyzed duration.
   b. Findings count: one line per category with emoji and count.
   c. High-priority highlight: show the top priority bug (if any).
   d. Call-to-action: `'Reply "full report" for complete analysis.'`.
   e. Ensure total length stays under `max_length`.
2. **Implement `format_full_chat_report()`**:
   a. Summary section (2-3 sentences from `analysis.summary`).
   b. Bugs section: numbered list with priority tags, capped at `max_tasks_per_section`.
   c. Enhancements section: same format.
   d. Questions section: same format.
   e. Truncation note if items were omitted (e.g., "...and 3 more").
   f. Use WhatsApp-compatible formatting: `*bold*`, `_italic_`, bullet points with `-` or `•`.
3. **Implement `_format_chat_task()`** — single line per task: `• {title} [{PRIORITY}]`.
4. **Implement `_format_duration_human()`** — `MM:SS` or `H:MM:SS` format.
5. **Integrate with Clawdbot skill** — the skill script calls these functions to format the response before sending to chat.

### Edge Cases

- **Zero findings** — show "No issues found!" message with a check emoji.
- **Only one category has findings** — omit empty categories entirely.
- **Many findings (>10)** — show top 3 by priority in summary, full list in detailed report (capped).
- **Very long task titles** — truncate to 60 characters with "...".
- **Unicode in task titles** — ensure no encoding issues.
- **Summary text is very long** — truncate to 200 characters in chat summary.

---

## Testing Requirements

### Unit Tests — `tests/test_output_chat.py`

```python
def test_chat_summary_basic():
    """Basic summary includes duration and counts."""
    analysis = AnalysisOutput(
        summary="Review of the dashboard.",
        bugs=[Task("Bug 1", "desc", "High")],
        enhancements=[Task("Enh 1", "desc", "Medium")],
        questions=[],
    )
    result = format_chat_summary(analysis, video_duration=180.0)
    assert "3:00" in result
    assert "1 bug" in result.lower() or "1 bugs" in result
    assert "1 enhancement" in result.lower()

def test_chat_summary_no_findings():
    """Summary shows 'no issues' when all lists empty."""
    analysis = AnalysisOutput(summary="All good.", bugs=[], enhancements=[], questions=[])
    result = format_chat_summary(analysis, video_duration=60.0)
    assert "no issues" in result.lower() or "No issues" in result

def test_chat_summary_high_priority_highlighted():
    """Top priority bug is shown in summary."""
    analysis = AnalysisOutput(
        summary="Found bugs.",
        bugs=[
            Task("Minor thing", "desc", "Low"),
            Task("Critical crash", "desc", "High"),
        ],
    )
    result = format_chat_summary(analysis, video_duration=120.0)
    assert "Critical crash" in result

def test_chat_summary_max_length():
    """Summary stays within max_length characters."""
    analysis = AnalysisOutput(
        summary="Very long " * 100,
        bugs=[Task(f"Bug {i}", "desc", "Medium") for i in range(20)],
    )
    result = format_chat_summary(analysis, video_duration=600.0, max_length=1000)
    assert len(result) <= 1000

def test_chat_summary_includes_cta():
    """Summary includes 'full report' call-to-action."""
    analysis = AnalysisOutput(summary="Test", bugs=[Task("B", "d", "High")])
    result = format_chat_summary(analysis, video_duration=60.0)
    assert "full report" in result.lower()

def test_full_chat_report_sections():
    """Full report includes all non-empty sections."""
    analysis = AnalysisOutput(
        summary="Overview.",
        bugs=[Task("Bug 1", "Bug desc", "High")],
        enhancements=[Task("Enh 1", "Enh desc", "Medium")],
        questions=[Task("Q 1", "Q desc", "Low")],
    )
    result = format_full_chat_report(analysis, video_duration=300.0)
    assert "Bug 1" in result
    assert "Enh 1" in result
    assert "Q 1" in result

def test_full_chat_report_truncation():
    """Full report truncates when too many items."""
    analysis = AnalysisOutput(
        summary="Many bugs.",
        bugs=[Task(f"Bug {i}", "desc", "Medium") for i in range(10)],
    )
    result = format_full_chat_report(analysis, video_duration=600.0, max_tasks_per_section=5)
    assert "more" in result.lower()

def test_format_chat_task():
    """Single task formats as expected."""
    task = Task("Search broken", "desc", "High")
    result = _format_chat_task(task, 1)
    assert "Search broken" in result
    assert "HIGH" in result

def test_format_duration_human():
    """Duration formatting works correctly."""
    assert _format_duration_human(180.0) == "3:00"
    assert _format_duration_human(65.0) == "1:05"
    assert _format_duration_human(3661.0) == "1:01:01"
```

---

## Example Usage

```python
from screen_feedback_agent.output import format_chat_summary, format_full_chat_report
from screen_feedback_agent.gemini import AnalysisOutput, Task

analysis = AnalysisOutput(
    summary="User reviewed the dashboard and found several issues.",
    bugs=[
        Task("Search doesn't clear on X", "X button non-functional", "High", "SearchBar.tsx"),
        Task("Pagination count wrong", "Count doesn't update after filter", "Medium"),
        Task("Tooltip flickers", "Tooltip appears and disappears rapidly", "Low"),
    ],
    enhancements=[
        Task("Add dark mode", "User wants dark mode toggle", "Medium"),
        Task("Keyboard shortcuts", "User wants Ctrl+K for search", "Low"),
    ],
    questions=[
        Task("Mobile support?", "User asked about mobile responsive design", "Medium"),
    ],
)

# Concise summary for initial response
print(format_chat_summary(analysis, video_duration=754.0))
```

**Output:**
```
🎬 Analyzed 12:34 of screen recording

Found:
🐛 3 bugs (1 high priority)
✨ 2 enhancement requests
❓ 1 question

Top priority:
• Search doesn't clear on X [HIGH]

Reply "full report" for complete analysis.
```

```python
# Full report when user replies "full report"
print(format_full_chat_report(analysis, video_duration=754.0))
```

**Output:**
```
📋 *Screen Feedback Analysis*
Video: 12:34 | Found 6 items

*🐛 Bugs (3)*
1. Search doesn't clear on X [HIGH]
   → X button non-functional (SearchBar.tsx)
2. Pagination count wrong [MEDIUM]
   → Count doesn't update after filter
3. Tooltip flickers [LOW]
   → Tooltip appears and disappears rapidly

*✨ Enhancements (2)*
1. Add dark mode [MEDIUM]
   → User wants dark mode toggle
2. Keyboard shortcuts [LOW]
   → User wants Ctrl+K for search

*❓ Questions (1)*
1. Mobile support? [MEDIUM]
   → User asked about mobile responsive design
```
