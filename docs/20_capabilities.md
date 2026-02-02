# 20 Capabilities & Schema

## Must
- Node identity fields:
  - node_id: stable unique string
  - kind: string (v0.1 uses "camera")
  - firmware: semantic-ish version string
- Capabilities are declared at registration time and may be updated later.
- v0.1 must support:
  - capabilities.video_in for snapshot mode

## Should
- Capabilities should be additive and forward-compatible.
- Avoid hardcoding per-node assumptions in Hub; rely on capabilities.

## Examples
### Register payload (camera-only v0.1)
```json
{
  "node_id": "cam-01",
  "kind": "camera",
  "firmware": "0.1.0",
  "capabilities": {
    "video_in": {
      "modes": ["snapshot"],
      "formats": ["jpeg"],
      "resolutions": ["640x480"],
      "fps_max": 1
    }
  }
}
```

## Open Questions
- Naming convention for node_id (human-readable vs UUID)

## Changelog
- v0.1: initial camera capability schema
