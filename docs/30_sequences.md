# 30 Sequences (Use-cases & Flows)

## Must
- Roles:
  - Hub: sends commands, receives snapshots, generates descriptions, writes logs.
  - Camera Node: receives commands, captures snapshot, uploads snapshot, ACK/ERROR only.
- v0.1 primary use-case: Manual capture via Hub HTTP API.

## Should
- One capture request produces exactly one snapshot upload and one log entry (unless error).

## Examples
### UC-01 Manual capture
1) Camera Node registers (HTTP)
2) Camera Node opens control channel (WebSocket)
3) User calls Hub `/api/v0/capture` with node_id
4) Hub sends WS command `capture_snapshot` with snapshot_id
5) Node captures and uploads via HTTP multipart to `/api/v0/snapshots/upload`
6) Hub stores image, generates description, appends JSONL log
7) Done (no result message back to node in v0.1)

## Open Questions
- Should Hub queue multiple capture requests or reject when busy?

## Changelog
- v0.1: UC-01 added
