# Spec Index (v0.1) — project-exuviae

本專案採用「契約就地、索引集中」：
- 人類可讀的索引/原則放在 `docs/spec/`
- 機器可讀的契約（schema/OpenAPI）放在 `../../hub/contracts/`（SSOT）
- Node 為單一 runtime，功能由啟動設定 `features` 決定（v0.1：啟動後不變）

---

## Layers (v0.1)

### L1 — Version / Scope / Language
- Hub: Python + FastAPI（Windows 開發，部署到 Linux 主機）
- Node: Python（部署到 Raspberry Pi）
- v0.1 目標：capture snapshot → describe → append JSONL log

### L2 — Principles & Boundaries
- 規範文件：`principles.md`

### L3 — Capabilities Model (Contracts)
- Node 註冊契約（SSOT）：`../../hub/contracts/capabilities/node_register.schema.json`
- 範例：`../../hub/contracts/capabilities/examples/`

### L4 — Sequences (Use-cases)
- v0.1 主用例：Hub 觸發 capture → Node 上傳 snapshot → Hub 寫 log
- 例子（先放在 contracts/examples，後續可補此處連結）

### L5 — Control Plane (WebSocket Contracts)
- WS 訊息契約（SSOT）：`../../hub/contracts/ws/messages.schema.json`
- 範例：`../../hub/contracts/ws/examples/`

### L6 — Data Plane & Storage (HTTP/OpenAPI + Logging)
- HTTP API（SSOT）：`../../hub/contracts/http/openapi.v0.yaml`
- Log line schema（SSOT）：`../../hub/contracts/logging/vision_log_line.schema.json`
- 範例：`../../hub/contracts/http/examples/`、`../../hub/contracts/logging/examples/`

### L7 — Config & Defaults
- Hub defaults：`../../hub/src/exuviae_hub/infrastructure/config.py`
- Node defaults：`../../node/src/exuviae_node/infrastructure/config/default.yaml`

---

## Definition of Done (v0.1)
- 契約檔案存在且可被驗證（OpenAPI / JSON Schema）
- Hub：
  - 能接受 /register、/capture、/snapshots/upload（依契約）
  - 能落盤 snapshot 並寫入一行 JSONL log
- Node：
  - 啟動後註冊 capabilities、建立 WS 連線
  - 收到 capture 命令後拍照並上傳 snapshot
- features 僅在啟動時決定（v0.1）