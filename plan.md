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
│       ├── ocr.py              # EasyOCR with CLAHE preprocessing
│       ├── regions.py          # screen region definitions (ROIs)
│       ├── timer.py            # game clock detection & parsing
│       ├── kda.py              # kills/deaths/assists extraction
│       ├── champions.py        # champion name identification
│       ├── game_state.py       # game start/end boundary detection
│       ├── result.py           # win/loss detection from post-game screens
│       ├── layout.py           # HUD layout validation
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
├── _cache/                     # Downloaded videos (gitignored)
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
- `preprocess_clahe(image, scale)` — CLAHE on each BGR channel + upscale
- `ocr_easyocr(image)` — thin wrapper around lazy-initialised EasyOCR reader
- GPU auto-detection: uses CUDA > MPS > CPU via EasyOCR's built-in fallback

### `regions.py` ✅
- `Region` dataclass with `Anchor` enum and pixel-based offsets from screen corners
- `Anchor`: TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, TOP_CENTER, BOTTOM_CENTER
- Pixel offsets calibrated at 854×394 reference, scaled by `frame_w / REF_WIDTH` at runtime
- Predefined regions: `SCOREBOARD`, `GAME_TIMER`, `KILLS`, `PLAYER_KDA`, `MINIMAP`, `PLAYER_PORTRAIT`, `ABILITIES`, `GOLD`, `EVENT_FEED`

### `timer.py` ✅
- `detect_game_time(frame)` → `"MM:SS"` or `None`
- `parse_game_time(text)` → seconds or `None`
- Tries focused timer region at scales 5/4/3, falls back to broader scoreboard region

### `kda.py` ✅
- `detect_team_kills(frame)` → `TeamKills(blue, red)` or `None`
- `detect_player_kda(frame)` → `PlayerKDA(kills, deaths, assists)` or `None`
- Regex extraction tolerant of OCR noise (V/v/Y/y, S/5/8, colon/period/slash/comma separators)

### `game_state.py` ✅
- `detect_game_phase(frame)` → `"loading"` | `"in_game"` | `"post_game"` | `"unknown"`
- Primary signal: timer OCR. Fallback: VICTORY/DEFEAT OCR for post-game, then HUD brightness heuristic

### `result.py` ✅
- `detect_result(frame)` → `"victory"` | `"defeat"` | `None`
- CLAHE + EasyOCR detection of VICTORY/DEFEAT text on post-game banner and scoreboard

### `champions.py` ✅
- `fuzzy_match_champion(text)` → champion name or `None`
- `detect_champions(frame, region)` → list of matched names
- Uses rapidfuzz against ~180 champion names from glossary.md

### `analyze.py` ✅
- `analyze_video(path, interval_sec, on_progress)` → `AnalysisResult`
- Eagerly initialises EasyOCR reader before frame loop
- Per-frame progress callback with timing
- `_sanitize_kills()` monotonicity filter removes implausible readings
- Samples frames, classifies phases, segments into games, extracts data

### `models.py` ✅
- `StreamAnalysis`, `Game`, `Champion`, `TimelineEvent`, `Runes`
- `StreamAnalysis.to_dict()` for JSON export matching schema.json

### `download.py` ✅
- `extract_video_id(url_or_id)` → video ID or `None`
- `download_video(video_id, output_dir, *, resolution, on_progress)` → local `Path`
- Defaults to 720p, ≤30fps, H.264 video-only; caches at `{output_dir}/{video_id}.mp4`

### `__main__.py` ✅
- CLI: `wr-analyzer <video|URL|ID> [--interval N] [--start N] [--end N] [--json] [--cache-dir DIR] [--resolution N]`
- Per-frame progress output on stderr

## Ground Truth (JjoDryfoCGs.mp4 at 720p, 1280×590)

Final score: Blue 38 VS Red 34 (victory).

| Frame | Video ts | Game timer | Blue | Red | KDA |
|---|---|---|---|---|---|
| in_game_01 | 60s | — | — | — | No HUD (pre-game) |
| in_game_02 | 600s | 02:35 | 1 | 1 | 1/0/0 |
| in_game_03 | 630s | 03:05 | 2 | 2 | 1/0/1 |
| in_game_04 | 660s | 03:35 | 2 | 2 | 1/0/1 |
| in_game_05 | 690s | 04:05 | 2 | 2 | 1/0/1 |
| in_game_06 | 700s | 04:15 | 2 | 4 | 1/0/1 |
| in_game_07 | 900s | 07:55 | 3 | 5 | 1/0/2 |
| in_game_08 | 1200s | 12:35 | 7 | 14 | 1/0/5 |
| in_game_09 | 1500s | 17:35 | 15 | 20 | 2/0/12 |
| in_game_10 | 1800s | 22:35 | 25 | 29 | 3/2/18 |
| in_game_11 | 2000s | 25:55 | 31 | 32 | 4/2/21 |

## Completed: Replace Tesseract with EasyOCR ✅

### What was done

**RED phase** — wrote failing tests against ground truth:
- `test_kda.py`: exact assertions for in_game_06 (2v4), 07 (3v5), 09 (15v20), 10 (25v29)
- `test_timer.py`: exact assertions for in_game_03 (3:05), 06 (4:15), 09 (17:35)
- `test_ocr.py`: tests for `preprocess_clahe` and `ocr_easyocr`

**GREEN phase** — switched kda.py and timer.py to CLAHE + EasyOCR:
- All ground truth kills tests pass
- Timer passes 3/4 (in_game_07 "7:55" misread as "7:35" — inherent OCR ambiguity)

**REFACTOR phase** — removed Tesseract entirely:
- Migrated result.py and champions.py to CLAHE + EasyOCR
- Removed `preprocess`, `preprocess_otsu`, `ocr_image`, `ocr_region` from ocr.py
- Removed `pytesseract` and `Pillow` from dependencies
- Removed `tesseract-ocr` from system deps in CLAUDE.md
- 122 tests pass

### Other improvements made
- KILLS region height reduced from h=23 to h=14 (prevents timer bleed)
- `_KILLS_RE` limited to `\d{1,2}` (no 3-digit garbage)
- `MAX_TEAM_KILLS = 60` sanity bound
- `_sanitize_kills()` monotonicity filter in analyze.py
- Download default bumped to 720p, capped at 30fps
- Test fixtures re-extracted from 720p video (1280×590)
- Eager EasyOCR model load before frame loop (amortize startup)
- Per-frame progress callback with timing
- `gpu=True` — auto-detects CUDA/MPS/CPU

## Performance Profile

After EasyOCR warmup (~3.7s for import + model load), per-frame breakdown:

| Step | Time | Notes |
|---|---|---|
| `extract_frame` | 0.05s | cv2 seek + decode |
| `detect_game_phase` | 0.23s | |
| `detect_game_time` | 0.19s | Tries 3 scales, short-circuits on match |
| `detect_team_kills` | 0.43s | Focused crop + scoreboard fallback |
| `detect_player_kda` | 0.40s | Focused crop + scoreboard fallback |
| **Total per frame** | **~1.3s** | ~148 frames for 37min video at 15s interval |

Each `readtext` call is only ~0.07s. Most overhead is in CLAHE + resize preprocessing
and the CRAFT text detection stage (which is redundant since we already know where text is).

## Next Steps: Performance

1. **Skip CRAFT text detection** — use EasyOCR's `recognize()` to run just the CRNN
   recognition stage on pre-cropped regions, bypassing text detection entirely.
2. **Stop upscaling for EasyOCR** — the neural net resizes to its own input dimensions
   internally. The scale=4 upscale was needed for Tesseract, not for a learned model.
3. **OCR the scoreboard once per frame** — currently timer, kills, and KDA each independently
   OCR the scoreboard fallback region. OCR it once and share the text.
4. **Batch crops** — collect all per-frame crops and run recognition in one call.

## Next Steps: Features

1. **Post-game scoreboard parsing** — the victory/defeat screen contains all 10 players'
   names, champions, KDA, and gold in a structured layout.
2. **Champion identification from loading screen**
3. **Timeline event extraction** — parse the kill feed for individual kill/death events.
4. **Unify data models** — `analyze.py` defines its own `FrameData`/`GameSegment`/`AnalysisResult`
   parallel to `models.py` `StreamAnalysis`/`Game`/`Champion`. These should be consolidated.

## Known Limitations

- **OCR accuracy is the main bottleneck.** EasyOCR with CLAHE is much better than Tesseract
  for colored game HUD text, but still misreads digits at small sizes (e.g. "5" as "3").
- **Region system handles aspect ratio variation.** Tested on 854×394, 854×480, 1280×590.
- KILLS region (h=14 ref pixels) avoids overlapping the GAME_TIMER region below it.
- Custom HUD layouts not supported; `layout.py` provides a validation smoke test.
- Multi-game VODs not tested beyond single-game sample video.
- `models.py` dataclasses not wired into analysis pipeline yet.

## Dependencies

- `opencv-python-headless` — frame extraction and image processing
- `easyocr` — scene text recognition (CRAFT detection + CRNN recognition)
- `rapidfuzz` — fuzzy string matching for champion names
- `yt-dlp` — YouTube video download and metadata

System deps: `ffmpeg`

Dev deps: `pytest`, `pytest-cov`
