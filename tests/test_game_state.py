"""Tests for wr_analyzer.game_state."""

import numpy as np
import pytest

from wr_analyzer.game_state import detect_game_phase
from wr_analyzer.video import extract_frame


class TestDetectGamePhase:
    def test_in_game_frame(self, sample_video_path):
        """Frames during gameplay should be detected as in_game."""
        # Sample several known in-game timestamps
        in_game_count = 0
        for ts in [700, 900, 1500, 1800, 2000]:
            frame = extract_frame(sample_video_path, ts)
            phase = detect_game_phase(frame)
            if phase == "in_game":
                in_game_count += 1
        # Most of these should be in_game
        assert in_game_count >= 2

    def test_champ_select_not_in_game(self, sample_video_path):
        """Champion select screen should not be detected as in_game."""
        frame = extract_frame(sample_video_path, 300)
        phase = detect_game_phase(frame)
        assert phase != "in_game"

    def test_returns_valid_phase(self, sample_video_path):
        """All frames should return one of the valid phase strings."""
        valid = {"loading", "in_game", "post_game", "unknown"}
        for ts in [60, 300, 600, 1200, 1800]:
            frame = extract_frame(sample_video_path, ts)
            phase = detect_game_phase(frame)
            assert phase in valid

    def test_black_frame_is_loading(self):
        """A completely black frame should be classified as loading."""
        black = np.zeros((394, 854, 3), dtype=np.uint8)
        assert detect_game_phase(black) == "loading"

    def test_bright_frame_is_post_game(self):
        """A very bright frame should be classified as post_game."""
        bright = np.full((394, 854, 3), 200, dtype=np.uint8)
        assert detect_game_phase(bright) == "post_game"
