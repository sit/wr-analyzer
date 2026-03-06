"""CLI entry point: ``python -m wr_analyzer <video>``.

The *video* argument may be a local file path **or** a YouTube URL / video ID.
When a URL is given the video is downloaded (and cached) before analysis.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wr_analyzer.analyze import analyze_video
from wr_analyzer.download import download_video, extract_video_id


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="wr-analyzer",
        description="Analyse a Wild Rift gameplay video.",
    )
    parser.add_argument(
        "video",
        help="Path to a local video file, YouTube URL, or YouTube video ID",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=15.0,
        help="Seconds between sampled frames (default: 15)",
    )
    parser.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="Start timestamp in seconds (default: 0)",
    )
    parser.add_argument(
        "--end",
        type=float,
        default=None,
        help="End timestamp in seconds (default: video duration)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output raw JSON instead of the human-readable report",
    )
    parser.add_argument(
        "--cache-dir",
        default="videos/cache",
        help="Directory for downloaded videos (default: videos/cache)",
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=720,
        help="Download resolution in pixels (default: 720)",
    )

    args = parser.parse_args(argv)

    # Resolve video source: local path or YouTube download.
    video_path = Path(args.video)
    if not video_path.exists():
        video_id = extract_video_id(args.video)
        if video_id is None:
            parser.error(f"File not found and not a YouTube URL: {args.video}")
        video_path = download_video(
            video_id,
            Path(args.cache_dir),
            resolution=args.resolution,
            on_progress=lambda msg: print(msg, file=sys.stderr),
        )

    print(f"Analysing {video_path} (sampling every {args.interval}s) ...", file=sys.stderr)

    def _progress(idx: int, total: int, elapsed: float) -> None:
        print(f"\r  frame {idx}/{total} ({elapsed:.1f}s)", end="", file=sys.stderr, flush=True)

    result = analyze_video(
        video_path,
        interval_sec=args.interval,
        start_sec=args.start,
        end_sec=args.end,
        on_progress=_progress,
    )
    print(file=sys.stderr)  # newline after progress

    if args.output_json:
        print(json.dumps(result.summary(), indent=2))
        return

    # --- human-readable report ---
    info_line = f"Video:    {result.source}  ({result.duration_sec / 60:.1f} min)"
    print(info_line)
    print(f"Sampled:  {len(result.frame_data)} frames")

    # Phase breakdown
    from collections import Counter

    phases = Counter(f.phase for f in result.frame_data)
    phase_str = ", ".join(f"{p}: {n}" for p, n in phases.most_common())
    print(f"Phases:   {phase_str}")

    in_game = [f for f in result.frame_data if f.phase == "in_game"]
    if not in_game:
        print("\nNo in-game frames detected.")
        return

    print(f"\nIn-game frames: {len(in_game)}")
    print(f"Video span:     {in_game[0].timestamp_sec:.0f}s – {in_game[-1].timestamp_sec:.0f}s")

    # Timer readings
    timer_readings = [(f.timestamp_sec, f.game_time) for f in in_game if f.game_time]
    if timer_readings:
        print(f"\nGame clock ({len(timer_readings)} readings):")
        for ts, gt in timer_readings:
            print(f"  video {ts:>7.0f}s  →  {gt}")

    # Kill scores
    kill_readings = [(f.timestamp_sec, f.team_kills) for f in in_game if f.team_kills]
    if kill_readings:
        print(f"\nTeam kills ({len(kill_readings)} readings):")
        for ts, tk in kill_readings:
            print(f"  video {ts:>7.0f}s  →  Blue {tk.blue:>2d}  vs  Red {tk.red:>2d}")

    # KDA
    kda_readings = [(f.timestamp_sec, f.player_kda) for f in in_game if f.player_kda]
    if kda_readings:
        print(f"\nPlayer KDA ({len(kda_readings)} readings):")
        for ts, kda in kda_readings:
            print(f"  video {ts:>7.0f}s  →  {kda.kills}/{kda.deaths}/{kda.assists}")

    # Game segments
    if result.games:
        print(f"\nGames detected: {len(result.games)}")
        for i, g in enumerate(result.games, 1):
            dur = (g.end_sec - g.start_sec) / 60
            result_str = g.result.upper() if g.result else "unknown"
            print(f"\n  Game {i}  [{result_str}]  (video {g.start_sec:.0f}s – {g.end_sec:.0f}s, {dur:.1f} min span)")
            if g.first_game_time:
                print(f"    First clock: {g.first_game_time}")
            if g.last_game_time:
                print(f"    Last clock:  {g.last_game_time}")
            tk = g.final_team_kills
            if tk:
                print(f"    Final kills: Blue {tk.blue} vs Red {tk.red}")
            kda = g.final_player_kda
            if kda:
                print(f"    Final KDA:   {kda.kills}/{kda.deaths}/{kda.assists}")
    else:
        print("\nNo game segments detected (frames too sparse or short).")


if __name__ == "__main__":
    main()
