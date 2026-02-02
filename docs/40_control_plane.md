# 40 Control Plane (WebSocket)

## Must
- Control channel: WebSocket
- v0.1 message types:
  - Hub -> Node: command.capture_snapshot
  - Node -> Hub: ack
  - Node -> Hub: error
  - (optional) Node -> Hub: heartbeat
- Hub does not send result messages in v0.1.

## Should
- Every command includes:
  - snapshot_id (primary correlation key)
  - node_id (optional in message if channel is already bound to node_id)
  - issued_at (optional; useful for debugging)

## Examples
### WS connect
- `/ws/v0?node_id=cam-01`
- token is optional in v0.1

### command.capture_snapshot
```json
{
  "type": "command.capture_snapshot",
  "snapshot_id": "s-20260202-173012-4f2a",
  "params": {
    "format": "jpeg",
    "resolution": "640x480"
  }
}
```

### ack
```json
{
  "type": "ack",
  "snapshot_id": "s-20260202-173012-4f2a",
  "status": "capturing"
}
```

### error
```json
{
  "type": "error",
  "snapshot_id": "s-20260202-173012-4f2a",
  "code": "camera_unavailable",
  "message": "camera device not found"
}
```

## Open Questions
- Define a minimal error code list for v0.1 (camera_unavailable, upload_failed, invalid_params, busy, ...)

## Changelog
- v0.1: initial message set
