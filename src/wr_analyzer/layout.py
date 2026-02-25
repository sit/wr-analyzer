"""HUD layout validation.

Checks whether the default HUD region definitions match the actual game
layout in a frame.  Wild Rift allows full HUD customisation, so the
default corner-anchored regions may not apply to all videos.

Currently performs a lightweight smoke test (timer presence).  Future work
may add search/scan logic to locate HUD elements dynamically.
"""

from __future__ import annotations

import logging

import numpy as np

from wr_analyzer.timer import detect_game_time

logger = logging.getLogger(__name__)


def validate_layout(frames: list[np.ndarray], *, threshold: int = 2) -> bool:
    """Check whether the default HUD layout is detectable.

    Runs timer OCR on the provided in-game frames.  If the timer is
    successfully read on at least *threshold* frames, the layout is
    considered valid.

    Parameters
    ----------
    frames : list[np.ndarray]
        A handful of in-game BGR frames (3-10 is sufficient).
    threshold : int
        Minimum number of frames where the timer must be detected.

    Returns
    -------
    bool
        ``True`` if the default layout appears correct.
    """
    if not frames:
        return False

    hits = sum(1 for f in frames if detect_game_time(f) is not None)

    if hits >= threshold:
        return True

    logger.warning(
        "HUD layout validation failed: timer detected in %d/%d frames "
        "(need %d).  The video may use a custom HUD layout.  "
        "OCR results may be unreliable.",
        hits,
        len(frames),
        threshold,
    )
    return False
