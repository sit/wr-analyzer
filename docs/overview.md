# Wild Rift Gameplay Analyzer

This is a tool to analyze video streams of Wild Rift game play,
allowing a player to study the game play of others or review
their own game play.

Wild Rift is a mobile game and as such there is a lot of visual structure in
the video stream: player avatars, a map with player icons, records of gold,
kills/deaths/assists, virtual buttons, and more. Players may also activate modals
to purchase items, or view game statistics. Players may customize the layout of
their UI but most players make only minor variations on the default layout.

A game is normally between 15 and 25 minutes in length and typically played at 60fps
on a phone or tablet device.

The analyzer will produce a structured data file that provides
- Stream metadata:
    - filename / URL / source
    - start and end time of each game in the stream
- For each game in the stream
    - Game metadata
        - game result (e.g., did the player win or lose)
        - list of champions in the match, their runes and their builds
    - Game timeline of events including:
        - All champion deaths
        - Call out of the player's kills, assists and deaths
        - Objective completions such as turret takedowns or neutral objectives
    - A complete summary of player's inputs, associated against a timeline
        - all abilities, auto-attacks, summoner spells
        - pings (optional)
        - movement (optional)
        - camera panning (optional)

Future features may allow for:
- intermediate gameplay analysis such as percentage of game time the player is dead, idle,
- more advanced analysis of gameplay, such as tempo, wave state, jungle camp status, jungle invasions,
  player pathing, fight positioning, etc.

## Key Components

### Video Preprocessing

- Frame Extraction: Extract frames at key intervals or detect scene changes (cuts/edits by the video editor,
  panning the camera, activating modals such as scoreboard, item shop, champ select or end of game stats, lobby)
- Resolution Normalization: Ensure consistent resolution across frames for reliable analysis.
- Frame Deduplication: Skip redundant frames during non-action moments to save processing power.

### Object and Text Detection

- Object Detection Models: Detect champions, map elements, items, and UI elements using models fine-tuned for the Wild Rift interface
- Use region-based detection to isolate UI panels like the scoreboard or item shop.
- OCR for Text Data: Extract player stats (gold, kills, deaths) and timestamps using OCR tools like Tesseract

### Timeline and Event Detection

- Define visual and textual markers for:
    - Match Start/End: Detect the loading screen or game timer resetting to 0.
    - Kills/Assists/Deaths: Recognize kill notifications, icons, or scoreboard updates.
    - Objectives: Use map state changes or textual cues (e.g., “Turret Destroyed”).
- Define visual markers for player inputs:
    - ability activations
    - map scrolling
- Implement temporal logic to align events with timestamps and group related sequences.

### Data output / storage

Aggregate and structure extracted data into JSON. See schema.json for a proposed schema.
YAML or TOML should be considered as an easier to generate and read for human format though.

A database of games, allowing for analysis.

## Development notes

Portability and flexibility is a key goal of the project.

Software development will be done on a MacBook Pro (M1Pro). It should be possible to
run much of the core logic on the laptop, and take advantage of M1Pro hardware
for acceleration as much as possible. Development may also take place on sandboxed Linux VMs.

If specially trained models might be helpful (e.g., finetuned multimodal models or
even more traditional models), it should be ideally runnable on Apple Silicon and then
using GPUs accessible through cloud providers such as GCP, AWS or Cloudflare etc.

Future work may include:
- packaging functionality into a webapp that allows a user to point to a
  YT or Twitch stream or upload a VOD.
- An iOS or Android client app would be a scaled down version that could either
  provide whatever analysis can be performed locally alone, or connect to a
  cloud version that can provide more horsepower for analysis and also an
  environment for reviewing and collecting multiple games.

The implementation should be able to share as much as possible (any training models, etc)
between these different hosting/execution modes. However, we should NOT build ahead.

We should aim to have unit tests as appropriate, golden data sets with evals to ensure any
ML or LLM work is accurate. It is reasonable for an LLM to ask a human to annotate certain
frames to assist in accurately determine what to do.

## Related Work

https://github.com/PepeTapia/WildAI

