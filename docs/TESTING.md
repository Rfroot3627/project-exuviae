# Exuviae 測試與驗證手冊 (Testing Guide)

> 此文件提供專案開發中常用的測試指令範例。旨在讓開發者與 AI 代理人能透過「複製貼上」快速執行驗證。

---

## 🚀 快速指令 (Quick Copy-Paste)

### 1. 全量驗收 (PR 前必跑)
最完整的自動化校驗，包含安全性、契約、單元測試與端對端測試。
```powershell
./scripts/check.ps1 -All
```

### 2. 核心邏輯快刷 (不跑 E2E)
僅執行安全性檢查、契約校驗與 Pytest 單元測試，適合頻繁開發時使用（速度最快）。
```powershell
./scripts/check.ps1
```

### 3. 功能導向測試
針對特定功能模組進行端對端驗證。

**HTTP 拍照流程 (PR4):**
```powershell
./scripts/check.ps1 -E2EHTTP
```

**WebSocket 指令廣播流程 (PR5):**
```powershell
./scripts/check.ps1 -E2EWS
```

**安全性審計:**
```powershell
./scripts/check.ps1 -Safety
```

---

## 🛠️ 開發中專用驗證

### 驗證節點註冊列表 (Hub Registry)
測試 Node 是否能成功向 Hub 報到，以及 Hub 是否能正確回傳在線節點資訊。
```powershell
./scripts/verify_hub_node_registry.ps1
```

### 模擬相機拍照流程 (Local Mock)
在沒有 Raspberry Pi 的情況下，驗證相機拍照、上傳與存儲的核心鏈路。
```powershell
./scripts/verify_node_capture_local.ps1
```

---

## 📖 參數說明 (check.ps1)

| 參數 | 說明 | 涵蓋範圍 |
| :--- | :--- | :--- |
| `-All` | 全量檢查 | 安全性 + 契約 + 單元測試 + 所有 E2E |
| (無參數) | 基礎快刷 | 安全性 + 契約 + 單元測試 |
| `-E2EHTTP` | 端對端 (HTTP) | 單純驗證 HTTP 捕獲與上傳流程 |
| `-E2EWS` | 端對端 (WS) | 驗證 WS 指令轉發與後續上傳流程 |
| `-Safety` | 安全審計 | 掃描敏感資料與 Key |

---

## ❓ 常見問題與排查

### 1. 找不到 Python 虛擬環境
**錯誤**: `hub venv python not found`
**解決**: 請確保已在 `hub/` 與 `node/` 目錄下建立 `.venv` 並安裝依賴。
```powershell
# Hub
cd hub; python -m venv .venv; .venv/Scripts/pip install -r requirements.txt
# Node
cd node; python -m venv .venv; .venv/Scripts/pip install -e .
```

### 2. 連線逾時 (Timeout)
**錯誤**: `Execution Error: ConnectTimeout`
**解決**: 檢查是否有殘留的 Hub 進程佔用埠口，或者嘗試手動執行測試腳本。
```powershell
# 強制清理殘留進程
taskkill /F /IM python.exe /T
```

### 3. 契約校驗失敗
**解決**: 核心規範變更後，請確保 `tools/validate_contracts.py` 通過校驗。
```powershell
python tools/validate_contracts.py
```
