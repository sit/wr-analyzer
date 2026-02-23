"""Orchestrator: ties all analysis modules together.

Samples frames across a video, detects game boundaries, and extracts
timer / kill-score / KDA data for each detected game.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from wr_analyzer.game_state import detect_game_phase
from wr_analyzer.kda import PlayerKDA, TeamKills, detect_player_kda, detect_team_kills
from wr_analyzer.timer import detect_game_time
from wr_analyzer.video import extract_frame, probe


@dataclass
class FrameData:
    """Extracted data from a single frame."""

    timestamp_sec: float
    phase: str
    game_time: str | None = None
    team_kills: TeamKills | None = None
    player_kda: PlayerKDA | None = None


@dataclass
class GameSegment:
    """A contiguous stretch of in-game frames."""

    start_sec: float
    end_sec: float
    frames: list[FrameData] = field(default_factory=list)

    @property
    def first_game_time(self) -> str | None:
        for f in self.frames:
            if f.game_time is not None:
                return f.game_time
        return None

    @property
    def last_game_time(self) -> str | None:
        for f in reversed(self.frames):
            if f.game_time is not None:
                return f.game_time
        return None

    @property
    def final_team_kills(self) -> TeamKills | None:
        for f in reversed(self.frames):
            if f.team_kills is not None:
                return f.team_kills
        return None

    @property
    def final_player_kda(self) -> PlayerKDA | None:
        for f in reversed(self.frames):
            if f.player_kda is not None:
                return f.player_kda
        return None


@dataclass
class AnalysisResult:
    """Complete analysis output for a video."""

    source: str
    analysis_date: datetime
    duration_sec: float
    games: list[GameSegment] = field(default_factory=list)
    frame_data: list[FrameData] = field(default_factory=list)

    def summary(self) -> dict:
        """Return a human-readable summary dict."""
        games_out = []
        for i, g in enumerate(self.games, 1):
            entry: dict = {
                "game": i,
                "video_start_sec": g.start_sec,
                "video_end_sec": g.end_sec,
                "first_game_time": g.first_game_time,
                "last_game_time": g.last_game_time,
            }
            tk = g.final_team_kills
            if tk:
                entry["final_kills"] = {"blue": tk.blue, "red": tk.red}
            kda = g.final_player_kda
            if kda:
                entry["final_kda"] = {
                    "kills": kda.kills,
                    "deaths": kda.deaths,
                    "assists": kda.assists,
                }
            games_out.append(entry)

        return {
            "source": self.source,
            "analysis_date": self.analysis_date.isoformat(),
            "video_duration_sec": self.duration_sec,
            "games_detected": len(self.games),
            "games": games_out,
        }


def _segment_games(
    frames: list[FrameData],
    min_gap_sec: float = 30.0,
    min_duration_sec: float = 60.0,
) -> list[GameSegment]:
    """Group consecutive in-game frames into game segments.

    A new segment starts when the gap between consecutive in-game frames
    exceeds *min_gap_sec*.  Segments shorter than *min_duration_sec* are
    discarded (likely false positives).
    """
    in_game = [f for f in frames if f.phase == "in_game"]
    if not in_game:
        return []

    segments: list[GameSegment] = []
    current = GameSegment(start_sec=in_game[0].timestamp_sec, end_sec=in_game[0].timestamp_sec)
    current.frames.append(in_game[0])

    for f in in_game[1:]:
        if f.timestamp_sec - current.end_sec > min_gap_sec:
            segments.append(current)
            current = GameSegment(start_sec=f.timestamp_sec, end_sec=f.timestamp_sec)
        current.end_sec = f.timestamp_sec
        current.frames.append(f)

    segments.append(current)

    return [s for s in segments if (s.end_sec - s.start_sec) >= min_duration_sec]


def analyze_frame(frame: np.ndarray, timestamp_sec: float) -> FrameData:
    """Analyse a single frame and return extracted data."""
    phase = detect_game_phase(frame)

    game_time = None
    team_kills = None
    player_kda = None

    if phase == "in_game":
        game_time = detect_game_time(frame)
        team_kills = detect_team_kills(frame)
        player_kda = detect_player_kda(frame)

    return FrameData(
        timestamp_sec=timestamp_sec,
        phase=phase,
        game_time=game_time,
        team_kills=team_kills,
        player_kda=player_kda,
    )


def analyze_video(
    path: str | Path,
    interval_sec: float = 10.0,
    start_sec: float = 0.0,
    end_sec: float | None = None,
) -> AnalysisResult:
    """Analyse a Wild Rift gameplay video.

    Samples one frame every *interval_sec* seconds, detects game
    boundaries, and extracts HUD data for each game.

    Parameters
    ----------
    path : str | Path
        Path to the video file.
    interval_sec : float
        Seconds between sampled frames.
    start_sec : float
        Where to begin sampling.
    end_sec : float | None
        Where to stop (defaults to video duration).
    """
    path = Path(path)
    info = probe(path)
    stop = end_sec if end_sec is not None else info.duration

    all_frames: list[FrameData] = []
    ts = start_sec
    while ts < stop:
        frame = extract_frame(path, ts)
        fd = analyze_frame(frame, ts)
        all_frames.append(fd)
        ts += interval_sec

    # Scale gap threshold: OCR misses many frames at low resolution, so
    # allow gaps up to 5x the sampling interval before splitting segments.
    gap = max(30.0, interval_sec * 5)
    games = _segment_games(all_frames, min_gap_sec=gap)

    return AnalysisResult(
        source=str(path),
        analysis_date=datetime.now(),
        duration_sec=info.duration,
        games=games,
        frame_data=all_frames,
    )
