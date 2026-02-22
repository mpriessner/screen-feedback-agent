# E3-S2: Analysis Prompt Engineering

| Field        | Value                                  |
|--------------|----------------------------------------|
| **Story ID** | E3-S2                                  |
| **Title**    | Analysis Prompt Engineering            |
| **Epic**     | E3 — Gemini API Analysis               |
| **Status**   | TODO                                   |
| **Points**   | 3                                      |
| **Dependencies** | E3-S1 (video uploaded to Gemini)   |

---

## Overview

Design, implement, and version the analysis prompt that instructs Gemini to extract structured coding tasks from a screen recording. The prompt combines the uploaded video, Whisper transcription, and optional project context to produce consistently formatted output.

This is the highest-leverage story in the project — prompt quality directly determines the usefulness of the entire tool's output.

---

## Acceptance Criteria

- [ ] `ANALYSIS_PROMPT` template produces consistent, parseable output across diverse video inputs
- [ ] Prompt includes placeholders for: transcription, project context, and output format instructions
- [ ] Function `build_prompt()` assembles the final prompt string from template + context
- [ ] Function `run_analysis()` sends the prompt + video to Gemini and returns raw response text
- [ ] Prompt versioning: prompts are stored with a version identifier; the active version is configurable
- [ ] Optional project context injection: README content, file tree, tech stack
- [ ] Gemini model name is configurable (default: `gemini-2.0-flash`)
- [ ] Response includes structured sections: Summary, Bugs, Enhancements, Questions
- [ ] Each extracted item has: Title, Description, Priority, Location hint, Suggested approach
- [ ] Handles case where Gemini returns unexpected format (fallback to raw text)
- [ ] Unit tests verify prompt construction and response handling

---

## Technical Specification

### Files to Modify

- `src/screen_feedback_agent/gemini.py` — refine existing `ANALYSIS_PROMPT` and `analyze_video()`

### New Data Structures

```python
@dataclass
class PromptVersion:
    """A versioned prompt template."""
    version: str
    template: str
    description: str

@dataclass
class AnalysisRequest:
    """Input for video analysis."""
    video_file: genai.types.File
    transcription: str
    project_context: str | None = None
    model_name: str = "gemini-2.0-flash"
    prompt_version: str = "v1"
```

### Function Signatures

```python
# Prompt registry
PROMPT_VERSIONS: dict[str, PromptVersion] = {}

def register_prompt(version: str, template: str, description: str) -> None:
    """Register a prompt version."""

def get_prompt(version: str = "v1") -> PromptVersion:
    """Retrieve a registered prompt version."""

def build_prompt(
    transcription: str,
    project_context: str | None = None,
    prompt_version: str = "v1",
) -> str:
    """Assemble the final prompt string from template and context."""

def run_analysis(
    request: AnalysisRequest,
    verbose: bool = False,
) -> str:
    """Send prompt + video to Gemini and return raw response text.

    Args:
        request: Analysis request with video file, transcription, context
        verbose: Print prompt and response details

    Returns:
        Raw response text from Gemini
    """

def analyze_video(
    video_path: Path,
    transcription: str,
    project_context: str | None = None,
    model_name: str = "gemini-2.0-flash",
    prompt_version: str = "v1",
    verbose: bool = False,
) -> AnalysisOutput:
    """Full analysis pipeline: upload, prompt, parse.

    This is the main entry point that orchestrates upload (E3-S1),
    prompting (E3-S2), and parsing (E3-S3).
    """
```

### Prompt Template (v1)

```python
PROMPT_V1 = """You are analyzing a screen recording where a software user reviews \
an application and provides verbal feedback about bugs, desired changes, and questions.

## Video Context
The attached video shows the user navigating through the application. Pay attention to:
- What the user clicks on and points at
- Error messages or unexpected behavior visible on screen
- UI elements the user discusses

## Transcription
The following is an automated transcription of the user's verbal commentary:

```
{transcription}
```

## Project Context
{project_context}

## Your Task
Extract ALL actionable items from this review. Categorize each as:

1. **BUGS** — Something is broken or behaving incorrectly
2. **ENHANCEMENTS** — A feature request or improvement suggestion
3. **QUESTIONS** — Something unclear that needs team discussion

## Required Output Format
You MUST respond in EXACTLY this Markdown format:

# Summary
[2-3 sentence overview of what was reviewed and key findings]

# Bugs
## 1. [Short Title] — Priority: [High/Medium/Low]
**Description:** [What is broken and expected vs actual behavior]
**Location:** [File, component, or UI area if visible/mentioned]
**Suggested Fix:** [Implementation hint if obvious, otherwise "Needs investigation"]

[Repeat for each bug]

# Enhancements
## 1. [Short Title] — Priority: [High/Medium/Low]
**Description:** [What the user wants changed or added]
**Location:** [Where this change would apply]
**Acceptance Criteria:**
- [Testable criterion 1]
- [Testable criterion 2]

[Repeat for each enhancement]

# Questions
## 1. [Short Title]
**Context:** [What prompted this question]
**Clarification Needed:** [What needs to be decided]

[Repeat for each question]

IMPORTANT:
- Assign Priority based on user emphasis (tone, repetition, words like "critical", "annoying")
- If no items exist for a category, write "None identified."
- Do NOT fabricate items — only extract what the user actually mentioned or demonstrated
"""
```

### External Dependencies

- `google-generativeai>=0.3` (already in pyproject.toml)

---

## Implementation Steps

1. **Create prompt registry** — define `PROMPT_VERSIONS` dict and `register_prompt()` / `get_prompt()` functions. Register `v1` prompt.
2. **Implement `build_prompt()`** — format the template with `transcription` and `project_context`. Use `"[No project context provided]"` when context is None.
3. **Implement `run_analysis()`**:
   a. Get the Gemini model: `genai.GenerativeModel(request.model_name)`.
   b. Build prompt via `build_prompt()`.
   c. Call `model.generate_content([request.video_file, prompt])`.
   d. Handle `google.api_core.exceptions` — retry on transient errors.
   e. Return `response.text`.
   f. If verbose, log the prompt length and response length.
4. **Refactor `analyze_video()`** — use `managed_upload()` from E3-S1, `build_prompt()` and `run_analysis()` from this story, and `parse_analysis_response()` from E3-S3.
5. **Add prompt versioning** — allow config or CLI to select prompt version.

### Edge Cases

- **Empty transcription** — prompt still works; Gemini relies more on video.
- **Very long transcription** — may exceed token limits. Truncate to last 10,000 chars with a note.
- **Gemini returns empty response** — raise `RuntimeError`.
- **Gemini response doesn't match expected format** — E3-S3 handles this; `run_analysis()` just returns raw text.
- **Rate limiting** — exponential backoff, max 3 retries.

---

## Testing Requirements

### Unit Tests — `tests/test_gemini_prompt.py`

```python
def test_build_prompt_with_transcription():
    """Prompt includes transcription text."""
    prompt = build_prompt("User said: fix this button")
    assert "fix this button" in prompt

def test_build_prompt_without_context():
    """Prompt handles missing project context."""
    prompt = build_prompt("test", project_context=None)
    assert "No project context provided" in prompt

def test_build_prompt_with_context():
    """Prompt includes project context."""
    prompt = build_prompt("test", project_context="README: My App")
    assert "README: My App" in prompt

def test_prompt_version_registry():
    """Prompts can be registered and retrieved by version."""
    register_prompt("v2", "New template {transcription}", "Test v2")
    p = get_prompt("v2")
    assert p.version == "v2"

def test_get_prompt_unknown_version():
    """KeyError raised for unknown prompt version."""
    with pytest.raises(KeyError):
        get_prompt("v999")

def test_run_analysis_success(mock_genai):
    """Analysis returns response text from Gemini."""

def test_run_analysis_empty_response(mock_genai):
    """RuntimeError raised for empty Gemini response."""

def test_run_analysis_retries_on_error(mock_genai):
    """Transient API errors trigger retry."""

def test_long_transcription_truncated():
    """Transcription over 10,000 chars is truncated."""
    long_text = "word " * 5000
    prompt = build_prompt(long_text)
    assert len(prompt) < len(long_text) + 5000  # template overhead
```

---

## Example Usage

```python
from screen_feedback_agent.gemini import build_prompt, run_analysis, AnalysisRequest

# Build and inspect prompt
prompt = build_prompt(
    transcription="The search bar doesn't clear when I click the X button...",
    project_context="# My App\nA React dashboard with search functionality.",
)
print(f"Prompt length: {len(prompt)} chars")

# Run analysis (requires uploaded video)
request = AnalysisRequest(
    video_file=uploaded_file_ref,
    transcription="The search bar doesn't clear...",
    project_context="# My App\n...",
    model_name="gemini-2.0-flash",
)
raw_response = run_analysis(request, verbose=True)
print(raw_response)
```
