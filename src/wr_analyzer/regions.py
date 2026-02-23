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
#
# Calibrated against 854x394 sample video.  The in-game HUD places the
# scoreboard in the top-right (not top-center).
# ---------------------------------------------------------------------------

# Broad scoreboard area — captures kills "# VS #", timer, and KDA.
# Useful for a single OCR pass when individual regions are too noisy.
SCOREBOARD = Region(x=0.70, y=0.0, w=0.17, h=0.12)

# Game clock ("12:34") — top-right, second row below kill scores
GAME_TIMER = Region(x=0.71, y=0.04, w=0.08, h=0.06)

# Team kill scores ("# VS #") — top-right, first row
KILLS = Region(x=0.70, y=0.0, w=0.13, h=0.06)

# Player KDA ("K/D/A") — top-right, right of kill scores
PLAYER_KDA = Region(x=0.81, y=0.0, w=0.07, h=0.06)

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
