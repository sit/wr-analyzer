"""Shared test helpers (importable, not pytest fixtures)."""

from pathlib import Path

import cv2
import numpy as np

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "frames"


def load_frame(ts: int) -> np.ndarray:
    """Load a pre-extracted test frame by timestamp (seconds).

    Frames live in tests/fixtures/frames/frame_t{ts}.png and are committed
    to the repository so tests never need to run ffmpeg.
    """
    path = FIXTURES_DIR / f"frame_t{ts}.png"
    frame = cv2.imread(str(path))
    if frame is None:
        raise FileNotFoundError(f"Missing test frame fixture: {path}")
    return frame
