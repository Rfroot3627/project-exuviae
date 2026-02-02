# 00 Scope (v0.1)

## Must
- Project name: project-exuviae
- Tagline: “A hub for passive nodes: capture, describe, log.”
- v0.1 goal:
  - Camera Node provides snapshots on request.
  - Hub stores snapshots, generates scene descriptions, and appends logs.
- Implementation language:
  - Hub: Python
  - Camera Node (on Raspberry Pi): Python (initially)
- Deployment:
  - Dev: Windows
  - Deploy: Raspberry Pi + Linux host

## Should
- Keep specs stable and backwards-compatible within v0.x (additive changes preferred).
- Keep v0.1 minimal: one node type (camera), snapshot-only.

## Examples
- A single button/API call triggers a capture sequence and produces one JSONL log line.

## Open Questions
- None (v0.1 scope fixed).

## Changelog
- v0.1: initial scope
