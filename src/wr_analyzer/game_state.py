"""Game start/end boundary detection.

Determines the current phase of a Wild Rift game by analysing visual
heuristics in each frame:

* **in_game** — the game timer is readable *or* the HUD scoreboard
  region contains bright pixels typical of the in-game overlay.
* **loading** — the top-right HUD area is very dark (no scoreboard) and
  the overall frame brightness is low.
* **post_game** — the frame is significantly brighter than a normal
  in-game frame, *or* contains a VICTORY/DEFEAT banner.
* **unknown** — none of the above matched.
"""

from __future__ import annotations

import cv2
import numpy as np

from wr_analyzer.regions import KILLS, SCOREBOARD
from wr_analyzer.result import detect_result
from wr_analyzer.timer import detect_game_time

# Brightness thresholds (mean grayscale of entire frame).
_LOADING_BRIGHTNESS_MAX = 40
_POSTGAME_BRIGHTNESS_MIN = 120

# The in-game kills region ("# VS #") has bright white/blue/red text
# on a dark overlay.  During gameplay the brightest pixel typically
# exceeds this value; during champ-select or menus it does not.
_HUD_BRIGHT_PIXEL_MIN = 100

# At least this fraction of the kills region should be "bright" (> 80)
# to count as HUD presence.  This filters out stray bright pixels from
# non-HUD content.
_HUD_BRIGHT_FRACTION_MIN = 0.02  # 2%


def _has_hud(frame: np.ndarray) -> bool:
    """Return ``True`` if the kills HUD region looks like an active game overlay."""
    kills_gray = cv2.cvtColor(KILLS.crop(frame), cv2.COLOR_BGR2GRAY)

    if int(kills_gray.max()) < _HUD_BRIGHT_PIXEL_MIN:
        return False

    bright_count = int(np.sum(kills_gray > 80))
    bright_frac = bright_count / kills_gray.size
    return bright_frac >= _HUD_BRIGHT_FRACTION_MIN


def detect_game_phase(frame: np.ndarray) -> str:
    """Return the game phase for *frame*.

    Returns one of ``"loading"``, ``"in_game"``, ``"post_game"``, or
    ``"unknown"``.
    """
    # If the game timer is readable, we are definitely in-game.
    if detect_game_time(frame) is not None:
        return "in_game"

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(gray.mean())

    # The scoreboard region should be populated during gameplay.
    # A very dark scoreboard region combined with a dark frame indicates
    # loading / champ-select.
    sb_crop = cv2.cvtColor(SCOREBOARD.crop(frame), cv2.COLOR_BGR2GRAY)
    sb_mean = float(sb_crop.mean())

    if mean_brightness < _LOADING_BRIGHTNESS_MAX and sb_mean < 30:
        return "loading"

    # End-of-game stat screens tend to be bright (white/light backgrounds).
    if mean_brightness > _POSTGAME_BRIGHTNESS_MIN:
        return "post_game"

    # The VICTORY/DEFEAT banner appears on post-game screens that aren't
    # necessarily bright overall (e.g. the scoreboard or animated banner).
    # Only run this OCR check when simpler heuristics haven't matched.
    if detect_result(frame) is not None:
        return "post_game"

    # Fallback: if the kills HUD region contains bright pixels typical of
    # the in-game overlay, classify as in_game even when OCR couldn't
    # read the exact timer text.
    if _has_hud(frame):
        return "in_game"

    return "unknown"
