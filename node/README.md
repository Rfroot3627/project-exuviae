# Exuviae Node

## 快速開始 (MVP v0.1)

### 1. 環境準備 (Windows)

```powershell
cd node
python -m venv .venv
.venv\Scripts\pip install -e .
```

### 2. 配置系統 (Configuration - v0.2)

Node 採用「規格先行」的載入機制。內容必須在 YAML 檔案中，環境變數僅作為指向該檔案的指標。

#### 🔹 載入優先序 (Priority)
1. **環境變數指定**: 讀取 `EXUVIAE_NODE_CONFIG` 指向的檔案路徑。
   - **Fail-fast**: 若變數已設定但檔案不存在，Node 將立即報錯中止，避免回退到預設值。
2. **自動向上搜尋**: 若無環境變數，將從執行路徑 (CWD) 開始向上搜尋 `.agent/local/config.yaml`。
   - **停止條件**: 搜尋到專案根目錄（含 `.git` 或 `pyproject.toml`）即停止。支援巢狀部署環境。
3. **預設配置**: 若以上皆無，回退至 `node/src/exuviae_node/infrastructure/config/default.yaml`。
   - **警告**: 此時 `stderr` 會輸出明確警告與配置建議。

#### 🔹 本地開發建議
請依範例建立本地配置：
- **位置**: `[RepoRoot]/.agent/local/config.yaml`
- **注意**: 此目錄已由 `.gitignore` 排除，適合存放包含真實 IP 與 ID 的私有設定。
- **範例檔**: 參考 `node/src/exuviae_node/infrastructure/config/default.yaml` 或專案提供的 `.example`。

---

### 3. PR4 Smoke 整合測試 (Strict SSOT)

此腳本會**動態解析** `hub/contracts/http/openapi.v0.yaml` 契約，自動提取所有 API 端點與欄位名稱。

**前提條件**: Hub 伺服器必須正在運行。

```powershell
# 執行基本 Smoke (自動解析契約 -> Capture -> Upload)
.venv\Scripts\python scripts/pr4_smoke.py

# 執行包含註冊的 Smoke
.venv\Scripts\python scripts/pr4_smoke.py --register

# 使用環境變數觸發註冊
$env:NODE_REGISTER=1; .venv\Scripts\python scripts/pr4_smoke.py
```

### 3. WS 指令觸發測試 (Strict SSOT)

此流程驗證「Hub 發送 WS 指令 -> Node 執行上傳 -> Hub 落盤」的完整路徑。

**手動執行 (分步)**:
1. **啟動 Node WS 客戶端**:
   ```powershell
   $env:HUB_WS_URL="ws://127.0.0.1:8000/ws/v0?node_id=cam-test-01"
   .venv\Scripts\python scripts/ws_node_smoke.py
   ```
2. **發送模擬指令** (另開視窗):
   ```powershell
   .venv\Scripts\python scripts/trigger_capture_ws.py
   ```

**自動化執行 (推薦)**:
在專案根目錄執行一鍵自動化測試：
```powershell
./scripts/check.ps1 -E2EWS
```

## 報到與連線流程 (Registration & Connection)
Node 隨附自動報到機制，確保其在 Hub 的註冊表中具備「身分」：
1. **HTTP 註冊**: 啟動時發送 `POST /api/v0/nodes/register`，傳遞 `capabilities`（例如：是否有相機）。
2. **WS 持久連線**: 註冊成功後維持 WebSocket 連線以接收拍照指令。

**SSOT 保證**:
- 腳本執行時會**動態解析** `hub/contracts/` 下的 OpenAPI 與 JSON Schema。
- 腳本執行時會**動態解析** `hub/contracts/` 下的 OpenAPI 與 JSON Schema。
- 若契約定義有誤（如欄位名變動），腳本將啟動 Fail-fast 機制立即報錯，不依賴硬編碼。

## 📸 相機拍照功能 (Camera Capture)

本專案支援 Raspberry Pi Camera 拍照功能，並具備跨平台 Mock 機制。

### 1. 支援硬體與模式
- **Raspberry Pi**: 自動偵測 `rpicam-still` 或 `libcamera-still` 指令，執行真實拍照。
- **Windows / Non-Pi**: 自動降級為 **Mock 模式**，生成全黑測試影像以驗證通訊流程。

### 2. 觸發方式
透過 Hub 發送 WebSocket 指令 `command.capture_snapshot`，Node 會自動：
1. 執行拍照 (Real/Mock)。
2. 將影像上傳至 Hub (`/api/v0/snapshots/upload`)。

### 3. 本地驗證 (Mock)
使用專用腳本驗證 Mock 拍照流程：
```powershell
./scripts/verify_node_capture_local.ps1
```

## 預期結果
- Node 端收到指令並完成上傳。
## WS 轉發機制說明 (Test Relay)

### 契約與協議範圍
本專案的 WebSocket 通訊協議嚴格定義於以下檔案：
- **消息結構**: [messages.schema.json](../hub/contracts/ws/messages.schema.json)
- **端點定義**: [openapi.v0.yaml](../hub/contracts/http/openapi.v0.yaml) 中的 `/ws/v0`

### 測試中繼 (Test Relay) 行為警告
目前 Hub 實作的 **「全體廣播」** 行為僅為了滿足 v0.1 MVP 的測試需求（由 Hub 觸發拍照指令給 Node）。
- **非協議保證**: 此轉發邏輯屬於「測試中繼」，**不屬於** 穩定版本的通訊協議。
- **不可依賴**: 生產環境的 Node 或 Hub 不應將此廣播行為視為穩定的 Routing 規則。
- **嚴格護欄**: Hub 已實作白名單護欄，僅會轉發契約中定義的消息類型，任何未知類型將被直接封鎖。

### 契約缺口 (Contract Gap) 定義
- **node_id**: 目前 OpenAPI 契約中 `/ws/v0` 缺少結構化的 `parameters` 定義。因此現有的 `?node_id=...` 傳遞方式僅視為測試輔助，不應作為生產環境的依據。
