# Exuviae Node

## 快速開始 (MVP v0.1)

### 1. 環境準備 (Windows)

```powershell
cd node
python -m venv .venv
.venv\Scripts\pip install requests
```

### 2. PR4 Smoke 整合測試 (Strict SSOT)

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

**SSOT 保證**:
- 腳本執行時會**動態解析** `hub/contracts/` 下的 OpenAPI 與 JSON Schema。
- 若契約定義有誤（如欄位名變動），腳本將啟動 Fail-fast 機制立即報錯，不依賴硬編碼。

## 預期結果
- Node 端收到指令並完成上傳。
- Hub 端 `DATA_ROOT/snapshots/` 產生影像。
- Hub 端 `DATA_ROOT/logs/vision.jsonl` 增加一筆紀錄且 ID 匹配。
