# Hub Tests

## 測試環境準備

Hub 的測試應在 `hub` 目錄下的虛擬環境中執行。

1. **安裝依賴（含測試工具）**:
   ```powershell
   cd hub
   .venv\Scripts\pip install -e .[test]
   ```

## 執行測試

### 自動化測試 (Automated Tests)
使用 `pytest` 執行整合測試，驗證完整資料流：Capture -> Upload(persist) -> Logline。

```powershell
cd hub
# 執行 PR4 完整資料流測試
.venv\Scripts\pytest tests/test_pr4_flow.py

# 執行基礎資料面測試
.venv\Scripts\pytest tests/test_data_plane.py
```

### 手動驗證 (Manual Verification)
針對 Windows 環境，建議使用 PowerShell 配合 Python 腳本進行，以確保路徑推導符合 SSOT。

**前提條件**: Hub 伺服器必須正在運行 (`python -m exuviae_hub.main`)

#### 步驟 1：觸發捕獲指令 (HTTP)
```powershell
$r = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v0/capture" -Body '{"node_id":"cam-test-01"}' -ContentType "application/json"
$sid = $r.snapshot_id
```

#### 步驟 2：執行影像上傳 (對齊 OpenAPI 欄位)
```powershell
.venv\Scripts\python -c "import requests; r = requests.post('http://127.0.0.1:8000/api/v0/snapshots/upload', data={'node_id':'cam-test-01', 'snapshot_id':'$sid'}, files={'image':('t.jpg', b'\xff\xd8\xff\xd9', 'image/jpeg')}); print(r.json())"
```

#### 步驟 3：確認日誌產出 (影像落盤後)
追加日誌發生於影像上傳完成時。請透過 Python 動態推導路徑並確認行數：
```powershell
.venv\Scripts\python -c "from exuviae_hub.infrastructure.config import settings; from pathlib import Path; p = Path(settings.DATA_ROOT) / settings.LOG_SUBDIR / settings.VISION_LOG_FILENAME; print(f'Total Log Lines: {len(p.read_text().splitlines())}')"
```

## 測試檔案說明
- `tests/test_pr4_flow.py`: 驗證 `Capture -> Upload -> Logline` 完整流程與資料關聯。
- `tests/test_data_plane.py`: 驗證 `POST /api/v0/snapshots/upload` 基礎功能。
- `src/exuviae_hub/core/patterns.py`: 系統唯一真相 (SSOT) 的正則表達式來源。
