# Hub Tests

## 安裝測試依賴

```bash
cd c:\Github_RRR\project-exuviae\hub
.venv\Scripts\pip install -e ".[test]"
```

或手動安裝：
```bash
.venv\Scripts\pip install requests
```

## 執行測試

### API 測試
測試 Hub 的 HTTP API 端點：

```bash
cd c:\Github_RRR\project-exuviae\hub
python tests\test_api.py
```

**前提條件**: Hub 伺服器必須正在運行 (http://127.0.0.1:8000)

### 運行服務器
在另一個終端視窗中：

```bash
cd c:\Github_RRR\project-exuviae\hub
.venv\Scripts\activate
uvicorn exuviae_hub.main:app --reload
```

## 測試內容

### test_api.py
- ✅ GET /docs - Swagger UI
- ✅ POST /api/v0/nodes/register - 節點註冊
- ✅ GET /api/v0/nodes - 列出節點 (501)
- ✅ POST /api/v0/capture - 觸發 Capture
- ✅ POST /api/v0/snapshots/upload - 上傳 Snapshot
