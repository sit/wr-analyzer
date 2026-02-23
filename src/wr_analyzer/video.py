"""Video loading and frame sampling.

Uses OpenCV (cv2.VideoCapture) for decoding.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

@dataclass(frozen=True)
class VideoInfo:
    """Basic metadata about a video file."""

    width: int
    height: int
    fps: float
    duration: float  # seconds


def probe(path: Path | str) -> VideoInfo:
    """Read video metadata via OpenCV.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    RuntimeError
        If cv2 fails to open the file.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    cap.release()

    duration = frame_count / fps if fps > 0 else 0.0

    return VideoInfo(
        width=width,
        height=height,
        fps=fps,
        duration=duration,
    )

def extract_frame(path: Path | str, timestamp_sec: float) -> np.ndarray:
    """Extract a single frame at *timestamp_sec* seconds into the video.

    Returns an OpenCV BGR image (numpy array).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    RuntimeError
        If cv2 fails to decode the frame.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")

    # Seek to the requested timestamp (in milliseconds)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000.0)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise RuntimeError(f"Failed to extract frame at timestamp={timestamp_sec}s")

    return frame


def sample_frames(
    path: Path | str,
    interval_sec: float = 1.0,
    start_sec: float = 0.0,
    end_sec: float | None = None,
) -> Iterator[tuple[float, np.ndarray]]:
    """Yield ``(timestamp_sec, frame)`` tuples at *interval_sec* intervals.

    Parameters
    ----------
    path : Path | str
        Video file path.
    interval_sec : float
        Seconds between sampled frames.
    start_sec : float
        Where to begin sampling.
    end_sec : float | None
        Where to stop (defaults to video duration).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0.0
        end = end_sec if end_sec is not None else duration

        ts = start_sec
        while ts < end:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            yield ts, frame
            ts += interval_sec
    finally:
        cap.release()
