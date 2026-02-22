# Wild Rift Gameplay Analyzer

This is a tool to analyze video streams of Wild Rift game play,
allowing a player to study the game play of others or review
their own game play.

Wild Rift is a mobile game and as such there is a lot of visual structure in
the video stream: player avatars, a map with player icons, records of gold,
kills, virtual buttons, etc. Players may also view special screens to purchase
items, or view game statistics. These screens also have visual structure we can
rely on. A game is normally between 15 and 25 minutes in length and
typically played at 60fps on a phone or tablet device such as an iPad.

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

Wild Rift Analyzer is a web application that will have a freemium model. People can submit
YouTube or Twitch URLs of game play, and the application will analyze them. The free mode
will extract only rudimentary data to give a sense of the capability (e.g., find the first
player kill). Paying members will be able to get in-depth metadata of their games.

Future features may allow for:
- intermediate gameplay analysis such as percentage of game time the player is dead, idle, 
- more advanced analysis of gameplay, such as tempo, wave state, jungle camp status, jungle invasions,
  player pathing, fight positioning, etc.
- a game catalog where users can identify other games with similar situations for study
- a mobile app add-on that can record/stream video and assist in performing some or all
  analysis locally, and then uploading metadata to the site for these other functions.

## Key Components

### Video Preprocessing

- Frame Extraction: Use a library like FFmpeg to extract frames at key intervals or detect scene changes (e.g., transitioning to match summary screens).
- Resolution Normalization: Ensure consistent resolution across frames for reliable analysis.
Frame Deduplication: Skip redundant frames during non-action moments to save processing power.

### Object and Text Detection

- Object Detection Models: Detect champions, map elements, items, and UI elements using models fine-tuned for the Wild Rift interface (e.g., YOLOv8 or Detectron2).
- Use region-based detection to isolate UI panels like the scoreboard or item shop.
- OCR for Text Data: Extract player stats (gold, kills, deaths) and timestamps using OCR tools like Tesseract or EasyOCR, combined with text-region detection models for game-specific fonts.

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

Aggregate and structure extracted data into JSON. See below for a full schema description.

A database of games, allowing for analysis.

## Deployment Modes

Portability and flexibility is a key goal of the project.

Software development will be done on a MacBook Pro (M1Pro). It should be possible to
run much of the core logic on the laptop, and take advantage of M1Pro hardware
for acceleration as much as possible.

A web app would run in some sort of cloud environment (e.g., AWS or GCP).

An iOS or Android client app would be a scaled down version that could either
provide whatever analysis can be performed locally alone, or connect to a cloud
version that can provide more horsepower for analysis and also an environment
for reviewing and collecting multiple games.

The implementation should be able to share as much as possible (any training models, etc)
between these different hosting/execution modes.

## Development Milestones

1. Local prototyping.
2. Webapp

## Related Work

https://github.com/PepeTapia/WildAI

