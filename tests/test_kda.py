"""Tests for wr_analyzer.kda."""

import pytest
from support import IN_GAME_FRAMES, load_frame
from wr_analyzer.kda import (
    MAX_TEAM_KILLS,
    PlayerKDA,
    TeamKills,
    _KDA_RE,
    _KILLS_RE,
    detect_player_kda,
    detect_team_kills,
)


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

    def test_rejects_three_digit_numbers(self):
        """Three-digit kill counts are OCR noise, not real game data."""
        m = _KILLS_RE.search("6 V8 111")
        if m:
            assert int(m.group(2)) < 100
        m = _KILLS_RE.search("9 vs 213")
        if m:
            assert int(m.group(2)) < 100


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


# Ground truth kill scores from JjoDryfoCGs at 720p (1280x590).
# Verified by human visual inspection of 720p HUD crops.
EXPECTED_KILLS = {
    "in_game_06": TeamKills(blue=2, red=4),
    "in_game_07": TeamKills(blue=3, red=5),
    "in_game_09": TeamKills(blue=15, red=20),
    "in_game_10": TeamKills(blue=25, red=29),
}

# Frames where no kill reading is expected (no HUD or HUD obscured).
EXPECT_NO_KILLS = ["in_game_01"]


class TestDetectTeamKills:
    @pytest.mark.parametrize("name,expected", EXPECTED_KILLS.items())
    def test_ground_truth(self, name, expected):
        """Kill scores must match human-verified ground truth."""
        result = detect_team_kills(load_frame(name))
        assert result is not None, f"{name}: expected {expected}, got None"
        assert result == expected, f"{name}: expected {expected}, got {result}"

    @pytest.mark.parametrize("name", EXPECT_NO_KILLS)
    def test_no_hud_returns_none(self, name):
        """Frames without a visible HUD should return None."""
        assert detect_team_kills(load_frame(name)) is None

    def test_kills_within_plausible_range(self):
        """All detected kill values must be <= MAX_TEAM_KILLS."""
        for name in IN_GAME_FRAMES:
            result = detect_team_kills(load_frame(name))
            if result is not None:
                assert result.blue <= MAX_TEAM_KILLS, (
                    f"{name}: blue={result.blue} exceeds max"
                )
                assert result.red <= MAX_TEAM_KILLS, (
                    f"{name}: red={result.red} exceeds max"
                )


class TestDetectPlayerKda:
    def test_in_game_frame(self):
        """Player KDA may be detected from in-game frames.

        At 720p the KDA text is still small and OCR is unreliable,
        so we only verify that any detected results are well-formed.
        """
        sample = IN_GAME_FRAMES[1::2]
        for name in sample:
            result = detect_player_kda(load_frame(name))
            if result is not None:
                assert isinstance(result, PlayerKDA)
                assert result.kills >= 0
                assert result.deaths >= 0
                assert result.assists >= 0
