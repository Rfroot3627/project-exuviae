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

### `verify_node_capture_local.ps1` (Node Capture)
驗證 Node 相機拍照功能的完整鏈路 (Unit/Mock)。
- **功能**:
  - 自動啟動 Hub 與 Node (使用 venv)。
  - 透過 API 觸發拍照指令。
  - 驗證 Node (Mock) 上傳的假圖片。
- **用途**: 開發階段快速驗證拍照邏輯與通訊流程，無需真實硬體。

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

## 🌐 區域網路 (LAN) 連線測試

當您需要從其它裝置（如 Raspberry Pi）連線至 Windows 上的 Hub 時，請參考以下步驟。

### 1. 啟動 Hub (監聽所有介面)
使用專用腳本啟動 Hub，這會將伺服器綁定至 `0.0.0.0`：
```powershell
./scripts/run_hub_local.ps1
```
*(注意：請確保您的網路防火牆已適當配置以允許連線)*

#### ⚠️ 連線前提 (Prerequisites)
若您遇到連線逾時 (Timeout)，請手動檢查以下設定：

1. **Hub 綁定位址**: 必須使用 `0.0.0.0` 啟動 (腳本已預設)。
2. **防火牆規則 (Firewall)**: 
   Windows 預設會阻擋外部連線。若需開放，請以**管理員權限**執行 PowerShell：
   ```powershell
   # 手動開放 TCP 8000 埠口
   New-NetFirewallRule -DisplayName "Exuviae Hub LAN Access" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```

### 2. 取回 IP 與連線
1. 在 Windows 執行 `ipconfig` 找到您的 IPv4 Address (例如 `192.168.x.x`)。
2. 在外部裝置嘗試存取：
   - **Docs**: `http://<YOUR_IP>:8000/docs`
   - **WS**: `ws://<YOUR_IP>:8000/ws/v0?node_id=pi-test`

---

## 🤝 貢獻者說明
- 請確保在修改 `hub` 或 `node` 的核心介面後，至少跑一遍 `./scripts/check.ps1 -All`。
- 如果新增了新的通訊消息類型，請先更新 `hub/contracts/` 下的 schema，腳本會自動動態解析。
