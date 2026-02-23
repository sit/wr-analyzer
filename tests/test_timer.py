"""Tests for wr_analyzer.timer."""

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


class TestDetectGameTime:
    def test_in_game_frame(self):
        """At least some in-game frames should yield a timer reading."""
        readings = []
        for ts in [700, 900, 1500, 1800, 2000]:
            result = detect_game_time(load_frame(ts))
            if result is not None:
                readings.append(result)
        assert len(readings) >= 1

    def test_non_game_frame_returns_none(self):
        """Champ-select / loading frames should not return a timer."""
        assert detect_game_time(load_frame(300)) is None
