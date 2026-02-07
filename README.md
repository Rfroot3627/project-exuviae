# project-exuviae

> “A hub for passive nodes: capture, describe, log.”

## 專案狀態 (v0.1 MVP)
- [x] **Node**: 已實作被動式攝影機節點 (WS 客戶端)，支援動態解析契約並與 Hub 通訊。
- [x] **Hub**: 已實作核心 Hub (FastAPI/Uvicorn)，支援影像接收、WS 指令廣播與 JSONL 日誌。
- [x] **E2E**: 已實作自動化 Smoke 測試與「全流程校驗」腳本。

## 目錄結構
- `hub/`: Hub 伺服器實作 (Python/FastAPI)
- `node/`: Node 客戶端實作 (Python)
- `specs/`: 專案核心規範與原則
- `scripts/`: 自動化驗證工具

## 快速驗證 (Windows PowerShell)
本專案提供一鍵驗證導向的腳本：

```powershell
# 1. 執行所有基礎檢查與測試 (不含 E2E)
./scripts/check.ps1

# 2. 執行 PR4 Smoke (HTTP 捕獲流程)
./scripts/check.ps1 -E2E

# 3. 執行 PR5 Smoke (WebSocket 指令 -> 上傳流程)
./scripts/check.ps1 -E2EWS
```

## 核心規格 (SSOT)
本專案嚴格遵守「契約為唯一真相」：
- **HTTP**: [openapi.v0.yaml](hub/contracts/http/openapi.v0.yaml)
- **WS**: [messages.schema.json](hub/contracts/ws/messages.schema.json)
