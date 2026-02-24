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

## 🛡️ 統一驗核 (Unified Verification)

為了維持規格的嚴肅性，請在任何變動後於根目錄執行：

```powershell
./scripts/check.ps1 -All
```

其內部流程即代表了本專案的 **Definition of Done (v0.1)**：
1. **Safety Audit**: 掃描敏感資料。
2. **Contract Check**: 驗證 `hub/contracts/` 與程式的一致性。
3. **Unit Tests**: 執行 `pytest`。
4. **E2E Smoke**: 執行 HTTP 與 WS 的完整鏈路演練。