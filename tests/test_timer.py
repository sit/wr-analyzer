"""Tests for wr_analyzer.timer."""

import numpy as np
import pytest

from wr_analyzer.timer import detect_game_time, parse_game_time
from wr_analyzer.video import extract_frame


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
    def test_in_game_frame(self, sample_video_path):
        """At least some in-game frames should yield a timer reading."""
        # Sample several frames during gameplay
        readings = []
        for ts in [700, 900, 1500, 1800, 2000]:
            frame = extract_frame(sample_video_path, ts)
            result = detect_game_time(frame)
            if result is not None:
                readings.append(result)
        # We expect at least one successful read from 5 in-game frames
        assert len(readings) >= 1

    def test_non_game_frame_returns_none(self, sample_video_path):
        """Champ-select / loading frames should not return a timer."""
        frame = extract_frame(sample_video_path, 300)  # champ select
        assert detect_game_time(frame) is None
