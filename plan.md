# WR Analyzer Prototype — Architecture Plan

## Package Structure

```
wr-analyzer/
├── pyproject.toml
├── src/
│   └── wr_analyzer/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       ├── models.py           # dataclasses matching schema.json
│       ├── video.py            # video loading, frame sampling
│       ├── ocr.py              # tesseract wrapper, region cropping
│       ├── regions.py          # screen region definitions (ROIs)
│       ├── timer.py            # game clock detection & parsing
│       ├── kda.py              # kills/deaths/assists extraction
│       ├── champions.py        # champion name identification
│       ├── game_state.py       # game start/end boundary detection
│       └── analyze.py          # orchestrator: ties modules together
├── tests/
│   ├── conftest.py
│   ├── test_video.py
│   ├── test_ocr.py
│   ├── test_regions.py
│   ├── test_models.py
│   ├── test_timer.py
│   ├── test_kda.py
│   ├── test_game_state.py
│   ├── test_champions.py
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
- `Region` dataclass with ratio-based coordinates (0.0–1.0)
- Predefined regions calibrated against 854×394 sample: `SCOREBOARD`, `GAME_TIMER`, `KILLS`, `PLAYER_KDA`, `MINIMAP`, `PLAYER_PORTRAIT`, `ABILITIES`, `GOLD`, `EVENT_FEED`

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
- Primary signal: timer OCR. Fallback: HUD brightness heuristic (kills region pixel analysis)

### `champions.py` ✅
- `fuzzy_match_champion(text)` → champion name or `None`
- `detect_champions(frame, region)` → list of matched names
- Uses rapidfuzz against ~180 champion names from glossary.md

### `analyze.py` ✅
- `analyze_video(path, interval_sec)` → `AnalysisResult`
- Samples frames, classifies phases, segments consecutive in-game frames into games
- Extracts timer, kill scores, and KDA per game

### `models.py` ✅
- `StreamAnalysis`, `Game`, `Champion`, `TimelineEvent`, `Runes`
- `StreamAnalysis.to_dict()` for JSON export matching schema.json

### `__main__.py` ✅
- CLI: `wr-analyzer <video> [--interval N] [--start N] [--end N] [--json]`

## Known Limitations

- OCR hits ~20–30% of frames at 854×394. Timer is the most reliable; kill scores sometimes misread digits.
- Regions are calibrated for one sample video. Different recording setups or resolutions may need tuning.
- The analyzer detects one game correctly in the sample video but has not been tested with multi-game VODs.

## Next Steps

High-value work not yet started:

1. **Post-game scoreboard parsing** — the victory/defeat screen contains all 10 players' names, champions, KDA, and gold in a structured layout. Easiest source of accurate game data.
2. **Win/loss detection** — detect "VICTORY"/"DEFEAT" text from the end-of-game banner.
3. **Champion identification from loading screen** — the loading screen shows all 10 champion splash arts and names.
4. **Timeline event extraction** — parse the kill feed (EVENT_FEED region) for individual kill/death events.
5. **OCR accuracy improvements** — higher resolution video, better preprocessing, or a lightweight ML model for digit recognition.

## Dependencies

- `opencv-python-headless` — frame extraction and image processing
- `pytesseract` — Tesseract OCR Python bindings
- `Pillow` — image format conversions
- `rapidfuzz` — fuzzy string matching for champion names

System deps: `tesseract-ocr`, `ffmpeg`

Dev deps: `pytest`, `pytest-cov`
