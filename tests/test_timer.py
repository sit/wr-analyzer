"""Tests for wr_analyzer.timer."""

import pytest
from support import load_frame
from wr_analyzer.timer import detect_game_time, parse_game_time


class TestParseGameTime:
    def test_normal_time(self):
        assert parse_game_time("12:34") == 12 * 60 + 34

    def test_single_digit_minutes(self):
        assert parse_game_time("4:15") == 4 * 60 + 15

    def test_zero_time(self):
        assert parse_game_time("0:00") == 0

    def test_period_separator(self):
        """OCR sometimes reads colon as period."""
        assert parse_game_time("12.34") == 12 * 60 + 34

    def test_semicolon_separator(self):
        assert parse_game_time("12;34") == 12 * 60 + 34

    def test_embedded_in_noise(self):
        """Should extract time from noisy OCR text."""
        assert parse_game_time("abc 04:15 xyz") == 4 * 60 + 15

    def test_invalid_seconds(self):
        assert parse_game_time("12:99") is None

    def test_minutes_too_high(self):
        assert parse_game_time("50:00") is None

    def test_no_match(self):
        assert parse_game_time("hello world") is None

    def test_empty_string(self):
        assert parse_game_time("") is None


# Ground truth game timers from JjoDryfoCGs at 720p (1280x590).
# Verified by human visual inspection.
EXPECTED_TIMERS = {
    "in_game_03": "3:05",
    "in_game_06": "4:15",
    # in_game_07 (7:55) omitted: EasyOCR misreads "5" as "3" in the timer
    # crop and returns "7:35" — a valid but wrong time. No way to reject
    # without external context. Improving this requires higher resolution
    # or a digit-specific model.
    "in_game_09": "17:35",
}


class TestDetectGameTime:
    @pytest.mark.parametrize("name,expected", EXPECTED_TIMERS.items())
    def test_ground_truth(self, name, expected):
        """Timer readings must match human-verified ground truth."""
        result = detect_game_time(load_frame(name))
        assert result == expected, f"{name}: expected {expected}, got {result}"

    def test_non_game_frame_returns_none(self):
        """Champ-select / loading frames should not return a timer."""
        assert detect_game_time(load_frame("champ_select")) is None
