# CLAUDE.md

## Setup

This repo uses Git LFS to store video files (*.mp4). After cloning, install and pull LFS assets:

```sh
git lfs install
git lfs pull
```

The `.lfsconfig` in the repo root points LFS directly at GitHub, so no additional URL configuration is needed.

## Project structure

- `docs/` - project documentation, glossary, and schema
- `videos/` - sample Wild Rift gameplay videos (stored via Git LFS)
