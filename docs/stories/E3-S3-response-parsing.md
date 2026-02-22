# E3-S3: Response Parsing

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E3-S3                                  |
| **Title**    | Response Parsing                       |
| **Epic**     | E3 — Gemini API Analysis               |
| **Status**   | TODO                                   |
| **Points**   | 2                                      |
| **Dependencies** | E3-S2 (raw Gemini response text)   |

---

## Overview

Parse Gemini's Markdown response into structured `AnalysisOutput` data objects. The parser handles the expected format from the analysis prompt and degrades gracefully when the response deviates from the expected structure.

This story converts unstructured AI output into typed, validated data that the rest of the system (output generation, chat formatting) can reliably consume.

---

## Acceptance Criteria

- [ ] Function `parse_analysis_response()` converts Markdown text into an `AnalysisOutput` object
- [ ] Correctly extracts: Summary, Bugs (with fields), Enhancements (with fields), Questions (with fields)
- [ ] Each `Task` has: `title`, `description`, `priority`, `location` (optional), `suggested_fix` (optional)
- [ ] Handles malformed responses: missing sections, extra sections, inconsistent formatting
- [ ] Falls back to raw text as summary when parsing completely fails (never raises on bad input)
- [ ] Validates priority values are one of: High, Medium, Low (defaults to Medium if unrecognized)
- [ ] Supports "None identified." sections (produces empty lists)
- [ ] Parser is stateless and pure (no side effects) for easy testing
- [ ] Comprehensive unit tests with diverse response samples

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/gemini.py` — replace `parse_analysis_response()` placeholder with full implementation

### Existing Data Structures (no changes needed)

```python
@dataclass
class Task:
    title: str
    description: str
    priority: str  # High, Medium, Low
    location: str | None = None
    suggested_fix: str | None = None

@dataclass
class AnalysisOutput:
    summary: str
    bugs: list[Task] = field(default_factory=list)
    enhancements: list[Task] = field(default_factory=list)
    questions: list[Task] = field(default_factory=list)
```

### Function Signatures

```python
def parse_analysis_response(text: str) -> AnalysisOutput:
    """Parse Gemini Markdown response into structured output.

    Args:
        text: Raw Markdown text from Gemini

    Returns:
        AnalysisOutput with parsed sections. Never raises;
        falls back to raw text as summary on total parse failure.
    """

def _extract_section(text: str, section_name: str) -> str | None:
    """Extract content between section headers.

    Args:
        section_name: e.g., "Summary", "Bugs", "Enhancements", "Questions"

    Returns:
        Section content or None if not found
    """

def _parse_tasks(section_text: str) -> list[Task]:
    """Parse a section containing numbered task items.

    Expects format:
        ## 1. [Title] — Priority: [Level]
        **Description:** ...
        **Location:** ...
        **Suggested Fix:** ...
    """

def _parse_single_task(task_block: str) -> Task | None:
    """Parse a single task block into a Task object.

    Returns None if the block cannot be parsed.
    """

def _normalize_priority(priority: str) -> str:
    """Normalize priority string to High/Medium/Low."""
```

### External Dependencies

- Standard library only: `re`

---

## Implementation Steps

1. **Implement `_extract_section()`**:
   a. Use regex to find `# <section_name>` header (case-insensitive).
   b. Extract everything between this header and the next `# ` header (or end of string).
   c. Strip leading/trailing whitespace.
   d. Return `None` if section not found.
2. **Implement `_normalize_priority()`** — map common variations: `"HIGH"`, `"high"`, `"H"` → `"High"`. Default to `"Medium"` for unrecognized values.
3. **Implement `_parse_single_task()`**:
   a. Extract title from `## N. [Title]` pattern (with or without `— Priority: [Level]`).
   b. Extract priority from the header line or from a `**Priority:**` field.
   c. Extract `**Description:**` field value.
   d. Extract optional `**Location:**` field value.
   e. Extract optional `**Suggested Fix:**` or `**Acceptance Criteria:**` field value.
   f. Return `Task` object, or `None` if title or description couldn't be extracted.
4. **Implement `_parse_tasks()`**:
   a. Split section by `## \d+\.` pattern to get individual task blocks.
   b. Call `_parse_single_task()` for each block.
   c. Filter out `None` results.
   d. Handle `"None identified."` — return empty list.
5. **Implement `parse_analysis_response()`**:
   a. Extract Summary section → `AnalysisOutput.summary`.
   b. Extract Bugs section → parse tasks → `AnalysisOutput.bugs`.
   c. Extract Enhancements section → parse tasks → `AnalysisOutput.enhancements`.
   d. Extract Questions section → parse tasks → `AnalysisOutput.questions`.
   e. If all extraction fails, set `summary` to first 500 chars of raw text.
   f. Never raise — always return a valid `AnalysisOutput`.

### Edge Cases

- **Missing section headers** — section returns `None`, task list is empty.
- **Extra whitespace/newlines** — strip aggressively.
- **Markdown formatting variations** — `## 1.` vs `## 1)` vs `### 1.` — handle common variations.
- **Priority in different position** — sometimes in header, sometimes as a field.
- **Multi-line descriptions** — description may span multiple lines until next `**Field:**`.
- **Acceptance Criteria as list** — join bullet points into description string.
- **Response is pure JSON instead of Markdown** — detect JSON, attempt `json.loads()` as fallback.
- **Empty response** — return `AnalysisOutput(summary="No analysis generated")`.
- **Non-English response** — parser works on structure, not language; should handle this.

---

## Testing Requirements

### Unit Tests — `tests/test_gemini_parsing.py`

```python
# Well-formed input
def test_parse_complete_response():
    """Full well-formed response parses into all sections."""

def test_parse_summary_extracted():
    """Summary section text is captured correctly."""

def test_parse_bugs_with_all_fields():
    """Bug tasks have title, description, priority, location, suggested_fix."""

def test_parse_enhancements_with_criteria():
    """Enhancement tasks capture acceptance criteria."""

def test_parse_questions():
    """Question tasks have title, context, and clarification needed."""

def test_parse_multiple_bugs():
    """Multiple bugs are parsed as separate Task objects."""

# Priority handling
def test_priority_normalization():
    """Various priority formats are normalized."""
    assert _normalize_priority("HIGH") == "High"
    assert _normalize_priority("low") == "Low"
    assert _normalize_priority("unknown") == "Medium"

# Edge cases
def test_parse_missing_section():
    """Missing section results in empty task list."""

def test_parse_none_identified():
    """'None identified.' section produces empty list."""

def test_parse_malformed_response():
    """Malformed response falls back to raw text summary."""

def test_parse_empty_string():
    """Empty string returns default AnalysisOutput."""

def test_parse_partial_task():
    """Task with missing optional fields still parses."""

def test_parse_multiline_description():
    """Multi-line descriptions are captured completely."""

def test_parse_json_fallback():
    """JSON response is handled via fallback parsing."""

# Regression samples
def test_parse_sample_response_1():
    """Real-world sample response 1 parses correctly."""

def test_parse_sample_response_2():
    """Real-world sample response 2 parses correctly."""
```

### Test Data

Create `tests/fixtures/sample_responses/` with 3-5 sample Gemini response files (`.md`) covering:
- Perfect format matching the prompt
- Slightly deviated format (different heading levels, extra sections)
- Minimal response (just summary)
- Response with "None identified" sections
- Malformed response (partial Markdown)

---

## Example Usage

```python
from screen_feedback_agent.gemini import parse_analysis_response

raw_response = """
# Summary
The user reviewed the dashboard application and found 2 bugs and suggested 1 enhancement.

# Bugs
## 1. Search doesn't clear on X click — Priority: High
**Description:** Clicking the X button in the search bar does not clear the search query.
**Location:** `src/components/SearchBar.tsx`
**Suggested Fix:** Add onClick handler to clear button that resets search state.

## 2. Table pagination shows wrong count — Priority: Medium
**Description:** The "Showing X of Y" count doesn't update after filtering.
**Location:** `src/components/DataTable.tsx`
**Suggested Fix:** Recalculate count from filtered dataset, not total.

# Enhancements
## 1. Add dark mode toggle — Priority: Low
**Description:** User wants a dark mode option in settings.
**Acceptance Criteria:**
- Toggle in settings page
- Persists across sessions
- Applies to all components

# Questions
None identified.
"""

result = parse_analysis_response(raw_response)
print(f"Summary: {result.summary[:80]}...")
print(f"Bugs: {len(result.bugs)}")
print(f"Enhancements: {len(result.enhancements)}")
print(f"Questions: {len(result.questions)}")
# Summary: The user reviewed the dashboard application and found 2 bugs and sugge...
# Bugs: 2
# Enhancements: 1
# Questions: 0

for bug in result.bugs:
    print(f"  [{bug.priority}] {bug.title}: {bug.location}")
# [High] Search doesn't clear on X click: src/components/SearchBar.tsx
# [Medium] Table pagination shows wrong count: src/components/DataTable.tsx
```
