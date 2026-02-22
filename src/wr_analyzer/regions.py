"""Screen region definitions (ROIs) for Wild Rift UI elements.

Regions are defined as ratios (0.0-1.0) of frame dimensions so they are
resolution-independent.  Pixel coordinates are computed at runtime via
Region.to_pixels().

These initial values are best-guess approximations based on the default
Wild Rift mobile layout and will need tuning against real frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple


class PixelBox(NamedTuple):
    """Absolute pixel coordinates: (x, y, width, height)."""
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class Region:
    """A rectangular region defined as ratios of frame size.

    (x, y) is the top-left corner; (w, h) is the size.
    All values are in [0.0, 1.0].
    """
    x: float
    y: float
    w: float
    h: float

    def to_pixels(self, frame_w: int, frame_h: int) -> PixelBox:
        """Convert ratio-based region to absolute pixel coordinates."""
        return PixelBox(
            x=int(self.x * frame_w),
            y=int(self.y * frame_h),
            w=int(self.w * frame_w),
            h=int(self.h * frame_h),
        )

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
# ---------------------------------------------------------------------------

# Game clock ("12:34") — top center of screen
GAME_TIMER = Region(x=0.44, y=0.0, w=0.12, h=0.08)

# Team kill scores — flanking the timer
KILLS_BLUE = Region(x=0.35, y=0.0, w=0.09, h=0.07)
KILLS_RED = Region(x=0.56, y=0.0, w=0.09, h=0.07)

# Minimap — top-left corner (default placement)
MINIMAP = Region(x=0.0, y=0.0, w=0.22, h=0.45)

# Player champion portrait + level — bottom-left
PLAYER_PORTRAIT = Region(x=0.0, y=0.70, w=0.12, h=0.30)

# Ability buttons — bottom-right cluster
ABILITIES = Region(x=0.65, y=0.55, w=0.35, h=0.45)

# Gold display — bottom center
GOLD = Region(x=0.40, y=0.90, w=0.20, h=0.10)

# Event / kill feed — left side
EVENT_FEED = Region(x=0.0, y=0.10, w=0.25, h=0.30)
