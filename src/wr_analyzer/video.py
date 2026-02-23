"""Video loading and frame sampling.

Uses ffmpeg/ffprobe via subprocess for broad codec support (including AV1).
"""

from __future__ import annotations

import json
import subprocess
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
    """Read video metadata via *ffprobe*.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    RuntimeError
        If ffprobe fails to read the file.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    # Find the video stream.
    video_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_stream = stream
            break
    if video_stream is None:
        raise RuntimeError(f"No video stream found in {path}")

    # Parse frame rate (e.g. "30/1").
    r_num, r_den = video_stream["r_frame_rate"].split("/")
    fps = int(r_num) / int(r_den)

    return VideoInfo(
        width=int(video_stream["width"]),
        height=int(video_stream["height"]),
        fps=fps,
        duration=float(video_stream.get("duration", 0)),
    )


def extract_frame(path: Path | str, timestamp_sec: float) -> np.ndarray:
    """Extract a single frame at *timestamp_sec* seconds into the video.

    Returns an OpenCV BGR image (numpy array).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    RuntimeError
        If ffmpeg fails to decode the frame.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    info = probe(path)

    result = subprocess.run(
        [
            "ffmpeg",
            "-ss", str(timestamp_sec),
            "-i", str(path),
            "-frames:v", "1",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-v", "error",
            "pipe:1",
        ],
        capture_output=True,
        check=True,
    )

    expected_bytes = info.width * info.height * 3
    if len(result.stdout) != expected_bytes:
        raise RuntimeError(
            f"Expected {expected_bytes} bytes, got {len(result.stdout)} "
            f"(timestamp={timestamp_sec}s)"
        )

    frame = np.frombuffer(result.stdout, dtype=np.uint8)
    return frame.reshape((info.height, info.width, 3))


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
    info = probe(path)
    end = end_sec if end_sec is not None else info.duration

    ts = start_sec
    while ts < end:
        yield ts, extract_frame(path, ts)
        ts += interval_sec
