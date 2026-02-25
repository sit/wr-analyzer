"""Tests for wr_analyzer.regions."""

import numpy as np
import pytest

from wr_analyzer.regions import (
    GAME_TIMER,
    KILLS,
    MINIMAP,
    PLAYER_KDA,
    SCOREBOARD,
    Anchor,
    PixelBox,
    REF_HEIGHT,
    REF_WIDTH,
    Region,
)


def test_top_left_anchor():
    r = Region(anchor=Anchor.TOP_LEFT, x=10, y=20, w=100, h=50)
    box = r.to_pixels(REF_WIDTH, REF_HEIGHT)
    assert box == PixelBox(x=10, y=20, w=100, h=50)


def test_top_right_anchor():
    r = Region(anchor=Anchor.TOP_RIGHT, x=10, y=5, w=100, h=50)
    box = r.to_pixels(REF_WIDTH, REF_HEIGHT)
    # x should be: 854 - 10 - 100 = 744
    assert box == PixelBox(x=744, y=5, w=100, h=50)


def test_bottom_left_anchor():
    r = Region(anchor=Anchor.BOTTOM_LEFT, x=0, y=10, w=100, h=50)
    box = r.to_pixels(REF_WIDTH, REF_HEIGHT)
    # y should be: 394 - 10 - 50 = 334
    assert box == PixelBox(x=0, y=334, w=100, h=50)


def test_bottom_right_anchor():
    r = Region(anchor=Anchor.BOTTOM_RIGHT, x=5, y=5, w=100, h=50)
    box = r.to_pixels(REF_WIDTH, REF_HEIGHT)
    assert box == PixelBox(x=749, y=339, w=100, h=50)


def test_top_center_anchor():
    r = Region(anchor=Anchor.TOP_CENTER, x=0, y=10, w=200, h=50)
    box = r.to_pixels(REF_WIDTH, REF_HEIGHT)
    # Centred: (854 - 200) // 2 = 327
    assert box == PixelBox(x=327, y=10, w=200, h=50)


def test_bottom_center_anchor():
    r = Region(anchor=Anchor.BOTTOM_CENTER, x=0, y=5, w=200, h=40)
    box = r.to_pixels(REF_WIDTH, REF_HEIGHT)
    assert box == PixelBox(x=327, y=349, w=200, h=40)


def test_scaling_with_larger_width():
    """At 2x width, offsets and sizes double."""
    r = Region(anchor=Anchor.TOP_LEFT, x=10, y=20, w=100, h=50)
    box = r.to_pixels(REF_WIDTH * 2, REF_HEIGHT * 2)
    assert box == PixelBox(x=20, y=40, w=200, h=100)


def test_aspect_ratio_invariance_top_right():
    """Top-right regions maintain pixel position when only height changes."""
    box_ref = GAME_TIMER.to_pixels(854, 394)
    box_wide = GAME_TIMER.to_pixels(854, 480)
    # Same x, y, w, h — height change does not affect top-anchored regions
    assert box_ref.x == box_wide.x
    assert box_ref.y == box_wide.y
    assert box_ref.w == box_wide.w
    assert box_ref.h == box_wide.h


def test_aspect_ratio_shifts_bottom_anchored():
    """Bottom-anchored regions shift down when height increases."""
    from wr_analyzer.regions import PLAYER_PORTRAIT

    box_ref = PLAYER_PORTRAIT.to_pixels(854, 394)
    box_tall = PLAYER_PORTRAIT.to_pixels(854, 480)
    assert box_tall.x == box_ref.x
    assert box_tall.y > box_ref.y  # shifted down
    assert box_tall.y == 480 - 1 - 118  # bottom margin = 1


def test_region_to_pixels_sample_resolution():
    """Timer region should be in the top-right of the screen."""
    box = GAME_TIMER.to_pixels(854, 394)
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


def test_kills_in_top_right():
    """Kill scores should be in the top-right corner."""
    w, h = 854, 394
    kills_box = KILLS.to_pixels(w, h)
    assert kills_box.x > w * 0.6
    assert kills_box.y < 10


def test_scoreboard_encompasses_kills_and_timer():
    """The broad scoreboard region should contain both kills and timer."""
    w, h = 854, 394
    sb = SCOREBOARD.to_pixels(w, h)
    kills = KILLS.to_pixels(w, h)
    timer = GAME_TIMER.to_pixels(w, h)

    assert sb.x <= kills.x
    assert sb.x <= timer.x
    assert sb.y + sb.h >= timer.y + timer.h


def test_minimap_is_top_left():
    box = MINIMAP.to_pixels(854, 394)
    assert box.x == 0
    assert box.y == 0
    assert box.w > 100
    assert box.h > 100


def test_region_is_frozen():
    r = Region(anchor=Anchor.TOP_LEFT, x=0, y=0, w=50, h=50)
    with pytest.raises(AttributeError):
        r.x = 10


def test_predefined_regions_within_frame():
    """All predefined regions should resolve within frame bounds."""
    for region in [GAME_TIMER, KILLS, PLAYER_KDA, SCOREBOARD, MINIMAP]:
        box = region.to_pixels(854, 394)
        assert box.x >= 0
        assert box.y >= 0
        assert box.x + box.w <= 854
        assert box.y + box.h <= 394


def test_clamping_prevents_negative():
    """Extreme offsets should clamp to frame bounds, not go negative."""
    r = Region(anchor=Anchor.TOP_RIGHT, x=900, y=0, w=100, h=50)
    box = r.to_pixels(854, 394)
    assert box.x >= 0
    assert box.w > 0
