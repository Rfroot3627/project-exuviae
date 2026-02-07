# Exuviae Node

## 快速開始 (MVP v0.1)

### 1. 環境準備 (Windows)

```powershell
cd node
python -m venv .venv
.venv\Scripts\pip install requests
```

### 2. PR4 Smoke 整合測試

此腳本用於模擬 Node 接收指令後，與已啟動的 Hub 進行「獲取 ID -> 上傳影像」的完整流程。

**前提條件**: Hub 伺服器必須正在運行 (`python -m exuviae_hub.main`)。

```powershell
# 執行 Smoke 腳本
.venv\Scripts\python scripts/pr4_smoke.py
```

**預期行為**:
1. 向 Hub 請求並獲取 `snapshot_id`。
2. 以 Multipart 形式上傳 mock JPEG 影像。
3. 輸出 Hub 回傳的 `image_path`。
4. 最終 Hub 端的 `vision.jsonl` 應會增加一筆與此 `snapshot_id` 關聯的紀錄。
