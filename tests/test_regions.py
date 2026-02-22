"""Tests for wr_analyzer.regions."""

import numpy as np

from wr_analyzer.regions import (
    GAME_TIMER,
    KILLS,
    MINIMAP,
    PLAYER_KDA,
    SCOREBOARD,
    PixelBox,
    Region,
)


def test_region_to_pixels():
    r = Region(x=0.1, y=0.2, w=0.3, h=0.4)
    box = r.to_pixels(1000, 500)
    assert box == PixelBox(x=100, y=100, w=300, h=200)


def test_region_to_pixels_sample_resolution():
    """Timer region should be in the top-right of the screen."""
    box = GAME_TIMER.to_pixels(854, 394)
    # Timer is in the top-right area (x > 600)
    assert box.x > 600
    assert box.y < 30


def test_region_crop():
    frame = np.zeros((394, 854, 3), dtype=np.uint8)
    box = GAME_TIMER.to_pixels(854, 394)
    frame[box.y : box.y + box.h, box.x : box.x + box.w] = 255

    cropped = GAME_TIMER.crop(frame)
    assert cropped.shape[0] == box.h
    assert cropped.shape[1] == box.w
    assert cropped.mean() == 255.0


def test_kills_and_timer_are_in_top_right():
    """Kill scores and timer should both be in the top-right."""
    w, h = 854, 394
    kills_box = KILLS.to_pixels(w, h)
    timer_box = GAME_TIMER.to_pixels(w, h)

    # Both in the right portion of the screen
    assert kills_box.x > w * 0.6
    assert timer_box.x > w * 0.6
    # Both near the top
    assert kills_box.y < 10
    assert timer_box.y < 30


def test_scoreboard_encompasses_kills_and_timer():
    """The broad scoreboard region should contain both kills and timer."""
    w, h = 854, 394
    sb = SCOREBOARD.to_pixels(w, h)
    kills = KILLS.to_pixels(w, h)
    timer = GAME_TIMER.to_pixels(w, h)

    # Scoreboard left edge is at or before both sub-regions
    assert sb.x <= kills.x
    assert sb.x <= timer.x
    # Scoreboard bottom edge extends past both
    assert sb.y + sb.h >= timer.y + timer.h


def test_minimap_is_top_left():
    box = MINIMAP.to_pixels(854, 394)
    assert box.x == 0
    assert box.y == 0
    assert box.w > 100
    assert box.h > 100


def test_region_is_frozen():
    r = Region(x=0.0, y=0.0, w=0.5, h=0.5)
    try:
        r.x = 0.1
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_predefined_regions_within_bounds():
    """All predefined regions should stay within [0, 1]."""
    for region in [GAME_TIMER, KILLS, PLAYER_KDA, SCOREBOARD, MINIMAP]:
        assert 0.0 <= region.x <= 1.0
        assert 0.0 <= region.y <= 1.0
        assert 0.0 <= region.x + region.w <= 1.0
        assert 0.0 <= region.y + region.h <= 1.0
