# Exuviae Scripts & Testing

此目錄包含項目用於自動化測試、驗收與安全檢查的腳本。所有腳本均設計為可在 Windows PowerShell 環境下運行。

## 🚀 統一驗收入口

### `check.ps1`
這是項目的主控檢查腳本，整合了從契約到 E2E 的全流程。

- **快速測試 (Unit/Fast)**:
  ```powershell
  ./scripts/check.ps1
  ```
- **HTTP 流程驗收 (E2E)**:
  ```powershell
  ./scripts/check.ps1 -E2EHTTP
  ```
- **WebSocket 流程驗收 (E2E)**:
  ```powershell
  ./scripts/check.ps1 -E2EWS
  ```
- **安全稽核 (Safety Check)**:
  ```powershell
  ./scripts/check.ps1 -Safety
  ```
- **全量驗收 (Recommended before PR)**:
  ```powershell
  ./scripts/check.ps1 -All
  ```

---

## 🛠️ 專用測試腳本

### `e2e_pr4.ps1` (HTTP E2E)
驗證「HTTP 捕獲 -> 上傳 -> 存儲 -> 記錄」的完整流程。
- **特點**: 自動啟動 Hub，模擬 Node 進行 REST API 調用，並校驗影像落盤與 JSONL 記錄。

### `e2e_ws_pr5.ps1` (WS E2E)
驗證「Hub WS 指令廣播 -> Node 執行 -> HTTP 上傳」的流程。
- **特點**: 基於 SSOT 原則動態解析 Hub 設定，驗證跨協議的連動性。

---

## 🛡️ 安全與維護

### `pre_publish_check.ps1`
在推送至 GitHub 前執行的安全稽核。
- **功能**:
  - 掃描敏感檔案（`.env`, `*.key` 等）。
  - 偵測內容中的金鑰模式（`Bearer`, `AKIA` 等）。
  - 驗證 `.gitignore` 覆蓋率（確保 `data/`, `.venv/` 不會外洩）。
- **用法**:
  ```powershell
  ./scripts/pre_publish_check.ps1
  ```

---

## 🤝 貢獻者說明
- 請確保在修改 `hub` 或 `node` 的核心介面後，至少跑一遍 `./scripts/check.ps1 -All`。
- 如果新增了新的通訊消息類型，請先更新 `hub/contracts/` 下的 schema，腳本會自動動態解析。
