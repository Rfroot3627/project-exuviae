# 10 Principles & Boundaries

## Must
- Topology: hub-and-spoke (star). Hub is the only coordinator.
- Node-to-node communication: forbidden.
- Passive nodes:
  - Nodes must not initiate capture/upload without an explicit Hub command.
  - Nodes may keep only short-lived buffers needed to perform a command.
- v0.1 result notifications:
  - Hub does not send execution results back to nodes (no "result" messages).
- Observability:
  - Every snapshot must be traceable via node_id + snapshot_id to an on-disk image and a log entry.

## Should
- Prefer additive protocol evolution (new fields, new message types) over breaking changes.
- Keep control plane and data plane separated (even if both use HTTP/WS initially).

## Examples
- A camera node idles until it receives `capture_snapshot` over WebSocket.

## Open Questions
- Minimal auth in v0.1: token or trusted LAN only?

## Changelog
- v0.1: initial principles
