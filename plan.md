# WR Analyzer Prototype - Architecture Plan

## Package Structure

```
wr-analyzer/
├── pyproject.toml              # uv project config, dependencies
├── src/
│   └── wr_analyzer/
│       ├── __init__.py         # version, top-level imports
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
│   ├── conftest.py             # shared fixtures (sample frames, etc.)
│   ├── test_video.py
│   ├── test_ocr.py
│   ├── test_timer.py
│   ├── test_kda.py
│   └── test_game_state.py
├── videos/                     # LFS-tracked sample videos (already exists)
├── docs/                       # existing docs
├── CLAUDE.md
└── README.md
```

## Module Responsibilities

### `models.py`
Dataclasses that mirror the schema: `GameAnalysis`, `GameResult`, `Champion`, `TimelineEvent`. Plain dataclasses with `asdict()` for JSON export.

### `video.py`
- `FrameExtractor` class: opens video with OpenCV, provides:
  - `sample_frames(interval_sec)` → yields `(timestamp_sec, frame)` tuples
  - `get_frame(timestamp_sec)` → single frame at a timestamp
  - `fps`, `duration`, `resolution` properties
- Handles video lifecycle (open/close)

### `ocr.py`
- `ocr_region(frame, region) → str`: crops a frame to a Region, preprocesses (grayscale, threshold), runs Tesseract
- Preprocessing helpers: contrast boost, binarization — whatever helps Tesseract on the game UI

### `regions.py`
- Named `Region` dataclass: `(x, y, width, height)` as ratios (0.0–1.0) of frame size, so resolution-independent
- Predefined regions: `GAME_TIMER`, `BLUE_KDA`, `RED_KDA`, `BLUE_CHAMPIONS`, `RED_CHAMPIONS`, `MINIMAP`
- These will need tuning against real frames — start with best guesses from default layout

### `timer.py`
- `detect_game_time(frame) → Optional[str]`: extracts the game clock text (e.g., "12:34") from the timer region
- `parse_game_time(text) → Optional[int]`: parses to seconds

### `kda.py`
- `detect_kda(frame) → dict`: extracts team kill scores from the HUD

### `champions.py`
- `detect_champions(frame) → list[str]`: OCR champion names from scoreboard/loading screen
- Uses fuzzy matching against the known champion list from glossary.md

### `game_state.py`
- `detect_game_phase(frame) → str`: returns "loading", "in_game", "post_game", or "unknown"
- Uses heuristics: presence of game timer, loading screen patterns, end screen detection

### `analyze.py`
- `analyze_video(path) → GameAnalysis`: main entry point
  - Samples frames across the video
  - Detects game boundaries
  - Within each game, extracts timer/KDA/champions
  - Returns structured result

## Dependencies

- `opencv-python-headless` — frame extraction and image processing
- `pytesseract` — Tesseract OCR Python bindings
- `Pillow` — image format conversions
- `rapidfuzz` — fuzzy string matching for champion names

System deps: `tesseract-ocr`

Dev deps: `pytest`, `pytest-cov`

## Testing Strategy

- Unit tests per module using saved frame crops as fixtures
- `conftest.py` provides a helper to extract and cache specific frames from the sample video
- Tests can be run without the full video by using small cropped PNGs checked into `tests/fixtures/`

## Implementation Order

1. `models.py` + `regions.py` — data structures, no deps
2. `video.py` — frame extraction from sample video
3. `ocr.py` — get Tesseract working on cropped regions
4. `timer.py` — first concrete detector, validate against real frames
5. `game_state.py` — game boundary detection
6. `kda.py` — score extraction
7. `champions.py` — champion identification with fuzzy matching
8. `analyze.py` — wire it all together
9. Tests + docs updates throughout
