"""Tests for wr_analyzer.ocr."""

import cv2
import numpy as np

from wr_analyzer.ocr import (
    ocr_easyocr,
    preprocess_clahe,
)


def _make_text_image(text: str, width: int = 200, height: int = 60) -> np.ndarray:
    """Create a synthetic BGR image with white text on dark background."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(
        img,
        text,
        org=(10, height - 15),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1.2,
        color=(255, 255, 255),
        thickness=2,
    )
    return img


class TestPreprocessClahe:
    def test_output_is_bgr(self):
        bgr = np.zeros((20, 100, 3), dtype=np.uint8)
        result = preprocess_clahe(bgr, scale=2)
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_upscale(self):
        bgr = np.zeros((20, 100, 3), dtype=np.uint8)
        result = preprocess_clahe(bgr, scale=4)
        assert result.shape == (80, 400, 3)

    def test_preserves_colored_text(self):
        """CLAHE should boost contrast of colored text, not flatten it."""
        img = np.zeros((30, 100, 3), dtype=np.uint8)
        # Red text on dark background
        img[10:20, 20:40, 2] = 120  # red channel
        result = preprocess_clahe(img, scale=1)
        # The red region should be brighter after CLAHE
        assert result[10:20, 20:40, 2].mean() >= 120


class TestOcrEasyocr:
    def test_reads_white_text(self):
        img = _make_text_image("25 VS 29")
        scaled = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        texts = ocr_easyocr(scaled)
        joined = " ".join(texts)
        assert "25" in joined or "29" in joined

    def test_returns_list(self):
        img = np.zeros((50, 100, 3), dtype=np.uint8)
        result = ocr_easyocr(img)
        assert isinstance(result, list)
