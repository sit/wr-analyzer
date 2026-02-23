"""Game clock detection and parsing."""

from __future__ import annotations

import re

import numpy as np

from wr_analyzer.ocr import ocr_image, preprocess_otsu
from wr_analyzer.regions import GAME_TIMER, SCOREBOARD

# Matches "MM:SS" or "M:SS" patterns (colon may OCR as period/semicolon).
_TIMER_RE = re.compile(r"(\d{1,2})[:.;](\d{2})")


def parse_game_time(text: str) -> int | None:
    """Parse a timer string like ``"12:34"`` into total seconds.

    Returns ``None`` if *text* does not contain a valid ``MM:SS`` pattern.
    """
    m = _TIMER_RE.search(text)
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
    # Try the focused timer region.
    crop = GAME_TIMER.crop(frame)
    processed = preprocess_otsu(crop, scale=5)
    text = ocr_image(processed, psm=7, whitelist="0123456789:")
    secs = parse_game_time(text)
    if secs is not None:
        return f"{secs // 60}:{secs % 60:02d}"

    # Fallback: broader scoreboard region (more context for Tesseract).
    crop = SCOREBOARD.crop(frame)
    processed = preprocess_otsu(crop, scale=5)
    text = ocr_image(processed, psm=6)
    secs = parse_game_time(text)
    if secs is not None:
        return f"{secs // 60}:{secs % 60:02d}"

    return None
