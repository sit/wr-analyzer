"""Tests for wr_analyzer.layout."""

from unittest.mock import patch

import numpy as np

from wr_analyzer.layout import validate_layout


def _frame():
    """Minimal dummy frame."""
    return np.zeros((394, 854, 3), dtype=np.uint8)


def test_valid_layout_enough_hits():
    frames = [_frame() for _ in range(5)]
    with patch("wr_analyzer.layout.detect_game_time", return_value="1:00"):
        assert validate_layout(frames, threshold=2) is True


def test_invalid_layout_too_few_hits():
    frames = [_frame() for _ in range(5)]
    with patch("wr_analyzer.layout.detect_game_time", return_value=None):
        assert validate_layout(frames, threshold=2) is False


def test_empty_frames():
    assert validate_layout([], threshold=1) is False


def test_mixed_hits():
    frames = [_frame() for _ in range(4)]
    results = ["1:00", None, "2:00", None]
    with patch("wr_analyzer.layout.detect_game_time", side_effect=results):
        # 2 hits out of 4, threshold=2 → valid
        assert validate_layout(frames, threshold=2) is True


def test_logs_warning_on_failure(caplog):
    frames = [_frame() for _ in range(3)]
    with patch("wr_analyzer.layout.detect_game_time", return_value=None):
        import logging

        with caplog.at_level(logging.WARNING):
            result = validate_layout(frames, threshold=2)
        assert result is False
        assert "custom HUD layout" in caplog.text
