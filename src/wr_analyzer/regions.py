"""Screen region definitions (ROIs) for Wild Rift UI elements.

Regions are defined as pixel offsets from an anchor corner at a reference
resolution (854×394).  The anchor ensures that HUD elements stay correctly
located regardless of frame aspect ratio — the game's HUD is pixel-anchored
to screen edges, and extra vertical space extends the game world, not the HUD.

Pixel offsets are scaled proportionally with frame width at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class PixelBox(NamedTuple):
    """Absolute pixel coordinates: (x, y, width, height)."""

    x: int
    y: int
    w: int
    h: int


class Anchor(Enum):
    """Corner or edge that a region is anchored to."""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    TOP_CENTER = "top_center"
    BOTTOM_CENTER = "bottom_center"


# Reference frame dimensions used when measuring pixel offsets.
REF_WIDTH: int = 854
REF_HEIGHT: int = 394


@dataclass(frozen=True)
class Region:
    """A rectangular region anchored to a screen corner/edge.

    *x* and *y* are margin distances (in reference pixels) from the anchor:

    * TOP_LEFT / BOTTOM_LEFT: *x* = left margin, *y* = top/bottom margin.
    * TOP_RIGHT / BOTTOM_RIGHT: *x* = right margin, *y* = top/bottom margin.
    * TOP_CENTER / BOTTOM_CENTER: *x* = horizontal offset of region centre
      from frame centre (positive = rightward), *y* = top/bottom margin.

    *w* and *h* are the region's width and height in reference pixels.
    """

    anchor: Anchor
    x: int
    y: int
    w: int
    h: int

    def to_pixels(self, frame_w: int, frame_h: int) -> PixelBox:
        """Convert to absolute pixel coordinates for a given frame size.

        All reference-pixel values are scaled by ``frame_w / REF_WIDTH`` so
        the HUD regions track the game's resolution scaling.  The anchor
        corner handles aspect-ratio differences (extra height goes to the
        game world, not the HUD).
        """
        scale = frame_w / REF_WIDTH
        sw = int(self.w * scale)
        sh = int(self.h * scale)
        sx = int(self.x * scale)
        sy = int(self.y * scale)

        anchor = self.anchor

        if anchor is Anchor.TOP_LEFT:
            ax, ay = sx, sy
        elif anchor is Anchor.TOP_RIGHT:
            ax, ay = frame_w - sx - sw, sy
        elif anchor is Anchor.BOTTOM_LEFT:
            ax, ay = sx, frame_h - sy - sh
        elif anchor is Anchor.BOTTOM_RIGHT:
            ax, ay = frame_w - sx - sw, frame_h - sy - sh
        elif anchor is Anchor.TOP_CENTER:
            ax = (frame_w - sw) // 2 + sx
            ay = sy
        elif anchor is Anchor.BOTTOM_CENTER:
            ax = (frame_w - sw) // 2 + sx
            ay = frame_h - sy - sh
        else:
            raise ValueError(f"Unknown anchor: {anchor!r}")

        # Clamp to frame bounds.
        ax = max(0, min(ax, frame_w - 1))
        ay = max(0, min(ay, frame_h - 1))
        sw = min(sw, frame_w - ax)
        sh = min(sh, frame_h - ay)

        return PixelBox(x=ax, y=ay, w=sw, h=sh)

    def crop(self, frame):
        """Crop a numpy/OpenCV frame to this region.

        Parameters
        ----------
        frame : numpy.ndarray
            An OpenCV image (H, W, C).

        Returns
        -------
        numpy.ndarray
            The cropped sub-image.
        """
        h, w = frame.shape[:2]
        box = self.to_pixels(w, h)
        return frame[box.y : box.y + box.h, box.x : box.x + box.w]


# ---------------------------------------------------------------------------
# Predefined regions for the default Wild Rift HUD layout
#
# Calibrated against 854×394 sample video (JjoDryfoCGs).  Pixel offsets are
# measured from the anchor corner at that resolution.
# ---------------------------------------------------------------------------

# Broad scoreboard area — captures kills "# VS #", timer, and KDA.
# Anchored top-right; right margin = 112, top margin = 0.
SCOREBOARD = Region(anchor=Anchor.TOP_RIGHT, x=112, y=0, w=145, h=47)

# Game clock ("12:34") — top-right, second row below kill scores.
# Right margin = 180, top margin = 15.
GAME_TIMER = Region(anchor=Anchor.TOP_RIGHT, x=180, y=15, w=68, h=23)

# Team kill scores ("# VS #") — top-right, first row.
# Right margin = 146, top margin = 0.
# Height limited to 14px to avoid overlapping the GAME_TIMER region below.
KILLS = Region(anchor=Anchor.TOP_RIGHT, x=146, y=0, w=111, h=14)

# Player KDA ("K/D/A") — top-right, right of kill scores.
# Right margin = 104, top margin = 0.
PLAYER_KDA = Region(anchor=Anchor.TOP_RIGHT, x=104, y=0, w=59, h=23)

# Minimap — top-left corner (default placement).
MINIMAP = Region(anchor=Anchor.TOP_LEFT, x=0, y=0, w=187, h=177)

# Player champion portrait + level — bottom-left.
PLAYER_PORTRAIT = Region(anchor=Anchor.BOTTOM_LEFT, x=0, y=1, w=102, h=118)

# Ability buttons — bottom-right cluster.
ABILITIES = Region(anchor=Anchor.BOTTOM_RIGHT, x=1, y=1, w=298, h=177)

# Gold display — bottom centre.
GOLD = Region(anchor=Anchor.BOTTOM_CENTER, x=0, y=1, w=170, h=39)

# Event / kill feed — left side, below minimap.
EVENT_FEED = Region(anchor=Anchor.TOP_LEFT, x=0, y=39, w=213, h=118)
