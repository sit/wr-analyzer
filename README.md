# WR Analyzer

Extracts structured game data from Wild Rift gameplay videos using OCR.

## What it does

Given a recorded Wild Rift game, the analyzer samples frames and extracts:

- **Game boundaries** — detects when a game starts and ends in the video
- **Game clock** — reads the in-game timer (MM:SS)
- **Team kill scores** — reads the "# VS #" HUD display
- **Player KDA** — reads kills/deaths/assists from the HUD
- **Champion names** — fuzzy-matches OCR text against known champion list

## Usage

```sh
# Human-readable report
uv run wr-analyzer videos/JjoDryfoCGs.mp4

# JSON output
uv run wr-analyzer videos/JjoDryfoCGs.mp4 --json

# Control sampling rate and range
uv run wr-analyzer videos/JjoDryfoCGs.mp4 --interval 10 --start 400 --end 2150
```

## Setup

Requires system packages `tesseract-ocr` and `ffmpeg`:

```sh
apt-get update && apt-get install -y tesseract-ocr ffmpeg
```

The sample video is stored with Git LFS:

```sh
apt-get install -y git-lfs
git lfs install
git lfs pull
```

Install Python dependencies:

```sh
uv sync
```

## Tests

```sh
uv run pytest
```

72 tests covering all modules. Tests that need the sample video skip gracefully if Git LFS hasn't been pulled.

## Limitations

- OCR accuracy is ~20–30% per frame at 854x394. The analyzer compensates by sampling many frames.
- Kill score OCR occasionally misreads digits (e.g. "25" → "75"). Timer readings are more reliable.
- Champion identification from in-game frames is not yet reliable.
- Calibrated against a single sample video. Region positions may need tuning for different recording setups.
