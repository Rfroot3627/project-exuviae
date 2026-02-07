# Exuviae Hub

> “The only coordinator in the v0.1 star topology.”

## 快速開始 (Windows)

### 1. 環境準備
```powershell
cd hub
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # 或使用 uv / pip install .
```

### 2. 啟動 Hub
```powershell
# 使用預設設定啟動
uvicorn exuviae_hub.main:app --port 8000 --reload
```

## 配置 (Environment Variables)
所有配置均可透過環境變數覆蓋 (前綴為 `EXUVIAE_`)：
- `EXUVIAE_DATA_ROOT`: 資料儲存根目錄 (預設 `data`)
- `EXUVIAE_SNAPSHOT_SUBDIR`: 影像子目錄 (預設 `snapshots`)
- `EXUVIAE_VISION_LOG_FILENAME`: 日誌檔名 (預設 `vision.jsonl`)

## 測試與驗證
Hub 包含單元測試、整合測試與 WS 廣播測試：

```powershell
# 執行 pytest (不含 E2E)
.venv\Scripts\python -m pytest

# 執行 E2E 驗證 (需配合 Node)
../../scripts/check.ps1 -E2EWS
```

## 核心行為 (v0.1)
- **WS 廣播**: 接收來自 `/ws/v0` 的訊息並廣播給所有連線節點，實現 Hub 觸發之拍照指令。
- **影像落盤**: 在 `DATA_ROOT/snapshots/{date}/{node_id}/` 儲存 JPEG。
- **日誌追蹤**: 每筆成功上傳均會在 `DATA_ROOT/logs/vision.jsonl` 增加紀錄。
