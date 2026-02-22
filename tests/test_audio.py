"""Tests for audio detection and transcription (E6-S1)."""

from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

from screen_feedback_agent.audio import (
    SpeechSegment,
    detect_speech_segments_whisper,
    merge_speech_segments,
    merge_segments,
)


# --- SpeechSegment dataclass tests ---


class TestSpeechSegment:
    def test_creation(self):
        seg = SpeechSegment(start=1.0, end=5.0, text="hello world")
        assert seg.start == 1.0
        assert seg.end == 5.0
        assert seg.text == "hello world"

    def test_duration(self):
        seg = SpeechSegment(start=2.0, end=7.5, text="test")
        assert seg.end - seg.start == 5.5


# --- merge_speech_segments tests ---


class TestMergeSpeechSegments:
    def test_empty_list(self):
        assert merge_speech_segments([]) == []

    def test_single_segment(self):
        segments = [SpeechSegment(1.0, 3.0, "hello")]
        result = merge_speech_segments(segments)
        assert len(result) == 1
        assert result[0].text == "hello"

    def test_merges_adjacent(self):
        """Segments within 1s gap are merged."""
        segments = [
            SpeechSegment(0.0, 3.0, "Hello"),
            SpeechSegment(3.5, 6.0, "World"),
        ]
        result = merge_speech_segments(segments, gap_threshold=1.0)
        assert len(result) == 1
        assert result[0].start == 0.0
        assert result[0].end == 6.0
        assert result[0].text == "Hello World"

    def test_keeps_distant_separate(self):
        """Segments with > gap_threshold stay separate."""
        segments = [
            SpeechSegment(0.0, 2.0, "First"),
            SpeechSegment(5.0, 7.0, "Second"),
        ]
        result = merge_speech_segments(segments, gap_threshold=1.0)
        assert len(result) == 2
        assert result[0].text == "First"
        assert result[1].text == "Second"

    def test_merges_overlapping(self):
        """Overlapping segments are merged."""
        segments = [
            SpeechSegment(0.0, 4.0, "Part one"),
            SpeechSegment(3.0, 6.0, "Part two"),
        ]
        result = merge_speech_segments(segments, gap_threshold=1.0)
        assert len(result) == 1
        assert result[0].start == 0.0
        assert result[0].end == 6.0
        assert result[0].text == "Part one Part two"

    def test_custom_gap_threshold(self):
        """Custom gap threshold works."""
        segments = [
            SpeechSegment(0.0, 2.0, "A"),
            SpeechSegment(4.0, 6.0, "B"),
        ]
        # With gap_threshold=3.0, these should merge
        result = merge_speech_segments(segments, gap_threshold=3.0)
        assert len(result) == 1

        # With gap_threshold=1.0, they stay separate
        result = merge_speech_segments(segments, gap_threshold=1.0)
        assert len(result) == 2

    def test_multiple_merges_chain(self):
        """Multiple adjacent segments all merge into one."""
        segments = [
            SpeechSegment(0.0, 2.0, "A"),
            SpeechSegment(2.5, 4.0, "B"),
            SpeechSegment(4.3, 6.0, "C"),
        ]
        result = merge_speech_segments(segments, gap_threshold=1.0)
        assert len(result) == 1
        assert result[0].text == "A B C"
        assert result[0].start == 0.0
        assert result[0].end == 6.0


# --- Legacy merge_segments (tuple-based) tests ---


class TestMergeSegments:
    def test_empty(self):
        assert merge_segments([]) == []

    def test_no_merge_needed(self):
        segments = [(0.0, 2.0), (5.0, 7.0)]
        result = merge_segments(segments)
        assert result == [(0.0, 2.0), (5.0, 7.0)]

    def test_merges_close_segments(self):
        segments = [(0.0, 3.0), (3.5, 6.0)]
        result = merge_segments(segments, gap_threshold=1.0)
        assert result == [(0.0, 6.0)]


# --- detect_speech_segments_whisper tests (mocked) ---


class TestDetectSpeechSegmentsWhisper:
    def _make_mock_segment(self, start: float, end: float, text: str):
        """Create a mock Whisper segment."""
        seg = MagicMock()
        seg.start = start
        seg.end = end
        seg.text = text
        return seg

    @patch("faster_whisper.WhisperModel")
    def test_basic_detection(self, mock_model_cls):
        """Detects speech segments from Whisper output."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model

        # Segments far enough apart to not merge after padding
        mock_segments = [
            self._make_mock_segment(2.0, 5.0, " Hello world "),
            self._make_mock_segment(15.0, 18.0, " This is a test "),
        ]
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter(mock_segments), mock_info)

        result = detect_speech_segments_whisper(
            Path("test.mp4"),
            padding_before=2.0,
            padding_after=2.0,
        )

        assert len(result) == 2
        assert result[0].start == 0.0  # max(0, 2.0 - 2.0)
        assert result[0].end == 7.0  # 5.0 + 2.0
        assert result[0].text == "Hello world"
        assert result[1].start == 13.0  # 15.0 - 2.0
        assert result[1].end == 20.0  # 18.0 + 2.0
        assert result[1].text == "This is a test"

    @patch("faster_whisper.WhisperModel")
    def test_filters_short_segments(self, mock_model_cls):
        """Segments shorter than min_duration are filtered out."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model

        mock_segments = [
            self._make_mock_segment(1.0, 1.3, " click "),  # 0.3s < 0.5s min
            self._make_mock_segment(3.0, 6.0, " Actual speech "),
        ]
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter(mock_segments), mock_info)

        result = detect_speech_segments_whisper(
            Path("test.mp4"), min_duration=0.5,
        )

        assert len(result) == 1
        assert result[0].text == "Actual speech"

    @patch("faster_whisper.WhisperModel")
    def test_empty_audio(self, mock_model_cls):
        """No speech detected returns empty list."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter([]), mock_info)

        result = detect_speech_segments_whisper(Path("silent.mp4"))
        assert result == []

    @patch("faster_whisper.WhisperModel")
    def test_vad_parameters_passed(self, mock_model_cls):
        """VAD parameters are passed to transcribe."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter([]), mock_info)

        detect_speech_segments_whisper(Path("test.mp4"))

        mock_model.transcribe.assert_called_once()
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs["vad_filter"] is True
        assert call_kwargs["word_timestamps"] is True
        assert call_kwargs["vad_parameters"]["min_speech_duration_ms"] == 500
        assert call_kwargs["vad_parameters"]["min_silence_duration_ms"] == 300

    @patch("faster_whisper.WhisperModel")
    def test_adjacent_segments_merged(self, mock_model_cls):
        """Adjacent speech segments within merge_gap are merged."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model

        # With padding=2.0, these segments will overlap: (0, 5) and (3, 10)
        mock_segments = [
            self._make_mock_segment(2.0, 3.0, " Hello "),
            self._make_mock_segment(5.0, 8.0, " World "),
        ]
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter(mock_segments), mock_info)

        result = detect_speech_segments_whisper(
            Path("test.mp4"),
            padding_before=2.0,
            padding_after=2.0,
            merge_gap=1.0,
        )

        # Segments overlap after padding: (0, 5) and (3, 10) -> merged to (0, 10)
        assert len(result) == 1
        assert result[0].text == "Hello World"

    @patch("faster_whisper.WhisperModel")
    def test_model_size_passed(self, mock_model_cls):
        """Model size parameter is passed to WhisperModel."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter([]), mock_info)

        detect_speech_segments_whisper(Path("test.mp4"), model_size="large-v3")

        mock_model_cls.assert_called_once_with("large-v3", compute_type="int8")

    @patch("faster_whisper.WhisperModel")
    def test_padding_clamps_to_zero(self, mock_model_cls):
        """Start time is clamped to 0 when padding exceeds start."""
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model

        mock_segments = [
            self._make_mock_segment(0.5, 2.0, " Early speech "),
        ]
        mock_info = MagicMock()
        mock_model.transcribe.return_value = (iter(mock_segments), mock_info)

        result = detect_speech_segments_whisper(
            Path("test.mp4"), padding_before=2.0,
        )

        assert result[0].start == 0.0  # Clamped, not -1.5
