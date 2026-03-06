"""Download YouTube videos for analysis.

Uses yt-dlp to fetch video files at a configurable resolution, caching
them locally so repeated runs don't re-download.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp
from yt_dlp.utils import download_range_func


def extract_video_id(url_or_id: str) -> str | None:
    """Extract a YouTube video ID from a URL, or return *None*.

    Accepts:
    - ``https://www.youtube.com/watch?v=ID``
    - ``https://youtu.be/ID``
    - ``https://youtube.com/watch?v=ID&t=123``
    - bare 11-char video IDs like ``JjoDryfoCGs``

    Returns *None* when *url_or_id* doesn't look like any of the above
    (e.g. a local file path).
    """
    parsed = urlparse(url_or_id)

    # Full youtube.com URL
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        ids = qs.get("v")
        if ids:
            return ids[0]
        return None

    # Shortened youtu.be URL
    if parsed.hostname == "youtu.be":
        vid = parsed.path.lstrip("/").split("/")[0]
        return vid if vid else None

    # No scheme — could be a bare video ID (11 alphanumeric + hyphen/underscore)
    if not parsed.scheme and re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id

    return None


def get_video_metadata(video_id: str) -> dict:
    """Fetch video metadata (title, channel, duration, etc.) without downloading.

    Raises ``RuntimeError`` on failure.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch metadata for {video_id}") from e

    return {
        "title": info.get("title", ""),
        "channel": info.get("uploader", ""),
        "upload_date": info.get("upload_date", ""),
        "timestamp": info.get("timestamp"),
        "duration": info.get("duration", 0),
        "description": info.get("description", ""),
    }


def download_video(
    video_id: str,
    output_dir: Path,
    *,
    start_time: float | None = None,
    end_time: float | None = None,
    resolution: int = 720,
    on_progress: Callable[[str], None] | None = None,
) -> Path:
    """Download a YouTube video and return the local file path.

    The file is cached at ``output_dir/{video_id}.mp4``.  If it already
    exists the download is skipped.

    Parameters
    ----------
    video_id:
        YouTube video ID (11-character string).
    output_dir:
        Directory to store downloaded files.
    start_time / end_time:
        Optional time range in seconds.
    resolution:
        Maximum video height in pixels (default 480).
    on_progress:
        Optional callback for status messages.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_id}.mp4"

    if output_path.exists():
        if on_progress:
            on_progress(f"Using cached video: {output_path}")
        return output_path

    if on_progress:
        on_progress(f"Downloading {video_id} ({resolution}p) ...")

    ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        # H.264 video-only at target resolution, ≤30fps — no audio needed
        # for analysis and high frame rates waste bandwidth/disk.
        "format": f"bestvideo[height<={resolution}][fps<=30][vcodec^=avc1]",
        "outtmpl": str(output_path),
        "no_playlist": True,
    }

    if start_time is not None or end_time is not None:
        ranges = [(start_time or 0, end_time or float("inf"))]
        ydl_opts["download_ranges"] = download_range_func(None, ranges)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    except Exception as e:
        # Clean up partial file on failure.
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(f"Download failed for {video_id}") from e

    if on_progress:
        on_progress(f"Downloaded to {output_path}")

    return output_path
