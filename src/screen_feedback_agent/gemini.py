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
You are a senior software engineer analyzing a screen recording to extract
PRECISE coding tasks. The user is reviewing an application and describing
bugs or desired features.

## Video Context
{video_description}

## Transcription with Timestamps
{timestamped_transcription}

## Screenshots (when user said "snap")
{snapshot_descriptions}

## Project Context
{project_context}

## Analysis Instructions

For EACH issue or feature request, provide:

### 1. EXACT LOCATION
- UI element name (button text, menu item, icon type)
- Position on screen (top-left, sidebar, header, etc.)
- Screenshot reference if available ("See snapshot at 12.3s")

### 2. CURRENT STATE
- What the UI looks like NOW
- What happens when interacting with it
- Any visible text/labels

### 3. DESIRED STATE
- Exactly what should change
- Expected behavior after fix
- Visual mockup description if needed

### 4. IMPLEMENTATION SPEC
```
File: [exact file path if known, or likely location]
Component: [component name]
Changes:
- Line X: Change Y to Z
- Add new function: [signature]
- CSS: [specific style changes]
```

### 5. ACCEPTANCE TEST
```
GIVEN [precondition]
WHEN [action]
THEN [expected result]
```

### 6. AGENT PROMPT
Write a complete prompt that could be given to Claude Code to implement this:
```
[Ready-to-use prompt for coding agent]
```

---

## Output Format

Respond with a markdown document containing each task in the format above.
Be EXTREMELY specific. Vague descriptions are useless.

Examples of BAD output:
- "Add a settings menu" (no location, no details)
- "Make the sidebar collapsible" (no implementation spec)

Examples of GOOD output:
- "Add dropdown menu to '.workspace-header' div, triggered by clicking the workspace name. Menu items: 'Settings' (links to /settings), 'Account' (shows email), 'Logout' (calls auth.signOut())"
- "Add collapse button to '#sidebar-container', position: absolute top-right. On click: animate width from 240px to 48px, show hamburger icon, persist state to localStorage key 'sidebar-collapsed'"
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
    model = genai.GenerativeModel("gemini-3.0-flash")
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
