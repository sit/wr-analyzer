"""Tests for wr_analyzer.regions."""

import numpy as np

from wr_analyzer.regions import (
    GAME_TIMER,
    KILLS_BLUE,
    KILLS_RED,
    MINIMAP,
    PixelBox,
    Region,
)


def test_region_to_pixels():
    r = Region(x=0.1, y=0.2, w=0.3, h=0.4)
    box = r.to_pixels(1000, 500)
    assert box == PixelBox(x=100, y=100, w=300, h=200)


def test_region_to_pixels_sample_resolution():
    """Test with the actual sample video resolution (854x394)."""
    box = GAME_TIMER.to_pixels(854, 394)
    # Timer should be roughly centered horizontally, at the very top
    assert 350 < box.x < 400
    assert box.y == 0
    assert 90 < box.w < 120
    assert 25 < box.h < 40


def test_region_crop():
    frame = np.zeros((394, 854, 3), dtype=np.uint8)
    # Paint the timer region white
    box = GAME_TIMER.to_pixels(854, 394)
    frame[box.y : box.y + box.h, box.x : box.x + box.w] = 255

    cropped = GAME_TIMER.crop(frame)
    assert cropped.shape[0] == box.h
    assert cropped.shape[1] == box.w
    assert cropped.mean() == 255.0


def test_kills_regions_flank_timer():
    """Blue kills region should be left of timer, red should be right."""
    w, h = 854, 394
    blue_box = KILLS_BLUE.to_pixels(w, h)
    timer_box = GAME_TIMER.to_pixels(w, h)
    red_box = KILLS_RED.to_pixels(w, h)

    # Blue should end at or before timer starts
    assert blue_box.x + blue_box.w <= timer_box.x + timer_box.w
    # Red should start at or after timer starts
    assert red_box.x >= timer_box.x
    # Both at top of screen
    assert blue_box.y < 10
    assert red_box.y < 10


def test_minimap_is_top_left():
    box = MINIMAP.to_pixels(854, 394)
    assert box.x == 0
    assert box.y == 0
    assert box.w > 100  # substantial area
    assert box.h > 100


def test_region_is_frozen():
    """Region should be immutable."""
    r = Region(x=0.0, y=0.0, w=0.5, h=0.5)
    try:
        r.x = 0.1
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_predefined_regions_within_bounds():
    """All predefined regions should stay within [0, 1]."""
    for region in [GAME_TIMER, KILLS_BLUE, KILLS_RED, MINIMAP]:
        assert 0.0 <= region.x <= 1.0
        assert 0.0 <= region.y <= 1.0
        assert 0.0 <= region.x + region.w <= 1.0
        assert 0.0 <= region.y + region.h <= 1.0
