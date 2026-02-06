# Node Tests

## 測試環境準備

Node 的測試應在 `node` 目錄下的虛擬環境中執行。

1. **安裝依賴（含測試工具）**:
   ```bash
   cd node
   .venv\Scripts\pip install -e .[test]
   ```

## 執行測試

### 單元測試 (Unit Tests)
目前主要測試配置載入邏輯。

```bash
cd node
.venv\Scripts\pytest tests/test_config_loader.py
```

### 整合驗證 (Integration Verification)
手動驗證 Node 是否能成功向 Hub 註冊並建立 WebSocket 連線。

**前提條件**: Hub 伺服器必須正在運行 (http://127.0.0.1:8000)

1. **啟動 Node**:
   ```bash
   cd node/src
   ..\.venv\Scripts\python.exe -m exuviae_node.main
   ```

2. **預期日誌**:
   - `Config loaded for node: cam-01`
   - `Registering node at http://127.0.0.1:8000/api/v0/nodes/register...`
   - `Registration successful: {'ok': True}`
   - `Connected to Hub WS.`

## 測試檔案說明
- `tests/test_config_loader.py`: 驗證 `infrastructure/config/loader.py` 是否能正確解析 `default.yaml` 格式。
- `src/exuviae_node/main.py`: 包含內建的 boot/register/connect 流程驗證邏輯。
