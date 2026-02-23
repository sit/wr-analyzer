#!/usr/bin/env python
"""Regenerate test fixture frames from the sample video.

Usage:
    uv run python tests/extract_fixtures.py [VIDEO]

Extracts one frame per entry in FRAME_DEFS and writes it to
tests/fixtures/frames/{name}.png.  Requires ffmpeg.

The default video is videos/JjoDryfoCGs.mp4 (Git LFS).
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2

# -- canonical mapping: (descriptive name, timestamp in seconds) ----------
# This is the single source of truth for which frames exist as fixtures.
# If you add, remove, or rename a fixture, update this list and re-run
# the script.  Tests import FRAME_DEFS from here via support.py.
FRAME_DEFS: list[tuple[str, float]] = [
    ("champ_select",                 300),
    ("in_game_01",                    60),
    ("in_game_02",                   600),
    ("in_game_03",                   630),
    ("in_game_04",                   660),
    ("in_game_05",                   690),
    ("in_game_06",                   700),
    ("in_game_07",                   900),
    ("in_game_08",                  1200),
    ("in_game_09",                  1500),
    ("in_game_10",                  1800),
    ("in_game_11",                  2000),
    ("postgame_victory_banner",     2190),
    ("postgame_victory_scoreboard", 2205),
]

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "frames"
DEFAULT_VIDEO = REPO_ROOT / "videos" / "JjoDryfoCGs.mp4"


def main() -> None:
    video = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VIDEO
    if not video.exists():
        sys.exit(f"Video not found: {video}\nRun `git lfs pull` first.")

    # Import here so the module-level FRAME_DEFS is importable without
    # triggering video extraction.
    from wr_analyzer.video import extract_frame

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    for name, ts in FRAME_DEFS:
        out = FIXTURES_DIR / f"{name}.png"
        frame = extract_frame(video, ts)
        cv2.imwrite(str(out), frame)
        print(f"  {out.name}  (t={ts}s)")

    print(f"\nExtracted {len(FRAME_DEFS)} frames to {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
