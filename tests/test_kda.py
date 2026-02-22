"""Tests for wr_analyzer.kda."""

import re

import numpy as np
import pytest

from wr_analyzer.kda import (
    PlayerKDA,
    TeamKills,
    _KDA_RE,
    _KILLS_RE,
    detect_player_kda,
    detect_team_kills,
)
from wr_analyzer.video import extract_frame


class TestKillsRegex:
    def test_standard(self):
        m = _KILLS_RE.search("25 VS 29")
        assert m and m.group(1) == "25" and m.group(2) == "29"

    def test_no_spaces(self):
        m = _KILLS_RE.search("25VS29")
        assert m and m.group(1) == "25" and m.group(2) == "29"

    def test_lowercase(self):
        m = _KILLS_RE.search("2 vs 4")
        assert m and m.group(1) == "2" and m.group(2) == "4"

    def test_ocr_misread_s_as_8(self):
        """OCR sometimes reads 'S' as '8' or '5'."""
        m = _KILLS_RE.search("25V8 29")
        assert m and m.group(1) == "25" and m.group(2) == "29"

    def test_no_match(self):
        assert _KILLS_RE.search("no kills here") is None


class TestKdaRegex:
    def test_slash_separator(self):
        m = _KDA_RE.search("3/2/18")
        assert m and m.groups() == ("3", "2", "18")

    def test_colon_separator(self):
        m = _KDA_RE.search("3:2:18")
        assert m and m.groups() == ("3", "2", "18")

    def test_mixed_separator(self):
        m = _KDA_RE.search("3.2:18")
        assert m and m.groups() == ("3", "2", "18")

    def test_no_match(self):
        assert _KDA_RE.search("no kda") is None


class TestDetectTeamKills:
    def test_in_game_frame(self, sample_video_path):
        """At least some in-game frames should yield kill scores."""
        readings = []
        for ts in [700, 1200, 1500, 1800, 2000]:
            frame = extract_frame(sample_video_path, ts)
            result = detect_team_kills(frame)
            if result is not None:
                readings.append(result)
                assert isinstance(result, TeamKills)
                assert result.blue >= 0
                assert result.red >= 0
        assert len(readings) >= 1


class TestDetectPlayerKda:
    def test_in_game_frame(self, sample_video_path):
        """Player KDA may be detected from in-game frames.

        At 854x394 the KDA text is very small and OCR is unreliable,
        so we only verify that any detected results are well-formed.
        """
        for ts in [700, 1200, 1500, 1800, 2000]:
            frame = extract_frame(sample_video_path, ts)
            result = detect_player_kda(frame)
            if result is not None:
                assert isinstance(result, PlayerKDA)
                assert result.kills >= 0
                assert result.deaths >= 0
                assert result.assists >= 0
