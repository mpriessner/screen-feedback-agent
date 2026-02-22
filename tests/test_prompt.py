"""Tests for enhanced prompt engineering (E6-S3)."""

from pathlib import Path

import pytest

from screen_feedback_agent.audio import SpeechSegment
from screen_feedback_agent.snapshots import Snapshot
from screen_feedback_agent.gemini import (
    ENHANCED_ANALYSIS_PROMPT,
    build_enhanced_prompt,
    format_snapshot_descriptions,
    format_timestamped_transcription,
)


# --- format_timestamped_transcription tests ---


class TestFormatTimestampedTranscription:
    def test_basic_formatting(self):
        segments = [
            SpeechSegment(0.0, 5.0, "Hello world"),
            SpeechSegment(7.0, 12.0, "This is a test"),
        ]
        result = format_timestamped_transcription(segments)
        assert "[0.0s - 5.0s] Hello world" in result
        assert "[7.0s - 12.0s] This is a test" in result

    def test_empty_segments(self):
        result = format_timestamped_transcription([])
        assert result == "[No transcription available]"

    def test_single_segment(self):
        segments = [SpeechSegment(3.5, 8.2, "Just one segment")]
        result = format_timestamped_transcription(segments)
        assert "[3.5s - 8.2s] Just one segment" in result

    def test_timestamps_formatted_one_decimal(self):
        segments = [SpeechSegment(1.123, 2.789, "Precision")]
        result = format_timestamped_transcription(segments)
        assert "[1.1s - 2.8s]" in result

    def test_multiple_lines(self):
        segments = [
            SpeechSegment(0.0, 3.0, "First"),
            SpeechSegment(5.0, 8.0, "Second"),
            SpeechSegment(10.0, 15.0, "Third"),
        ]
        result = format_timestamped_transcription(segments)
        lines = result.strip().split("\n")
        assert len(lines) == 3


# --- format_snapshot_descriptions tests ---


class TestFormatSnapshotDescriptions:
    def test_no_snapshots(self):
        result = format_snapshot_descriptions([])
        assert result == "No snapshots captured."

    def test_single_snapshot(self):
        snapshots = [
            Snapshot(5.2, Path("/tmp/snap.png"), "look at this snap"),
        ]
        result = format_snapshot_descriptions(snapshots)
        assert "Snapshot 1" in result
        assert "5.2s" in result
        assert "look at this snap" in result
        assert "[Image 1 attached below]" in result

    def test_multiple_snapshots(self):
        snapshots = [
            Snapshot(5.0, Path("/tmp/snap1.png"), "first snap"),
            Snapshot(12.0, Path("/tmp/snap2.png"), "second snap"),
        ]
        result = format_snapshot_descriptions(snapshots)
        assert "Snapshot 1" in result
        assert "Snapshot 2" in result
        assert "5.0s" in result
        assert "12.0s" in result

    def test_includes_header(self):
        snapshots = [
            Snapshot(1.0, Path("/tmp/snap.png"), "test"),
        ]
        result = format_snapshot_descriptions(snapshots)
        assert "User captured the following screenshots" in result


# --- ENHANCED_ANALYSIS_PROMPT tests ---


class TestEnhancedAnalysisPrompt:
    def test_prompt_contains_required_sections(self):
        """Enhanced prompt contains all required analysis sections."""
        assert "EXACT LOCATION" in ENHANCED_ANALYSIS_PROMPT
        assert "CURRENT STATE" in ENHANCED_ANALYSIS_PROMPT
        assert "DESIRED STATE" in ENHANCED_ANALYSIS_PROMPT
        assert "IMPLEMENTATION SPEC" in ENHANCED_ANALYSIS_PROMPT
        assert "ACCEPTANCE TEST" in ENHANCED_ANALYSIS_PROMPT
        assert "AGENT PROMPT" in ENHANCED_ANALYSIS_PROMPT

    def test_prompt_contains_format_placeholders(self):
        """Prompt has all required placeholders."""
        assert "{video_description}" in ENHANCED_ANALYSIS_PROMPT
        assert "{timestamped_transcription}" in ENHANCED_ANALYSIS_PROMPT
        assert "{snapshot_descriptions}" in ENHANCED_ANALYSIS_PROMPT
        assert "{project_context}" in ENHANCED_ANALYSIS_PROMPT

    def test_prompt_has_specificity_guidance(self):
        """Prompt includes guidance for specific output."""
        assert "EXTREMELY specific" in ENHANCED_ANALYSIS_PROMPT
        assert "BAD output" in ENHANCED_ANALYSIS_PROMPT
        assert "GOOD output" in ENHANCED_ANALYSIS_PROMPT

    def test_prompt_mentions_bdd(self):
        """Prompt includes BDD-style acceptance test format."""
        assert "GIVEN" in ENHANCED_ANALYSIS_PROMPT
        assert "WHEN" in ENHANCED_ANALYSIS_PROMPT
        assert "THEN" in ENHANCED_ANALYSIS_PROMPT

    def test_prompt_mentions_css_selectors(self):
        """Prompt examples include CSS selectors."""
        assert "." in ENHANCED_ANALYSIS_PROMPT  # CSS class selector
        assert "#" in ENHANCED_ANALYSIS_PROMPT  # CSS ID selector

    def test_prompt_mentions_file_paths(self):
        """Prompt mentions file paths in implementation spec."""
        assert "File:" in ENHANCED_ANALYSIS_PROMPT
        assert "Component:" in ENHANCED_ANALYSIS_PROMPT

    def test_prompt_mentions_coding_agent(self):
        """Prompt includes coding agent instruction."""
        assert "Claude Code" in ENHANCED_ANALYSIS_PROMPT


# --- build_enhanced_prompt tests ---


class TestBuildEnhancedPrompt:
    def test_basic_build(self):
        segments = [
            SpeechSegment(0.0, 5.0, "There is a bug in the sidebar"),
        ]
        snapshots = [
            Snapshot(3.0, Path("/tmp/snap.png"), "this snap shows"),
        ]
        result = build_enhanced_prompt(segments, snapshots, "My project context")

        assert "[0.0s - 5.0s] There is a bug in the sidebar" in result
        assert "Snapshot 1" in result
        assert "My project context" in result
        assert "EXACT LOCATION" in result

    def test_no_snapshots(self):
        segments = [SpeechSegment(0.0, 3.0, "Hello")]
        result = build_enhanced_prompt(segments, [])
        assert "No snapshots captured." in result

    def test_no_project_context(self):
        segments = [SpeechSegment(0.0, 3.0, "Hello")]
        result = build_enhanced_prompt(segments, [], project_context=None)
        assert "[No project context provided]" in result

    def test_custom_video_description(self):
        segments = [SpeechSegment(0.0, 3.0, "Hello")]
        result = build_enhanced_prompt(
            segments, [],
            video_description="Custom app review",
        )
        assert "Custom app review" in result

    def test_all_sections_present(self):
        """All enhanced prompt sections are present in output."""
        segments = [SpeechSegment(0.0, 5.0, "Test speech")]
        snapshots = [Snapshot(2.0, Path("/tmp/s.png"), "snap")]
        result = build_enhanced_prompt(segments, snapshots, "project ctx")

        assert "EXACT LOCATION" in result
        assert "CURRENT STATE" in result
        assert "DESIRED STATE" in result
        assert "IMPLEMENTATION SPEC" in result
        assert "ACCEPTANCE TEST" in result
        assert "AGENT PROMPT" in result

    def test_empty_segments_handled(self):
        result = build_enhanced_prompt([], [])
        assert "[No transcription available]" in result
