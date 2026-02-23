"""Shared test fixtures."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = REPO_ROOT / "videos"
SAMPLE_VIDEO = VIDEOS_DIR / "JjoDryfoCGs.mp4"


@pytest.fixture
def sample_video_path() -> Path:
    """Return path to the sample video, skipping if not available."""
    if not SAMPLE_VIDEO.exists():
        pytest.skip("Sample video not available (run git lfs pull)")
    return SAMPLE_VIDEO
