"""Game clock detection and parsing."""

from __future__ import annotations

import re

import numpy as np

from wr_analyzer.ocr import ocr_easyocr, preprocess_clahe
from wr_analyzer.regions import GAME_TIMER, SCOREBOARD

# Matches "MM:SS" or "M:SS" patterns.  The colon may OCR as period,
# semicolon, asterisk, or a letter/digit (e.g. "17e35", "07835").
_TIMER_RE = re.compile(r"(\d{1,2})[:.;*eE](\d{2})")

# Fallback: four consecutive digits with no separator (e.g. "1735" → 17:35).
_TIMER_NOSEP_RE = re.compile(r"(\d{1,2})(\d{2})\b")


def parse_game_time(text: str) -> int | None:
    """Parse a timer string like ``"12:34"`` into total seconds.

    Returns ``None`` if *text* does not contain a valid ``MM:SS`` pattern.
    """
    m = _TIMER_RE.search(text)
    if m is None:
        m = _TIMER_NOSEP_RE.search(text)
    if m is None:
        return None
    minutes, seconds = int(m.group(1)), int(m.group(2))
    if seconds >= 60 or minutes > 40:
        return None
    return minutes * 60 + seconds


def detect_game_time(frame: np.ndarray) -> str | None:
    """Extract the game clock from a video frame.

    Tries the dedicated timer region first; falls back to the broader
    scoreboard region and regex extraction.

    Returns the time as ``"MM:SS"`` or ``None`` if not detected.
    """
    # Try the focused timer region with CLAHE + EasyOCR at multiple scales.
    crop = GAME_TIMER.crop(frame)
    for scale in (5, 4, 3):
        enhanced = preprocess_clahe(crop, scale=scale)
        parts = ocr_easyocr(enhanced)
        text = " ".join(parts)
        secs = parse_game_time(text)
        if secs is not None:
            return f"{secs // 60}:{secs % 60:02d}"

    # Fallback: broader scoreboard region.
    crop = SCOREBOARD.crop(frame)
    enhanced = preprocess_clahe(crop, scale=3)
    parts = ocr_easyocr(enhanced)
    text = " ".join(parts)
    secs = parse_game_time(text)
    if secs is not None:
        return f"{secs // 60}:{secs % 60:02d}"

    return None
