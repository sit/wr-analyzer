"""Tests for wr_analyzer.ocr."""

import cv2
import numpy as np

from wr_analyzer.ocr import ocr_image, ocr_region, preprocess
from wr_analyzer.regions import Region


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


class TestPreprocess:
    def test_output_is_single_channel(self):
        bgr = np.zeros((50, 100, 3), dtype=np.uint8)
        result = preprocess(bgr)
        assert result.ndim == 2

    def test_upscale(self):
        bgr = np.zeros((50, 100, 3), dtype=np.uint8)
        result = preprocess(bgr, scale=4)
        assert result.shape == (200, 400)

class TestOcrImage:
    def test_reads_digits(self):
        img = _make_text_image("12345")
        processed = preprocess(img, scale=3)
        text = ocr_image(processed, whitelist="0123456789")
        # Allow some OCR fuzziness but core digits should be present
        digits = "".join(c for c in text if c.isdigit())
        assert len(digits) >= 3

    def test_reads_letters(self):
        img = _make_text_image("HELLO")
        processed = preprocess(img, scale=3)
        text = ocr_image(processed, whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        assert any(c in text.upper() for c in "HELO")


class TestOcrRegion:
    def test_end_to_end(self):
        # Create a small image with known text and OCR the whole thing
        # via ocr_region with a full-frame region.
        img = _make_text_image("42", width=200, height=60)
        # Embed into a slightly larger frame so the region crop is meaningful.
        frame = np.zeros((120, 400, 3), dtype=np.uint8)
        frame[30:90, 100:300] = img
        region = Region(x=0.25, y=0.25, w=0.50, h=0.50)
        text = ocr_region(frame, region, whitelist="0123456789")
        digits = "".join(c for c in text if c.isdigit())
        assert "4" in digits or "2" in digits
