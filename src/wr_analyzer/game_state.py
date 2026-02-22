"""Game start/end boundary detection.

Determines the current phase of a Wild Rift game by analysing visual
heuristics in each frame:

* **in_game** — the game timer is visible in the HUD.
* **loading** — the top-right HUD area is very dark (no scoreboard) and
  the overall frame brightness is low.
* **post_game** — the frame is significantly brighter than a normal
  in-game frame (end-of-game stats screen).
* **unknown** — none of the above matched.
"""

from __future__ import annotations

import cv2
import numpy as np

from wr_analyzer.regions import SCOREBOARD
from wr_analyzer.timer import detect_game_time

# Brightness thresholds (mean grayscale of entire frame).
_LOADING_BRIGHTNESS_MAX = 40
_POSTGAME_BRIGHTNESS_MIN = 120


def detect_game_phase(frame: np.ndarray) -> str:
    """Return the game phase for *frame*.

    Returns one of ``"loading"``, ``"in_game"``, ``"post_game"``, or
    ``"unknown"``.
    """
    # If the game timer is readable, we are in-game.
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

    return "unknown"
