"""Tests for wr_analyzer.analyze."""

from support import load_frame
from wr_analyzer.analyze import (
    AnalysisResult,
    FrameData,
    _segment_games,
    analyze_frame,
    analyze_video,
)


class TestSegmentGames:
    def _make_frame(self, ts: float, phase: str) -> FrameData:
        return FrameData(timestamp_sec=ts, phase=phase)

    def test_single_continuous_game(self):
        frames = [self._make_frame(t, "in_game") for t in range(0, 600, 10)]
        segments = _segment_games(frames)
        assert len(segments) == 1
        assert segments[0].start_sec == 0
        assert segments[0].end_sec == 590

    def test_two_games_with_gap(self):
        game1 = [self._make_frame(t, "in_game") for t in range(0, 300, 10)]
        gap = [self._make_frame(t, "loading") for t in range(300, 400, 10)]
        game2 = [self._make_frame(t, "in_game") for t in range(400, 700, 10)]
        frames = game1 + gap + game2
        segments = _segment_games(frames, min_gap_sec=30, min_duration_sec=60)
        assert len(segments) == 2

    def test_short_segment_filtered(self):
        """Segments shorter than min_duration_sec should be discarded."""
        frames = [self._make_frame(t, "in_game") for t in range(0, 30, 10)]
        segments = _segment_games(frames, min_duration_sec=60)
        assert len(segments) == 0

    def test_no_in_game_frames(self):
        frames = [self._make_frame(t, "loading") for t in range(0, 300, 10)]
        segments = _segment_games(frames)
        assert len(segments) == 0


class TestAnalyzeFrame:
    def test_returns_frame_data(self):
        fd = analyze_frame(load_frame(700), 700.0)
        assert isinstance(fd, FrameData)
        assert fd.timestamp_sec == 700.0
        assert fd.phase in {"loading", "in_game", "post_game", "unknown"}


class TestAnalyzeVideo:
    def test_basic_analysis(self, sample_video_path):
        """Integration test: run analysis on a short slice and verify structure."""
        result = analyze_video(
            sample_video_path,
            interval_sec=30.0,
            start_sec=600.0,
            end_sec=720.0,
        )
        assert isinstance(result, AnalysisResult)
        assert result.source == str(sample_video_path)
        assert result.duration_sec > 0
        assert len(result.frame_data) > 0

    def test_summary_structure(self, sample_video_path):
        result = analyze_video(
            sample_video_path,
            interval_sec=60.0,
            start_sec=600.0,
            end_sec=720.0,
        )
        summary = result.summary()
        assert "source" in summary
        assert "games_detected" in summary
        assert "games" in summary
        assert isinstance(summary["games"], list)
