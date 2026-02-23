"""Shared test fixtures."""

from pathlib import Path

import pytest

from wr_analyzer.analyze import AnalysisResult, analyze_video

REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = REPO_ROOT / "videos"
SAMPLE_VIDEO = VIDEOS_DIR / "JjoDryfoCGs.mp4"


@pytest.fixture
def sample_video_path() -> Path:
    """Return path to the sample video, skipping if not available."""
    if not SAMPLE_VIDEO.exists() or SAMPLE_VIDEO.stat().st_size < 1_000_000:
        pytest.skip("Sample video not available (run git lfs pull)")
    return SAMPLE_VIDEO


@pytest.fixture(scope="session")
def sample_analysis_result() -> AnalysisResult:
    """Run analyze_video once for the whole session and share the result.

    Skipped when the sample video is absent (CI without LFS).
    """
    if not SAMPLE_VIDEO.exists() or SAMPLE_VIDEO.stat().st_size < 1_000_000:
        pytest.skip("Sample video not available (run git lfs pull)")
    return analyze_video(SAMPLE_VIDEO, interval_sec=30.0, start_sec=600.0, end_sec=720.0)
