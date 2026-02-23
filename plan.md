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

## Future Consideration: Layout & Device Variability

Wild Rift is played on a wide range of phones and tablets with different aspect ratios (16:9, 18:9, 19.5:9, 20:9, etc.), and players can reposition and resize HUD elements (minimap corner, joystick, skill buttons, etc.). This means:

- The ratio-based `Region` definitions in `regions.py` that are calibrated to one device/recording will drift for others.
- This applies to **all** screens: in-game HUD, loading screen, post-game scoreboard — each may have a different layout per device.
- Before this becomes a multi-user tool, we will likely need a calibration step: either auto-detection of anchor points (minimap corner, joystick, scoreboard header) or a one-time user-guided calibration that records offsets for their specific device and HUD layout.
- Tests and golden frames should be tagged with the source device/aspect ratio so regressions are meaningful.

## Next Steps

High-value work not yet started:

1. **Win/loss detection + post-game scoreboard parsing** *(in progress — see plan below)*
2. **Champion identification from loading screen** — the loading screen shows all 10 champion splash arts and names.
3. **Timeline event extraction** — parse the kill feed (EVENT_FEED region) for individual kill/death events.
4. **OCR accuracy improvements** — higher resolution video, better preprocessing, or a lightweight ML model for digit recognition.

### Plan: Win/Loss Detection + Post-Game Scoreboard (Items 1 & 2)

These are tackled together because both data sources live on the same post-game screen.

#### New module: `postgame.py`

```
detect_result(frame) → "Win" | "Lose" | None
```
- OCR a center-top banner region (`POSTGAME_BANNER`) for the text "VICTORY" or "DEFEAT".
- Fallback: dominant hue in the banner region (green → Win, red/purple → Lose).
- Returns `None` if neither signal is confident.

```
parse_scoreboard(frame) → PostgameData | None
```
- Parses the full post-game stats table.
- Wild Rift's default layout stacks blue team (top) and red team (bottom) in a table with columns: player name, champion, KDA, gold, items.
- Returns a `PostgameData` dataclass containing `result`, `blue_team: list[PlayerRow]`, `red_team: list[PlayerRow]`.

```
@dataclass
class PlayerRow:
    player: str
    champion: str | None   # fuzzy-matched via champions.py
    kills: int | None
    deaths: int | None
    assists: int | None
    gold: int | None
```

#### New regions in `regions.py`

```python
POSTGAME_BANNER      # center-top strip — "VICTORY" / "DEFEAT" text
POSTGAME_BLUE_TEAM   # rows for the 5 blue-side players
POSTGAME_RED_TEAM    # rows for the 5 red-side players
```

Initial coordinates are best guesses; they need calibration against actual post-game frames from the sample video.  Extraction of individual player rows is done by subdividing the team region into 5 equal horizontal strips.

#### Changes to `game_state.py`

- `detect_game_phase` already returns `"post_game"` for bright frames.
- No changes needed here; `postgame.py` is called downstream by the orchestrator.

#### Changes to `analyze.py`

- `GameSegment` gains optional fields: `result: str | None` and `postgame_frame_ts: float | None`.
- After segmenting in-game frames, scan forward from each segment's `end_sec` for the first `"post_game"` frame (within a reasonable window, e.g. 120 s).
- If found, call `detect_result` and `parse_scoreboard` on that frame and attach results to the segment.
- `AnalysisResult.summary()` updated to include `result` and `scoreboard`.

#### Changes to `models.py`

- `Game.result` is already `Result` — just needs populating.
- `Champion` already has `name`, `player`; `role` will remain empty until role detection is added.
- `Game.champions` populated from `PostgameData.blue_team + red_team`.

#### New tests: `tests/test_postgame.py`

- `test_detect_result_victory` — synthetic bright-green frame → `"Win"`.
- `test_detect_result_defeat` — synthetic red frame → `"Lose"`.
- `test_detect_result_non_postgame` → `None`.
- `test_parse_scoreboard_*` — with a captured post-game frame from the sample video (skipped if LFS not pulled).

#### Calibration note

Region coordinates for the post-game screen cannot be finalized without inspecting actual post-game frames.  The first implementation step is to extract a post-game frame from the sample video, inspect it, and measure the banner and table positions before writing the OCR logic.

## Dependencies

- `opencv-python-headless` — frame extraction and image processing
- `pytesseract` — Tesseract OCR Python bindings
- `Pillow` — image format conversions
- `rapidfuzz` — fuzzy string matching for champion names

System deps: `tesseract-ocr`, `ffmpeg`

Dev deps: `pytest`, `pytest-cov`
