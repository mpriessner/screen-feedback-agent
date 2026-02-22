"""Gemini API integration for video analysis."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import google.generativeai as genai


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
    project_context: str | None = None,
    verbose: bool = False,
) -> AnalysisOutput:
    """Analyze video using Gemini Vision.
    
    Args:
        video_path: Path to condensed video
        transcription: Whisper transcription text
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
    
    # Upload video
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
    
    # Build prompt
    prompt = ANALYSIS_PROMPT.format(
        transcription=transcription or "[No transcription available]",
        project_context=project_context or "[No project context provided]",
    )
    
    # Generate analysis
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([video_file, prompt])
    
    # Cleanup uploaded file
    genai.delete_file(video_file.name)
    
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
