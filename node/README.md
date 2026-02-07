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

**SSOT 保證**:
- 腳本執行時會印出解析到的 Endpoint 與欄位清單。
- 若契約定義有誤，腳本將啟動 Fail-fast 機制立即報錯。
