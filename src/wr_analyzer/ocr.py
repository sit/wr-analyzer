"""OCR wrappers (EasyOCR) with preprocessing for game UI text."""

from __future__ import annotations

import cv2
import easyocr
import numpy as np

# Lazy-initialised EasyOCR reader (downloads models on first use).
_easyocr_reader: easyocr.Reader | None = None


def _get_easyocr_reader() -> easyocr.Reader:
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["en"], gpu=True, verbose=False)
    return _easyocr_reader


def preprocess_clahe(image: np.ndarray, scale: int = 4) -> np.ndarray:
    """Enhance a BGR crop using CLAHE on each channel, then upscale.

    CLAHE (Contrast-Limited Adaptive Histogram Equalisation) boosts local
    contrast in each colour channel independently.  This makes both
    blue-tinted *and* red-tinted HUD text visible — unlike grayscale
    conversion, which dims red text on dark backgrounds.

    Returns a BGR image (not binary) suitable for EasyOCR.
    """
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(2, 2))
    b, g, r = cv2.split(image)
    enhanced = cv2.merge([clahe.apply(b), clahe.apply(g), clahe.apply(r)])
    if scale > 1:
        enhanced = cv2.resize(
            enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
    return enhanced


def ocr_easyocr(image: np.ndarray) -> list[str]:
    """Run EasyOCR on a BGR image.

    Returns a list of detected text strings.
    """
    reader = _get_easyocr_reader()
    return reader.readtext(image, detail=0)
