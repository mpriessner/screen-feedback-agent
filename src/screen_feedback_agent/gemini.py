"""Gemini API integration for video analysis."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import google.generativeai as genai

from .audio import SpeechSegment
from .snapshots import Snapshot


@dataclass
class Task:
    """A coding task extracted from analysis."""
    title: str
    description: str
    priority: str  # High, Medium, Low
    location: str | None = None
    suggested_fix: str | None = None


@dataclass
class AnalysisOutput:
    """Structured output from Gemini analysis."""
    summary: str
    bugs: list[Task] = field(default_factory=list)
    enhancements: list[Task] = field(default_factory=list)
    questions: list[Task] = field(default_factory=list)


ENHANCED_ANALYSIS_PROMPT = """
You are a staff software engineer creating IMPLEMENTATION-READY specifications 
from a screen recording. The user is reviewing their application and describing 
bugs, issues, or features they want. Your job is to extract EVERY request and 
turn it into a precise, actionable task.

Watch the video carefully. Listen to what the user says. Look at screenshots 
captured when they said "snap". Create detailed specs that a coding agent can 
implement WITHOUT asking clarifying questions.

---

## INPUT CONTEXT

### Video Description
{video_description}

### Timestamped Transcription
{timestamped_transcription}

### Screenshots (captured at "snap" keywords)
{snapshot_descriptions}

### Project Context
{project_context}

---

## OUTPUT REQUIREMENTS

You MUST output a structured markdown document with the following format.
Follow this EXACTLY for EACH task identified in the video.

---

# 🎯 OVERALL GOAL

[One paragraph describing the high-level objective the user wants to achieve.
What is the end state they're working towards? Why do they want these changes?]

---

# 📋 TASK LIST

## Task 1: [Short descriptive title]

### 🎯 Objective
[One sentence: What specific problem does this solve or what feature does this add?]

### 📍 Location (REQUIRED - be specific!)
| Field | Value |
|-------|-------|
| **Timestamp in video** | [e.g., 12.3s - 15.7s] |
| **Screenshot reference** | [e.g., "See snap at 17.5s" or "N/A"] |
| **Screen area** | [e.g., "Right sidebar", "Top navigation bar", "Main content area below header"] |
| **UI element** | [e.g., "The blue 'Save' button", "Table with class .data-grid", "Dropdown menu labeled 'Options'"] |
| **Current visible text** | [Exact text visible on the element, if any] |

### 📸 Visual Reference
[Describe EXACTLY what you see in the video/screenshot at this moment. 
Be specific: colors, positions, sizes, text content, surrounding elements.]

### 🔄 Current State → Desired State

**CURRENT:**
[Describe precisely what happens NOW when interacting with this element.
Include: appearance, behavior on click/hover, any animations, data shown.]

**DESIRED:**
[Describe precisely what SHOULD happen after the change.
Include: new appearance, new behavior, new data, animations, edge cases.]

### 🛠️ Implementation Specification

```yaml
type: [bug_fix | feature | enhancement | refactor]
priority: [critical | high | medium | low]
estimated_complexity: [trivial | simple | moderate | complex]

files_likely_affected:
  - path/to/file1.tsx  # [reason]
  - path/to/file2.css  # [reason]

components_involved:
  - ComponentName  # [what changes needed]

new_elements_needed:
  - element: "[CSS selector or component name]"
    type: "[div | button | modal | etc.]"
    position: "[where in DOM / layout]"
    styles: "[key CSS properties]"
    behavior: "[click/hover/etc. handlers]"

data_requirements:
  - source: "[API endpoint | localStorage | props | state]"
    format: "[describe data structure]"

state_changes:
  - "[describe any new state variables or state modifications]"
```

### ✅ Acceptance Criteria

```gherkin
GIVEN [specific precondition - be exact about app state]
WHEN [specific user action - be exact about what they do]
THEN [specific expected result - be exact about what they see/experience]

GIVEN [another scenario]
WHEN [action]
THEN [result]
```

### 🤖 CLAUDE CODE PROMPT

```markdown
## Task: [Title]

**Context:** [1-2 sentences about where this fits in the app]

**Current behavior:** [What happens now]

**Required changes:**

1. [First specific change with exact details]
   - File: `path/to/file.tsx`
   - Find: [what to look for]
   - Change: [what to modify]

2. [Second specific change]
   - File: `path/to/file.css`
   - Add: [exact CSS or code to add]

3. [Third specific change if needed]

**Acceptance test:**
- [ ] [Specific testable criterion]
- [ ] [Another criterion]
- [ ] [Edge case to handle]

**Do NOT:**
- [Common mistake to avoid]
- [Another thing to avoid]
```

---

## Task 2: [Next task title]

[Repeat the same structure for each additional task]

---

# 📊 SUMMARY

| # | Task | Type | Priority | Complexity |
|---|------|------|----------|------------|
| 1 | [Title] | [type] | [priority] | [complexity] |
| 2 | [Title] | [type] | [priority] | [complexity] |

---

## CRITICAL RULES

1. **NO VAGUE DESCRIPTIONS** - Every field must have specific, concrete values
2. **WATCH THE WHOLE VIDEO** - Don't miss any requests the user makes
3. **USE SCREENSHOTS** - Reference snap screenshots with exact timestamps
4. **INFER TECHNICAL DETAILS** - Look at the UI to guess component names, CSS classes, file paths
5. **MULTIPLE TASKS = MULTIPLE SECTIONS** - Each distinct request gets its own Task section
6. **CODING PROMPT MUST BE COPY-PASTEABLE** - Someone should be able to give it directly to Claude Code

## EXAMPLES OF GOOD VS BAD

❌ BAD: "Add a sidebar"
✅ GOOD: "Add a collapsible sidebar to the right of .main-content, width 280px collapsed to 48px, containing a table of contents generated from h2 headings on the page, with smooth 200ms ease-out transition on hover"

❌ BAD: "Fix the button"  
✅ GOOD: "The 'Submit' button (button.primary-action in the form footer) should be disabled and show opacity 0.5 while the form is submitting, re-enable after response"

❌ BAD: "Make it look better"
✅ GOOD: "Increase padding on .card-container from 12px to 24px, add border-radius: 8px, add subtle box-shadow: 0 2px 8px rgba(0,0,0,0.1)"
"""

# Keep legacy prompt for backward compatibility
ANALYSIS_PROMPT = ENHANCED_ANALYSIS_PROMPT


def format_timestamped_transcription(segments: list[SpeechSegment]) -> str:
    """Format transcription with timestamps for context.

    Args:
        segments: List of SpeechSegment objects with timing info

    Returns:
        Formatted string with timestamps, e.g. "[0.0s - 5.0s] Hello world"
    """
    if not segments:
        return "[No transcription available]"

    lines = []
    for seg in segments:
        timestamp = f"[{seg.start:.1f}s - {seg.end:.1f}s]"
        lines.append(f"{timestamp} {seg.text}")
    return "\n".join(lines)


def format_snapshot_descriptions(snapshots: list[Snapshot]) -> str:
    """Describe snapshots for text context in the prompt.

    Args:
        snapshots: List of Snapshot objects

    Returns:
        Formatted description of all snapshots
    """
    if not snapshots:
        return "No snapshots captured."

    lines = ["User captured the following screenshots by saying 'snap':"]
    for i, snap in enumerate(snapshots, 1):
        lines.append(f"\n**Snapshot {i}** (at {snap.timestamp:.1f}s)")
        lines.append(f"Context: \"{snap.context}\"")
        lines.append(f"[Image {i} attached below]")

    return "\n".join(lines)


def build_enhanced_prompt(
    segments: list[SpeechSegment],
    snapshots: list[Snapshot],
    project_context: str | None = None,
    video_description: str = "Screen recording of user reviewing an application",
) -> str:
    """Build the enhanced text-only prompt with all context.

    Args:
        segments: Speech segments with timestamps and text
        snapshots: Snapshot objects from snap keywords
        project_context: Optional project README/structure
        video_description: Description of the video content

    Returns:
        Formatted prompt string
    """
    return ENHANCED_ANALYSIS_PROMPT.format(
        video_description=video_description,
        timestamped_transcription=format_timestamped_transcription(segments),
        snapshot_descriptions=format_snapshot_descriptions(snapshots),
        project_context=project_context or "[No project context provided]",
    )


def build_multimodal_prompt(
    video_path: Path,
    segments: list[SpeechSegment],
    snapshots: list[Snapshot],
    project_context: str | None = None,
) -> list:
    """Build Gemini prompt with video + snapshot images.

    Creates a multimodal prompt that includes the video file,
    any snapshot images captured at "snap" keywords, and the
    enhanced analysis instructions.

    Args:
        video_path: Path to the condensed video
        segments: Speech segments with timestamps and text
        snapshots: List of Snapshot objects with images
        project_context: Optional project context

    Returns:
        List of prompt parts for Gemini generate_content()
    """
    prompt_parts: list = []

    # Add video
    video_file = genai.upload_file(path=str(video_path))
    prompt_parts.append(video_file)

    # Add snapshots with context
    for snap in snapshots:
        prompt_parts.append(f"\n--- SNAPSHOT at {snap.timestamp:.1f}s ---")
        prompt_parts.append(f"User said: '{snap.context}'")
        prompt_parts.append(genai.upload_file(path=str(snap.image_path)))

    # Add enhanced analysis instructions
    prompt_parts.append(build_enhanced_prompt(
        segments, snapshots, project_context,
    ))

    return prompt_parts


def analyze_video(
    video_path: Path,
    transcription: str,
    segments: list[SpeechSegment] | None = None,
    snapshots: list[Snapshot] | None = None,
    project_context: str | None = None,
    verbose: bool = False,
) -> AnalysisOutput:
    """Analyze video using Gemini Vision.

    Args:
        video_path: Path to condensed video
        transcription: Whisper transcription text
        segments: Optional speech segments for enhanced prompt
        snapshots: Optional list of snap keyword screenshots
        project_context: Optional project README/structure
        verbose: Print debug output

    Returns:
        Structured analysis output
    """
    # Configure API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)

    if segments and snapshots:
        # Use full multimodal prompt with snapshots and enhanced template
        if verbose:
            print(f"Building multimodal prompt with {len(snapshots)} snapshots")
        prompt_parts = build_multimodal_prompt(
            video_path, segments, snapshots, project_context,
        )
    elif segments:
        # Use enhanced prompt without snapshots
        if verbose:
            print(f"Uploading video: {video_path}")
        video_file = genai.upload_file(path=str(video_path))

        import time
        while video_file.state.name == "PROCESSING":
            if verbose:
                print("Waiting for video processing...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Video processing failed: {video_file.state.name}")

        prompt = build_enhanced_prompt(
            segments, [], project_context,
        )
        prompt_parts = [video_file, prompt]
    else:
        # Fallback: simple prompt with transcription string
        if verbose:
            print(f"Uploading video: {video_path}")
        video_file = genai.upload_file(path=str(video_path))

        import time
        while video_file.state.name == "PROCESSING":
            if verbose:
                print("Waiting for video processing...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Video processing failed: {video_file.state.name}")

        prompt = ENHANCED_ANALYSIS_PROMPT.format(
            video_description="Screen recording of user reviewing an application",
            timestamped_transcription=transcription or "[No transcription available]",
            snapshot_descriptions="No snapshots captured.",
            project_context=project_context or "[No project context provided]",
        )
        prompt_parts = [video_file, prompt]

    # Generate analysis
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt_parts)

    # Parse response
    return parse_analysis_response(response.text)


def parse_analysis_response(text: str) -> AnalysisOutput:
    """Parse Gemini response into structured output.

    TODO: Implement proper parsing in E3-S3
    """
    # Placeholder - just return raw text as summary
    return AnalysisOutput(
        summary=text[:500] if text else "Analysis complete",
        bugs=[],
        enhancements=[],
        questions=[],
    )
