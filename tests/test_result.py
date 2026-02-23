"""Tests for wr_analyzer.result."""

import numpy as np

from support import load_frame
from wr_analyzer.result import detect_result


class TestDetectResult:
    def test_victory_banner(self):
        """The VICTORY banner frame should be detected as victory."""
        assert detect_result(load_frame(2190)) == "victory"

    def test_victory_scoreboard(self):
        """The post-game scoreboard with VICTORY header should be detected."""
        assert detect_result(load_frame(2205)) == "victory"

    def test_in_game_returns_none(self):
        """In-game frames should not be detected as victory or defeat."""
        for ts in [600, 900, 1200]:
            assert detect_result(load_frame(ts)) is None

    def test_champ_select_returns_none(self):
        """Champion select frame should not trigger result detection."""
        assert detect_result(load_frame(300)) is None

    def test_black_frame_returns_none(self):
        """A black frame should not trigger result detection."""
        black = np.zeros((394, 854, 3), dtype=np.uint8)
        assert detect_result(black) is None
