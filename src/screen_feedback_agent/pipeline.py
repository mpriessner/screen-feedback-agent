"""Main analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .audio import SpeechSegment, detect_speech_segments_whisper
from .video import extract_and_combine_segments
from .gemini import analyze_video
from .output import generate_markdown


@dataclass
class AnalysisResult:
    """Result of video analysis."""
    markdown: str
    bug_count: int
    enhancement_count: int
    question_count: int
    segments: list[SpeechSegment]
    transcription: str


def run_pipeline(
    video_path: Path,
    project_path: Path | None = None,
    model_size: str = "base",
    verbose: bool = False,
) -> AnalysisResult:
    """Run the full analysis pipeline.

    Steps:
    1. Detect speech segments using Whisper + VAD
    2. Extract and combine relevant clips
    3. Load project context
    4. Send to Gemini for analysis
    5. Generate markdown output
    """
    # Step 1: Detect speech segments with Whisper (voice-only, ignores clicks)
    speech_segments = detect_speech_segments_whisper(
        video_path, model_size=model_size, verbose=verbose,
    )

    # Convert to (start, end) tuples for video extraction
    segment_tuples = [(seg.start, seg.end) for seg in speech_segments]

    # Build transcription from detected speech
    transcription = "\n".join(seg.text for seg in speech_segments)

    # Step 2: Extract and combine clips
    condensed_video, _ = extract_and_combine_segments(
        video_path, segment_tuples, verbose=verbose,
    )

    # Step 3: Load project context if provided
    project_context = None
    if project_path:
        project_context = load_project_context(project_path)

    # Step 4: Analyze with Gemini
    analysis = analyze_video(
        video_path=condensed_video,
        transcription=transcription,
        project_context=project_context,
        verbose=verbose,
    )

    # Step 5: Generate output
    markdown = generate_markdown(analysis, transcription)

    return AnalysisResult(
        markdown=markdown,
        bug_count=len(analysis.bugs),
        enhancement_count=len(analysis.enhancements),
        question_count=len(analysis.questions),
        segments=speech_segments,
        transcription=transcription,
    )


def load_project_context(project_path: Path) -> str:
    """Load relevant project context for analysis."""
    context_parts = []

    # README
    readme = project_path / "README.md"
    if readme.exists():
        context_parts.append(f"# README\n{readme.read_text()[:2000]}")

    # File structure (top-level)
    files = [f.name for f in project_path.iterdir() if not f.name.startswith(".")]
    context_parts.append(f"# Files\n{', '.join(sorted(files))}")

    return "\n\n".join(context_parts)
