"""Kills/deaths/assists extraction from the in-game HUD."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from wr_analyzer.ocr import ocr_image, preprocess_otsu
from wr_analyzer.regions import KILLS, PLAYER_KDA, SCOREBOARD

# "# VS #" — V may OCR as V/v, S may OCR as 5/8/s.
_KILLS_RE = re.compile(r"(\d{1,3})\s*[Vv][Ss58]\s*(\d{1,3})")

# "K/D/A" or "K:D:A" — separator may OCR as /.:
_KDA_RE = re.compile(r"(\d{1,2})[/:.;](\d{1,2})[/:.;](\d{1,2})")


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


def detect_team_kills(frame: np.ndarray) -> TeamKills | None:
    """Extract team kill scores (``# VS #``) from a frame.

    Returns ``None`` if the pattern is not detected.
    """
    # Try focused kills region first.
    crop = KILLS.crop(frame)
    processed = preprocess_otsu(crop, scale=5)
    text = ocr_image(processed, psm=7)
    m = _KILLS_RE.search(text)
    if m:
        return TeamKills(blue=int(m.group(1)), red=int(m.group(2)))

    # Fallback: broader scoreboard region.
    crop = SCOREBOARD.crop(frame)
    processed = preprocess_otsu(crop, scale=5)
    text = ocr_image(processed, psm=6)
    m = _KILLS_RE.search(text)
    if m:
        return TeamKills(blue=int(m.group(1)), red=int(m.group(2)))

    return None


def detect_player_kda(frame: np.ndarray) -> PlayerKDA | None:
    """Extract player KDA (``K/D/A``) from a frame.

    Returns ``None`` if the pattern is not detected.
    """
    # Try focused KDA region.
    crop = PLAYER_KDA.crop(frame)
    processed = preprocess_otsu(crop, scale=5)
    text = ocr_image(processed, psm=7)
    m = _KDA_RE.search(text)
    if m:
        return PlayerKDA(
            kills=int(m.group(1)),
            deaths=int(m.group(2)),
            assists=int(m.group(3)),
        )

    # Fallback: broader scoreboard region.
    crop = SCOREBOARD.crop(frame)
    processed = preprocess_otsu(crop, scale=5)
    text = ocr_image(processed, psm=6)
    m = _KDA_RE.search(text)
    if m:
        return PlayerKDA(
            kills=int(m.group(1)),
            deaths=int(m.group(2)),
            assists=int(m.group(3)),
        )

    return None
