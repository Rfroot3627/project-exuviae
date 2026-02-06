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
使用 `pytest` 執行整合測試，驗證 API 規範與檔案落盤邏輯。

```powershell
cd hub
.venv\Scripts\pytest tests/test_data_plane.py
```

### 手動驗證 (Manual Verification)
針對 Windows 環境，建議使用 Python 腳本或修正後的 `curl.exe` 進行測試。

**前提條件**: Hub 伺服器必須正在運行 (`python -m exuviae_hub.main`)

#### 方法 A：使用 Python 驗證 (推薦)
```powershell
.venv\Scripts\python -c "import requests; resp = requests.post('http://127.0.0.1:8000/api/v0/snapshots/upload', data={'node_id': 'cam-01', 'snapshot_id': 's-20260206-235000-abcd1234'}, files={'image': ('test.jpg', b'fake_data', 'image/jpeg')}); print(resp.json())"
```

#### 方法 B：使用 Windows `curl.exe`
```powershell
# 1. 產生測試檔
echo "fake_data" > test.jpg

# 2. 執行上傳
curl.exe -X POST http://127.0.0.1:8000/api/v0/snapshots/upload -F "node_id=cam-01" -F "snapshot_id=s-20260206-235000-abcd1234" -F "image=@test.jpg"
```

## 測試檔案說明
- `tests/test_data_plane.py`: 驗證 `POST /api/v0/snapshots/upload` 端點。
  - 檢查 HTTP 狀態碼與 JSON 欄位（ok, snapshot_id, image_path）。
  - 驗證影像是否正確儲存於 `DATA_ROOT/SNAPSHOT_SUBDIR` 且路徑符合 SSOT 契約。
- `src/exuviae_hub/core/patterns.py`: 測試中使用的正則表達式來源，直接由契約 JSON 載入。
