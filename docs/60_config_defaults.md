# 60 Config & Defaults

## Must
- v0.1 uses fixed capture settings (hard-coded defaults):
  - format: jpeg
  - resolution: fixed (default 640x480)
  - frequency: manual only (no periodic capture)
- Hub must define:
  - DATA_ROOT
  - SNAPSHOT_DIR pattern
  - LOG_PATH (JSONL)

## Should
- Even if values are fixed in v0.1, keep fields in protocol for future upgrades:
  - command params may include resolution/format but Hub may ignore non-default values in v0.1.

## Examples
- Defaults:
  - SNAPSHOT_FORMAT = "jpeg"
  - SNAPSHOT_RESOLUTION = "640x480"
  - LOG_PATH = "data/logs/vision.jsonl"

## Open Questions
- Add CAPTURE_COOLDOWN_SEC default now?

## Changelog
- v0.1: initial defaults
