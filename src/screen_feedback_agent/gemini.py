"""Gemini API integration for video analysis."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import google.generativeai as genai

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


ANALYSIS_PROMPT = """You are analyzing a screen recording where a user reviews software and comments on bugs and desired changes.

The user navigates through the application while verbally noting issues and suggestions. Your task is to extract actionable coding tasks from this review.

## Transcription
{transcription}

## Project Context
{project_context}

## Instructions
Watch the video carefully and extract:

1. **BUGS** - Issues the user encountered or mentioned
2. **ENHANCEMENTS** - Features or changes the user requested  
3. **QUESTIONS** - Unclear items that need clarification

For each item provide:
- **Title**: Short, descriptive name
- **Description**: What needs to change and why
- **Priority**: High (blocking/critical), Medium (should fix), Low (nice to have)
- **Location**: File/component if visible or mentioned
- **Suggested Approach**: Brief implementation hint if obvious

## Output Format
Respond with structured Markdown:

# Summary
[2-3 sentence overview of the review]

# Bugs
## 1. [Title] — Priority: [High/Medium/Low]
**Description:** ...
**Location:** ...
**Suggested Fix:** ...

# Enhancements
## 1. [Title] — Priority: [High/Medium/Low]
**Description:** ...
**Acceptance Criteria:**
- ...

# Questions
## 1. [Title]
**Context:** ...
**Clarification Needed:** ...
"""


def analyze_video(
    video_path: Path,
    transcription: str,
    snapshots: list[Snapshot] | None = None,
    project_context: str | None = None,
    verbose: bool = False,
) -> AnalysisOutput:
    """Analyze video using Gemini Vision.

    Args:
        video_path: Path to condensed video
        transcription: Whisper transcription text
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

    if snapshots:
        # Use multimodal prompt with snapshots
        if verbose:
            print(f"Building multimodal prompt with {len(snapshots)} snapshots")
        prompt_parts = build_multimodal_prompt(
            video_path, transcription, snapshots, project_context,
        )
    else:
        # Upload video and build simple prompt
        if verbose:
            print(f"Uploading video: {video_path}")
        video_file = genai.upload_file(path=str(video_path))

        # Wait for processing
        import time
        while video_file.state.name == "PROCESSING":
            if verbose:
                print("Waiting for video processing...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Video processing failed: {video_file.state.name}")

        prompt = ANALYSIS_PROMPT.format(
            transcription=transcription or "[No transcription available]",
            project_context=project_context or "[No project context provided]",
        )
        prompt_parts = [video_file, prompt]

    # Generate analysis
    model = genai.GenerativeModel("gemini-3.0-flash")
    response = model.generate_content(prompt_parts)

    # Parse response
    return parse_analysis_response(response.text)


def build_multimodal_prompt(
    video_path: Path,
    transcription: str,
    snapshots: list[Snapshot],
    project_context: str | None = None,
) -> list:
    """Build Gemini prompt with video + snapshot images.

    Creates a multimodal prompt that includes the video file,
    any snapshot images captured at "snap" keywords, and the
    analysis instructions.

    Args:
        video_path: Path to the condensed video
        transcription: Full transcription text
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

    # Add analysis instructions
    prompt_parts.append(ANALYSIS_PROMPT.format(
        transcription=transcription or "[No transcription available]",
        project_context=project_context or "[No project context provided]",
    ))

    return prompt_parts


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
