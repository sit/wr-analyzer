"""Shared test helpers (importable, not pytest fixtures)."""

from functools import cache
from pathlib import Path

import cv2
import numpy as np

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "frames"


@cache
def load_frame(ts: int) -> np.ndarray:
    """Load a pre-extracted test frame by timestamp (seconds).

    Frames live in tests/fixtures/frames/frame_t{ts}.png and are committed
    to the repository so tests never need to run ffmpeg.

    The result is cached in memory for the lifetime of the test session and
    marked read-only so a shared copy can't be silently mutated by one test
    and seen broken by another.
    """
    path = FIXTURES_DIR / f"frame_t{ts}.png"
    frame = cv2.imread(str(path))
    if frame is None:
        raise FileNotFoundError(f"Missing test frame fixture: {path}")
    frame.flags.writeable = False
    return frame
