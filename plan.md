# WR Analyzer Prototype — Architecture Plan

## Package Structure

```
wr-analyzer/
├── pyproject.toml
├── src/
│   └── wr_analyzer/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       ├── download.py          # YouTube download via yt-dlp
│       ├── models.py           # dataclasses matching schema.json
│       ├── video.py            # video loading, frame sampling
│       ├── ocr.py              # tesseract wrapper, region cropping
│       ├── regions.py          # screen region definitions (ROIs)
│       ├── timer.py            # game clock detection & parsing
│       ├── kda.py              # kills/deaths/assists extraction
│       ├── champions.py        # champion name identification
│       ├── game_state.py       # game start/end boundary detection
│       ├── result.py           # win/loss detection from post-game screens
│       └── analyze.py          # orchestrator: ties modules together
├── tests/
│   ├── conftest.py
│   ├── test_video.py
│   ├── test_download.py
│   ├── test_ocr.py
│   ├── test_regions.py
│   ├── test_models.py
│   ├── test_timer.py
│   ├── test_kda.py
│   ├── test_game_state.py
│   ├── test_champions.py
│   ├── test_result.py
│   └── test_analyze.py
├── videos/                     # LFS-tracked sample videos
├── docs/                       # vision, glossary, schema
├── CLAUDE.md
└── README.md
```

## Module Responsibilities

### `video.py` ✅
- `probe(path)` → `VideoInfo` (width, height, fps, duration)
- `extract_frame(path, timestamp_sec)` → BGR numpy array
- `sample_frames(path, interval_sec)` → iterator of `(timestamp, frame)` tuples

### `ocr.py` ✅
- `preprocess(image, scale)` → adaptive-threshold binary image
- `preprocess_otsu(image, scale)` → OTSU-threshold binary image (better for light-on-dark HUD text)
- `ocr_image(image, psm, whitelist)` → recognized text
- `ocr_region(frame, region)` → crop + preprocess + OCR in one call

### `regions.py` ✅
- `Region` dataclass with `Anchor` enum and pixel-based offsets from screen corners
- `Anchor`: TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, TOP_CENTER, BOTTOM_CENTER
- Pixel offsets calibrated at 854×394 reference, scaled by `frame_w / REF_WIDTH` at runtime
- Predefined regions: `SCOREBOARD`, `GAME_TIMER`, `KILLS`, `PLAYER_KDA`, `MINIMAP`, `PLAYER_PORTRAIT`, `ABILITIES`, `GOLD`, `EVENT_FEED`

### `timer.py` ✅
- `detect_game_time(frame)` → `"MM:SS"` or `None`
- `parse_game_time(text)` → seconds or `None`
- Tries focused timer region, falls back to broader scoreboard region

### `kda.py` ✅
- `detect_team_kills(frame)` → `TeamKills(blue, red)` or `None`
- `detect_player_kda(frame)` → `PlayerKDA(kills, deaths, assists)` or `None`
- Regex extraction tolerant of OCR noise (V/v, S/5/8, colon/period/slash separators)

### `game_state.py` ✅
- `detect_game_phase(frame)` → `"loading"` | `"in_game"` | `"post_game"` | `"unknown"`
- Primary signal: timer OCR. Fallback: VICTORY/DEFEAT OCR for post-game, then HUD brightness heuristic

### `result.py` ✅
- `detect_result(frame)` → `"victory"` | `"defeat"` | `None`
- OCR-based detection of VICTORY/DEFEAT text on post-game banner and scoreboard
- Tries two regions: centred banner (animated splash) and top-strip (scoreboard header)

### `champions.py` ✅
- `fuzzy_match_champion(text)` → champion name or `None`
- `detect_champions(frame, region)` → list of matched names
- Uses rapidfuzz against ~180 champion names from glossary.md

### `analyze.py` ✅
- `analyze_video(path, interval_sec)` → `AnalysisResult`
- Samples frames, classifies phases, segments consecutive in-game frames into games
- Extracts timer, kill scores, KDA, and win/loss result per game
- Attaches post-game frames to game segments for result extraction

### `models.py` ✅
- `StreamAnalysis`, `Game`, `Champion`, `TimelineEvent`, `Runes`
- `StreamAnalysis.to_dict()` for JSON export matching schema.json

### `download.py` ✅
- `extract_video_id(url_or_id)` → video ID or `None` (handles youtube.com, youtu.be, m.youtube.com, bare 11-char IDs)
- `get_video_metadata(video_id)` → dict (title, channel, duration, upload_date, etc.) via yt-dlp without downloading
- `download_video(video_id, output_dir, *, start_time, end_time, resolution, on_progress)` → local `Path`
- Caches downloads at `{output_dir}/{video_id}.mp4`; skips if already present
- H.264 video-only (no audio) at configurable resolution; cleans up partial files on failure

### `__main__.py` ✅
- CLI: `wr-analyzer <video|URL|ID> [--interval N] [--start N] [--end N] [--json] [--cache-dir DIR] [--resolution N]`
- Accepts local file paths, YouTube URLs, or bare video IDs
- Downloads and caches YouTube videos before analysis

## Known Limitations

- OCR hits ~20–30% of frames at 854×394. Timer is the most reliable; kill scores sometimes misread digits.
- **Region system now handles aspect ratio variation.** Regions use corner-anchored pixel offsets scaled by width. Tested on 854×394 (2.17:1) and 854×480 (16:9). Not yet tested on different widths (e.g. 1280, 1920) — scaling by width ratio is the hypothesis but unvalidated.
- Custom HUD layouts are not supported. `layout.py` provides a `validate_layout()` smoke test that warns when the default regions don't match the video's HUD placement.
- The analyzer detects one game correctly in the sample video but has not been tested with multi-game VODs.
- `models.py` dataclasses (`StreamAnalysis`, `Game`, `Champion`, etc.) are tested but not wired into the analysis pipeline. `analyze.py` defines its own parallel dataclasses (`FrameData`, `GameSegment`, `AnalysisResult`). These should be unified when post-game scoreboard parsing is added.

## Next Steps

1. ~~**Win/loss detection**~~ ✅ — `result.py` detects "VICTORY"/"DEFEAT" from post-game banner and scoreboard via OCR; integrated into `game_state.py` phase detection and `analyze.py` game segments.
2. ~~**YouTube download**~~ ✅ — `download.py` fetches videos via yt-dlp with caching, time-range support, and resolution control. CLI accepts URLs directly.
3. ~~**Region anchoring refactor**~~ ✅ — `regions.py` now uses corner-anchored pixel offsets with `Anchor` enum. HUD elements stay correctly located across aspect ratios. `layout.py` provides layout validation. Tested on 854×394 and 854×480 videos.
4. **Post-game scoreboard parsing** — the victory/defeat screen contains all 10 players' names, champions, KDA, and gold in a structured layout. Easiest source of accurate per-player game data. Wire results into `models.py`.
5. **Champion identification from loading screen** — the loading screen shows all 10 champion splash arts and names.
6. **Timeline event extraction** — parse the kill feed (EVENT_FEED region) for individual kill/death events.
7. **OCR accuracy improvements** — higher resolution video, better preprocessing, or a lightweight ML model for digit recognition.

## Dependencies

- `opencv-python-headless` — frame extraction and image processing
- `pytesseract` — Tesseract OCR Python bindings
- `Pillow` — image format conversions
- `rapidfuzz` — fuzzy string matching for champion names
- `yt-dlp` — YouTube video download and metadata

System deps: `tesseract-ocr`, `ffmpeg`

Dev deps: `pytest`, `pytest-cov`
