"""Tests for wr_analyzer.analyze."""

from support import load_frame
from wr_analyzer.analyze import (
    AnalysisResult,
    FrameData,
    GameSegment,
    _segment_games,
    _sanitize_kills,
    analyze_frame,
)
from wr_analyzer.kda import TeamKills


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

    def test_post_game_frames_attached(self):
        """Post-game frames following a segment should be attached."""
        game = [self._make_frame(t, "in_game") for t in range(0, 300, 10)]
        post = [FrameData(timestamp_sec=310, phase="post_game", result="victory")]
        segments = _segment_games(game + post, min_gap_sec=30, min_duration_sec=60)
        assert len(segments) == 1
        assert len(segments[0].post_game_frames) == 1
        assert segments[0].result == "victory"

    def test_post_game_not_attached_if_too_far(self):
        """Post-game frames beyond min_gap_sec should not be attached."""
        game = [self._make_frame(t, "in_game") for t in range(0, 300, 10)]
        post = [FrameData(timestamp_sec=400, phase="post_game", result="victory")]
        segments = _segment_games(game + post, min_gap_sec=30, min_duration_sec=60)
        assert len(segments) == 1
        assert len(segments[0].post_game_frames) == 0
        assert segments[0].result is None


class TestSanitizeKills:
    """Test monotonicity filtering of team kill readings."""

    def _make_frame(self, ts: float, blue: int, red: int) -> FrameData:
        return FrameData(
            timestamp_sec=ts, phase="in_game",
            team_kills=TeamKills(blue=blue, red=red),
        )

    def test_monotonic_series_unchanged(self):
        """A clean monotonic series should pass through unchanged."""
        frames = [
            self._make_frame(10, 0, 0),
            self._make_frame(20, 1, 1),
            self._make_frame(30, 3, 2),
        ]
        result = _sanitize_kills(frames)
        assert len(result) == 3

    def test_drops_decreasing_values(self):
        """Kill counts that decrease vs previous reading are OCR errors."""
        frames = [
            self._make_frame(10, 1, 1),
            self._make_frame(20, 3, 2),
            self._make_frame(30, 2, 5),  # blue decreased: OCR error
            self._make_frame(40, 4, 6),
        ]
        result = _sanitize_kills(frames)
        # Frame is kept but kills cleared to None
        assert len(result) == 4
        assert result[0].team_kills == TeamKills(1, 1)
        assert result[1].team_kills == TeamKills(3, 2)
        assert result[2].team_kills is None  # cleared
        assert result[3].team_kills == TeamKills(4, 6)

    def test_drops_spike_values(self):
        """A sudden spike followed by return to normal is OCR noise."""
        frames = [
            self._make_frame(10, 5, 3),
            self._make_frame(20, 5, 111),  # spike: OCR error
            self._make_frame(30, 6, 4),
        ]
        result = _sanitize_kills(frames)
        # The spike at t=20 should be removed (it would force t=30 to
        # be removed too if kept, since 4 < 111)
        kills = [f.team_kills for f in result]
        assert TeamKills(5, 111) not in kills

    def test_none_kills_preserved(self):
        """Frames without kill readings should pass through."""
        frames = [
            FrameData(timestamp_sec=10, phase="in_game"),
            self._make_frame(20, 1, 1),
        ]
        result = _sanitize_kills(frames)
        assert len(result) == 2
        assert result[0].team_kills is None


class TestAnalyzeFrame:
    def test_returns_frame_data(self):
        fd = analyze_frame(load_frame("in_game_06"), 700.0)
        assert isinstance(fd, FrameData)
        assert fd.timestamp_sec == 700.0
        assert fd.phase in {"loading", "in_game", "post_game", "unknown"}

    def test_post_game_frame_has_result(self):
        fd = analyze_frame(load_frame("postgame_victory_banner"), 2190.0)
        assert fd.phase == "post_game"
        assert fd.result == "victory"


class TestAnalyzeVideo:
    def test_basic_analysis(self, sample_analysis_result):
        """Integration test: run analysis on a short slice and verify structure."""
        result = sample_analysis_result
        assert isinstance(result, AnalysisResult)
        assert result.duration_sec > 0
        assert len(result.frame_data) > 0

    def test_summary_structure(self, sample_analysis_result):
        summary = sample_analysis_result.summary()
        assert "source" in summary
        assert "games_detected" in summary
        assert "games" in summary
        assert isinstance(summary["games"], list)
