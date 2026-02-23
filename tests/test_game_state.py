"""Tests for wr_analyzer.game_state."""

import numpy as np

from support import load_frame
from wr_analyzer.game_state import detect_game_phase


class TestDetectGamePhase:
    def test_in_game_frame(self):
        """Frames during gameplay should be detected as in_game."""
        in_game_count = 0
        for ts in [700, 900, 1500, 1800, 2000]:
            if detect_game_phase(load_frame(ts)) == "in_game":
                in_game_count += 1
        assert in_game_count >= 2

    def test_champ_select_not_in_game(self):
        """Champion select screen should not be detected as in_game."""
        assert detect_game_phase(load_frame(300)) != "in_game"

    def test_returns_valid_phase(self):
        """All frames should return one of the valid phase strings."""
        valid = {"loading", "in_game", "post_game", "unknown"}
        for ts in [60, 300, 600, 1200, 1800]:
            assert detect_game_phase(load_frame(ts)) in valid

    def test_black_frame_is_loading(self):
        """A completely black frame should be classified as loading."""
        black = np.zeros((394, 854, 3), dtype=np.uint8)
        assert detect_game_phase(black) == "loading"

    def test_bright_frame_is_post_game(self):
        """A very bright frame should be classified as post_game."""
        bright = np.full((394, 854, 3), 200, dtype=np.uint8)
        assert detect_game_phase(bright) == "post_game"

    def test_victory_frame_is_post_game(self):
        """The VICTORY banner frame should be classified as post_game."""
        assert detect_game_phase(load_frame(2190)) == "post_game"

    def test_scoreboard_frame_is_post_game(self):
        """The post-game scoreboard should be classified as post_game."""
        assert detect_game_phase(load_frame(2205)) == "post_game"
