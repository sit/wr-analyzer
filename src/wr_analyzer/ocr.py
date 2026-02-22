"""Tesseract OCR wrapper with preprocessing for game UI text."""

from __future__ import annotations

import cv2
import numpy as np
import pytesseract
from PIL import Image

from wr_analyzer.regions import Region


def preprocess(image: np.ndarray, scale: int = 3) -> np.ndarray:
    """Prepare a BGR crop for OCR: grayscale → resize → adaptive threshold.

    Best for text on varying-brightness backgrounds (e.g. synthetic test
    images).  For light text on dark game-UI backgrounds, prefer
    :func:`preprocess_otsu`.

    Parameters
    ----------
    image : np.ndarray
        BGR image (OpenCV format).
    scale : int
        Upscale factor before thresholding.  Larger values help Tesseract
        on tiny game-UI text.

    Returns
    -------
    np.ndarray
        Binary (white text on black) single-channel image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Upscale so small text is easier for Tesseract.
    if scale > 1:
        gray = cv2.resize(
            gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )

    # Adaptive threshold handles varying background brightness in the HUD.
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    return binary


def preprocess_otsu(image: np.ndarray, scale: int = 5) -> np.ndarray:
    """Prepare a BGR crop for OCR using OTSU thresholding.

    Better than adaptive threshold for the Wild Rift in-game HUD where
    light text (white / blue / red) sits on a dark semi-transparent
    background.

    Parameters
    ----------
    image : np.ndarray
        BGR image (OpenCV format).
    scale : int
        Upscale factor before thresholding.

    Returns
    -------
    np.ndarray
        Binary single-channel image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if scale > 1:
        gray = cv2.resize(
            gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def ocr_image(
    image: np.ndarray,
    *,
    psm: int = 7,
    whitelist: str = "",
) -> str:
    """Run Tesseract on a preprocessed (or raw) image.

    Parameters
    ----------
    image : np.ndarray
        Grayscale or BGR image.
    psm : int
        Tesseract page-segmentation mode.  Default ``7`` (single line).
    whitelist : str
        If non-empty, restrict Tesseract to these characters.

    Returns
    -------
    str
        Recognised text, stripped of surrounding whitespace.
    """
    config_parts = [f"--psm {psm}"]
    if whitelist:
        config_parts.append(f"-c tessedit_char_whitelist={whitelist}")
    config = " ".join(config_parts)

    pil_image = Image.fromarray(image)
    text: str = pytesseract.image_to_string(pil_image, config=config)
    return text.strip()


def ocr_region(
    frame: np.ndarray,
    region: Region,
    *,
    psm: int = 7,
    whitelist: str = "",
    scale: int = 3,
) -> str:
    """Crop *frame* to *region*, preprocess, and OCR.

    This is the main convenience function: give it a full frame and a
    ``Region`` and it returns the recognised text.
    """
    crop = region.crop(frame)
    processed = preprocess(crop, scale=scale)
    return ocr_image(processed, psm=psm, whitelist=whitelist)
