# CLAUDE.md

## Setup

```sh
apt-get update && apt-get install -y git-lfs tesseract-ocr ffmpeg
git lfs install && git lfs pull
uv sync
```

## Commands

```sh
uv run wr-analyzer videos/JjoDryfoCGs.mp4    # analyse local video
uv run wr-analyzer https://youtu.be/JjoDryfoCGs  # analyse YouTube video
uv run pytest                                  # 77 tests
uv run python tests/extract_fixtures.py        # regenerate test frame PNGs from video
```

All work using Python must be done via `uv` commands. You may not run `python3` or `python`
on its own.

## Module map

`src/wr_analyzer/`:

| Module | Role |
|---|---|
| `download.py` | YouTube download via yt-dlp (URL parsing, caching) |
| `video.py` | Frame extraction via ffmpeg |
| `ocr.py` | Tesseract OCR with adaptive and OTSU preprocessing |
| `regions.py` | HUD region definitions (corner-anchored pixel offsets, scaled by width) |
| `timer.py` | Game clock MM:SS detection |
| `kda.py` | Team kill scores and player KDA |
| `game_state.py` | Phase detection: loading / in_game / post_game |
| `result.py` | Win/loss detection from VICTORY/DEFEAT post-game screens |
| `champions.py` | Fuzzy match OCR text to glossary champion names |
| `analyze.py` | Orchestrator: sample frames → segment games → extract data |
| `models.py` | Dataclasses matching `docs/schema.json` |
| `__main__.py` | CLI entry point |
| `layout.py` | HUD layout validation (detects custom HUD layouts) |
