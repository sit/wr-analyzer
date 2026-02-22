"""Champion name identification via OCR and fuzzy matching."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from rapidfuzz import process as fuzz_process

from wr_analyzer.ocr import ocr_image, preprocess_otsu
from wr_analyzer.regions import Region

# Load the champion list once from the glossary.
_GLOSSARY_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "glossary.md"

_CHAMPIONS: list[str] = []


def _load_champions() -> list[str]:
    """Parse champion names from the glossary markdown."""
    global _CHAMPIONS  # noqa: PLW0603
    if _CHAMPIONS:
        return _CHAMPIONS

    if not _GLOSSARY_PATH.exists():
        return []

    text = _GLOSSARY_PATH.read_text()
    # Champions line follows "## Champions"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "," in stripped:
            # First non-heading, comma-separated line after the file start
            # is the champion list.
            _CHAMPIONS = [name.strip() for name in stripped.split(",") if name.strip()]
            break

    return _CHAMPIONS


def fuzzy_match_champion(text: str, score_cutoff: int = 65) -> str | None:
    """Match *text* to the closest known champion name.

    Returns ``None`` if no match meets the *score_cutoff*.
    """
    champions = _load_champions()
    if not champions or not text.strip():
        return None

    result = fuzz_process.extractOne(text.strip(), champions, score_cutoff=score_cutoff)
    if result is None:
        return None
    return result[0]


def detect_champions(frame: np.ndarray, region: Region) -> list[str]:
    """OCR a frame *region* and attempt to identify champion names.

    This is designed for scoreboard / loading-screen regions where
    champion names are listed as text.

    Returns a (possibly empty) list of matched champion names.
    """
    crop = region.crop(frame)
    processed = preprocess_otsu(crop, scale=4)
    raw_text = ocr_image(processed, psm=6)

    found: list[str] = []
    for word in raw_text.split("\n"):
        word = word.strip()
        if len(word) < 3:
            continue
        match = fuzzy_match_champion(word)
        if match and match not in found:
            found.append(match)
    return found
