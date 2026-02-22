"""Tests for snap keyword screenshot extraction (E6-S2)."""

from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from screen_feedback_agent.audio import SpeechSegment
from screen_feedback_agent.snapshots import (
    SNAP_KEYWORDS,
    Snapshot,
    cleanup_snapshots,
    detect_snap_moments,
    extract_all_snapshots,
    extract_frame,
)


# --- Snapshot dataclass tests ---


class TestSnapshot:
    def test_creation(self, tmp_path):
        snap = Snapshot(
            timestamp=5.2,
            image_path=tmp_path / "snap.png",
            context="look at this snap here",
        )
        assert snap.timestamp == 5.2
        assert snap.context == "look at this snap here"


# --- detect_snap_moments tests ---


class TestDetectSnapMoments:
    def test_detect_snap_keyword(self):
        """Finds 'snap' in transcription."""
        segments = [
            SpeechSegment(0.0, 5.0, "Look at this button snap now"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 1
        timestamp, context = moments[0]
        assert 0 < timestamp < 5.0
        assert "snap" in context.lower()

    def test_multiple_snaps(self):
        """Handles multiple snap keywords in different segments."""
        segments = [
            SpeechSegment(0.0, 3.0, "First snap now"),
            SpeechSegment(5.0, 8.0, "Second snap then"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 2

    def test_alternative_keywords(self):
        """Detects alternative keywords like 'screenshot' and 'capture'."""
        segments = [
            SpeechSegment(0.0, 5.0, "Take a screenshot of this"),
            SpeechSegment(6.0, 10.0, "Capture this moment"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 2

    def test_here_keyword(self):
        """Detects 'here' keyword."""
        segments = [
            SpeechSegment(0.0, 5.0, "Look right here at this button"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 1

    def test_no_keywords(self):
        """Returns empty when no keywords found."""
        segments = [
            SpeechSegment(0.0, 5.0, "This is just normal talking about things"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 0

    def test_case_insensitive(self):
        """Keyword detection is case insensitive."""
        segments = [
            SpeechSegment(0.0, 5.0, "SNAP this Capture THAT"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 2  # "SNAP" and "Capture"

    def test_custom_keywords(self):
        """Custom keywords can be provided."""
        segments = [
            SpeechSegment(0.0, 5.0, "Freeze this frame right now"),
        ]
        moments = detect_snap_moments(segments, keywords=["freeze"])
        assert len(moments) == 1

    def test_timestamp_estimation(self):
        """Timestamp is estimated via linear interpolation."""
        segments = [
            SpeechSegment(0.0, 10.0, "word1 word2 snap word4 word5"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 1
        timestamp = moments[0][0]
        # "snap" is at index 2 of 5 words -> ratio 2/5 = 0.4
        # timestamp = 0.0 + (10.0 - 0.0) * 0.4 = 4.0
        assert timestamp == pytest.approx(4.0, abs=0.1)

    def test_context_extraction(self):
        """Context includes 3 words before and after keyword."""
        segments = [
            SpeechSegment(0.0, 10.0, "a b c d snap e f g h"),
        ]
        moments = detect_snap_moments(segments)
        _, context = moments[0]
        # 3 words before "snap" (index 4): "b c d snap e f g"
        assert "snap" in context
        # Should have surrounding words
        words = context.split()
        assert len(words) <= 7  # max 3 before + keyword + 3 after

    def test_empty_segments(self):
        """Empty segment list returns no moments."""
        assert detect_snap_moments([]) == []

    def test_multiple_keywords_same_segment(self):
        """Multiple keywords in same segment each detected."""
        segments = [
            SpeechSegment(0.0, 10.0, "snap this and capture that"),
        ]
        moments = detect_snap_moments(segments)
        assert len(moments) == 2


# --- extract_frame tests ---


class TestExtractFrame:
    @patch("screen_feedback_agent.snapshots.subprocess.run")
    def test_extract_frame_calls_ffmpeg(self, mock_run, tmp_path):
        """FFmpeg is called with correct arguments."""
        video = tmp_path / "video.mp4"
        video.touch()

        extract_frame(video, 5.2, tmp_path)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-ss" in cmd
        assert "5.2" in cmd
        assert "-vframes" in cmd
        assert "1" in cmd
        assert "-q:v" in cmd

    @patch("screen_feedback_agent.snapshots.subprocess.run")
    def test_output_path_format(self, mock_run, tmp_path):
        """Output filename includes timestamp."""
        video = tmp_path / "video.mp4"
        video.touch()

        result = extract_frame(video, 3.14, tmp_path)

        assert result.name == "snap_3.14.png"
        assert result.parent == tmp_path


# --- extract_all_snapshots tests ---


class TestExtractAllSnapshots:
    @patch("screen_feedback_agent.snapshots.extract_frame")
    def test_extracts_all_snaps(self, mock_extract, tmp_path):
        """Extracts a frame for each snap moment."""
        mock_extract.return_value = tmp_path / "snap.png"

        segments = [
            SpeechSegment(0.0, 5.0, "First snap now"),
            SpeechSegment(6.0, 10.0, "Second snap then"),
        ]
        video = tmp_path / "video.mp4"
        video.touch()

        snapshots = extract_all_snapshots(video, segments, tmp_path)

        assert len(snapshots) == 2
        assert mock_extract.call_count == 2

    @patch("screen_feedback_agent.snapshots.extract_frame")
    def test_creates_output_dir(self, mock_extract, tmp_path):
        """Output directory is created if it doesn't exist."""
        mock_extract.return_value = tmp_path / "out" / "snap.png"

        segments = [SpeechSegment(0.0, 5.0, "snap")]
        video = tmp_path / "video.mp4"
        video.touch()

        output_dir = tmp_path / "new_dir"
        assert not output_dir.exists()

        extract_all_snapshots(video, segments, output_dir)

        assert output_dir.exists()

    @patch("screen_feedback_agent.snapshots.extract_frame")
    def test_no_snaps_returns_empty(self, mock_extract, tmp_path):
        """No snap keywords returns empty list."""
        segments = [SpeechSegment(0.0, 5.0, "No keywords at all")]
        video = tmp_path / "video.mp4"
        video.touch()

        snapshots = extract_all_snapshots(video, segments, tmp_path)

        assert snapshots == []
        mock_extract.assert_not_called()

    @patch("screen_feedback_agent.snapshots.extract_frame")
    def test_snapshot_has_correct_fields(self, mock_extract, tmp_path):
        """Returned Snapshot objects have correct fields."""
        mock_extract.return_value = tmp_path / "snap_2.50.png"

        segments = [SpeechSegment(0.0, 5.0, "Look at this snap")]
        video = tmp_path / "video.mp4"
        video.touch()

        snapshots = extract_all_snapshots(video, segments, tmp_path)

        assert len(snapshots) == 1
        snap = snapshots[0]
        assert isinstance(snap, Snapshot)
        assert snap.timestamp > 0
        assert snap.image_path == tmp_path / "snap_2.50.png"
        assert "snap" in snap.context.lower()


# --- cleanup_snapshots tests ---


class TestCleanupSnapshots:
    def test_removes_existing_files(self, tmp_path):
        """Cleanup removes image files."""
        img = tmp_path / "snap.png"
        img.write_bytes(b"fake image data")
        snapshots = [Snapshot(1.0, img, "test")]

        cleanup_snapshots(snapshots)

        assert not img.exists()

    def test_handles_missing_files(self, tmp_path):
        """Cleanup handles already-deleted files gracefully."""
        img = tmp_path / "missing.png"
        snapshots = [Snapshot(1.0, img, "test")]

        # Should not raise
        cleanup_snapshots(snapshots)
