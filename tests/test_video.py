"""Tests for wr_analyzer.video."""

import numpy as np
import pytest

from support import load_frame
from wr_analyzer.video import VideoInfo, extract_frame, probe, sample_frames


class TestProbe:
    def test_returns_video_info(self, sample_video_path):
        """Integration test: probe reads real metadata from the sample video."""
        info = probe(sample_video_path)
        assert isinstance(info, VideoInfo)
        assert info.width == 854
        assert info.height == 394
        assert info.fps == pytest.approx(30.0)
        assert info.duration > 0

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            probe(tmp_path / "nonexistent.mp4")


class TestExtractFrame:
    def test_returns_bgr_frame(self, sample_video_path):
        """Integration test: extract_frame decodes a real frame from video."""
        frame = extract_frame(sample_video_path, 30.0)
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (394, 854, 3)
        assert frame.dtype == np.uint8

    def test_different_timestamps_differ(self):
        """Frames at different timestamps should not be identical."""
        f1 = load_frame(700)
        f2 = load_frame(1800)
        assert not np.array_equal(f1, f2)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_frame(tmp_path / "missing.mp4", 0.0)


class TestSampleFrames:
    def test_yields_timestamp_frame_pairs(self, sample_video_path):
        frames = list(sample_frames(sample_video_path, interval_sec=30.0, end_sec=61.0))
        assert len(frames) == 3
        for ts, frame in frames:
            assert isinstance(ts, float)
            assert isinstance(frame, np.ndarray)
            assert frame.shape == (394, 854, 3)

    def test_start_end_range(self, sample_video_path):
        frames = list(
            sample_frames(
                sample_video_path, interval_sec=10.0, start_sec=100.0, end_sec=121.0
            )
        )
        timestamps = [ts for ts, _ in frames]
        assert timestamps[0] == pytest.approx(100.0)
        assert all(100.0 <= t <= 121.0 for t in timestamps)
