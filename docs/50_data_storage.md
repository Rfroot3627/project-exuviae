# 50 Data Plane & Storage

## Must
- HTTP APIs (v0.1):
  - POST /api/v0/nodes/register
  - GET  /api/v0/nodes (optional but recommended)
  - POST /api/v0/capture
  - POST /api/v0/snapshots/upload (multipart)
- Snapshot storage:
  - Must store on disk with deterministic path containing date + node_id + snapshot_id.
- Description log:
  - JSONL file (append-only) with traceability fields.

## Should
- Keep request/response JSON simple and stable.
- Allow extra fields in payloads (forward-compatible).

## Examples
### POST /api/v0/nodes/register
Request JSON: (see docs/20_capabilities.md)
Response JSON:
```json
{ "ok": true }
```

### POST /api/v0/capture
Request:
```json
{ "node_id": "cam-01" }
```
Response:
```json
{ "ok": true, "snapshot_id": "s-20260202-173012-4f2a" }
```

### POST /api/v0/snapshots/upload (multipart)
Fields:
- node_id: cam-01
- snapshot_id: s-...
- meta: JSON string (optional)
- image: file

Response:
```json
{ "ok": true }
```

### Storage path (example)
- data/snapshots/2026-02-02/cam-01/s-20260202-173012-4f2a.jpg

### JSONL log line (minimum)
```json
{
  "ts": "2026-02-02T17:30:15+08:00",
  "node_id": "cam-01",
  "snapshot_id": "s-20260202-173012-4f2a",
  "image_path": "data/snapshots/2026-02-02/cam-01/s-20260202-173012-4f2a.jpg",
  "desc": "A monitor showing a terminal window on a desk."
}
```

## Open Questions
- tags/model/latency_ms fields in v0.1 log: include now or defer?

## Changelog
- v0.1: initial APIs + storage/log format
