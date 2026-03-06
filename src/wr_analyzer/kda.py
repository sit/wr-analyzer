"""Kills/deaths/assists extraction from the in-game HUD."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from wr_analyzer.ocr import ocr_easyocr, preprocess_clahe
from wr_analyzer.regions import KILLS, PLAYER_KDA, SCOREBOARD

# "# VS #" — V may OCR as V/v, S may OCR as 5/8/s/Y.
# Limited to 2-digit numbers: no real game reaches 100 kills per team.
_KILLS_RE = re.compile(r"(\d{1,2})\s*[VvYy][Ss58]\s*(\d{1,2})")

# Upper bound on plausible team kills in a single Wild Rift game.
MAX_TEAM_KILLS = 60

# "K/D/A" or "K:D:A" — separator may OCR as /.:,
_KDA_RE = re.compile(r"(\d{1,2})[/:.,;\s](\d{1,2})[/:.,;\s](\d{1,2})")


@dataclass(frozen=True)
class TeamKills:
    """Blue and red team kill counts."""

    blue: int
    red: int


@dataclass(frozen=True)
class PlayerKDA:
    """Player kills, deaths, assists."""

    kills: int
    deaths: int
    assists: int


def _valid_kills(m: re.Match) -> TeamKills | None:
    """Build a TeamKills from a regex match, rejecting implausible values."""
    blue, red = int(m.group(1)), int(m.group(2))
    if blue > MAX_TEAM_KILLS or red > MAX_TEAM_KILLS:
        return None
    return TeamKills(blue=blue, red=red)


def _ocr_kills_text(crop: np.ndarray, scale: int = 4) -> str:
    """CLAHE-preprocess a crop and OCR it with EasyOCR, returning joined text."""
    enhanced = preprocess_clahe(crop, scale=scale)
    parts = ocr_easyocr(enhanced)
    return " ".join(parts)


def detect_team_kills(frame: np.ndarray) -> TeamKills | None:
    """Extract team kill scores (``# VS #``) from a frame.

    Returns ``None`` if the pattern is not detected.
    """
    # Try focused kills region with CLAHE + EasyOCR.
    crop = KILLS.crop(frame)
    text = _ocr_kills_text(crop, scale=4)
    m = _KILLS_RE.search(text)
    if m:
        result = _valid_kills(m)
        if result is not None:
            return result

    # Fallback: broader scoreboard region.
    crop = SCOREBOARD.crop(frame)
    text = _ocr_kills_text(crop, scale=3)
    m = _KILLS_RE.search(text)
    if m:
        return _valid_kills(m)

    return None


def detect_player_kda(frame: np.ndarray) -> PlayerKDA | None:
    """Extract player KDA (``K/D/A``) from a frame.

    Returns ``None`` if the pattern is not detected.
    """
    # Try focused KDA region.
    crop = PLAYER_KDA.crop(frame)
    text = _ocr_kills_text(crop, scale=4)
    m = _KDA_RE.search(text)
    if m:
        return PlayerKDA(
            kills=int(m.group(1)),
            deaths=int(m.group(2)),
            assists=int(m.group(3)),
        )

    # Fallback: broader scoreboard region.
    crop = SCOREBOARD.crop(frame)
    text = _ocr_kills_text(crop, scale=3)
    m = _KDA_RE.search(text)
    if m:
        return PlayerKDA(
            kills=int(m.group(1)),
            deaths=int(m.group(2)),
            assists=int(m.group(3)),
        )

    return None
