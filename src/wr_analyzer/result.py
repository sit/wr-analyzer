"""Win/loss detection from post-game screens.

Detects "VICTORY" or "DEFEAT" text that appears on the end-of-game
banner and the post-game scoreboard in Wild Rift.
"""

from __future__ import annotations

import re

import numpy as np

from wr_analyzer.ocr import ocr_easyocr, preprocess_clahe
from wr_analyzer.regions import Anchor, Region

# Two regions to check — the VICTORY/DEFEAT text appears in different
# positions on the animated banner vs. the post-game scoreboard.
#
# Banner region: the large centred banner shown right after game end.
# Centred horizontally, 19px from top at 854×394 reference.
_RESULT_BANNER = Region(anchor=Anchor.TOP_CENTER, x=0, y=19, w=427, h=137)
# Scoreboard header: smaller text at the very top of the stats screen.
_RESULT_SCOREBOARD = Region(anchor=Anchor.TOP_CENTER, x=0, y=0, w=341, h=47)

# Patterns tolerant of common OCR misreads.
# "VICTORY" often appears as "Victory", "VICTARY", "VICTQRY", etc.
# "DEFEAT" often appears as "OEFEAT", etc.
_VICTORY_RE = re.compile(r"vict", re.IGNORECASE)
_DEFEAT_RE = re.compile(r"def\s*eat", re.IGNORECASE)


def _match_text(text: str) -> str | None:
    """Return ``"victory"``, ``"defeat"``, or ``None``."""
    if _VICTORY_RE.search(text):
        return "victory"
    if _DEFEAT_RE.search(text):
        return "defeat"
    return None


def detect_result(frame: np.ndarray) -> str | None:
    """Detect win/loss from a post-game frame.

    Tries the large centred banner region first (animated victory/defeat
    splash), then falls back to the scoreboard header region (post-game
    stats screen).

    Parameters
    ----------
    frame : np.ndarray
        A BGR frame (OpenCV format).

    Returns
    -------
    str | None
        ``"victory"``, ``"defeat"``, or ``None`` if no result is detected.
    """
    for region in (_RESULT_BANNER, _RESULT_SCOREBOARD):
        crop = region.crop(frame)
        enhanced = preprocess_clahe(crop, scale=4)
        parts = ocr_easyocr(enhanced)
        text = " ".join(parts)
        result = _match_text(text)
        if result is not None:
            return result
    return None
