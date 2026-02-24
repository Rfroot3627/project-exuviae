# project-exuviae (Knowledge Map)

> “A hub for passive nodes: capture, describe, log.”
> 
> **此專案採用「規格先行 (SSOT)」與「代理人友善 (Agent-Friendly)」設計。**
> 無論您是開發者或解讀此專案的 AI 代理人，請以本目錄作為唯一導航入口。

---

## 🗺️ 知識地圖 (Navigation & Docs)

為了讓您（或您的 AI 夥伴）在不遍歷整個專案的情況下掌握現況，請依序閱讀以下導航點：

### 1. 核心架構與設計
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: **[必讀]** 分層架構（Clean Architecture）、組件關係與 Node 註冊流程。

### 2. 核心規範 (Strict SSOT)
所有通訊與行為皆由以下規格定義，嚴禁出現「第二真相」：
- **[HTTP API 規格](hub/contracts/http/openapi.v0.yaml)**: 定義所有 REST 端點與 DTO。
- **[WebSocket 協議](hub/contracts/ws/messages.schema.json)**: 定義即時指令與回饋訊息結構。
- **[開發原則](docs/spec/principles.md)**: 專案必須遵守的規範與約束。

### 3. 開發與演進
- **[開發藍圖](docs/spec/roadmap.md)**: 目前進度與未來規劃。
- **[Agent 協作規範](docs/spec/repo/agentic-dev.md)**: 如何與 Antigravity 共舞。
- **[規格概覽](docs/spec/README.md)**: 關於規格層級的詳細說明。

---

## 🚀 快速啟動
本專案分為兩個主要組件，各目錄下皆有專屬 `README`：
- **[Hub Server](hub/README.md)**: FastAPI 核心，負責日誌與指令轉發。
- **[Node Client](node/README.md)**: 相機節點，支援 Pi Camera 與 Mock 模式。

---

## 🛡️ 自動化驗收 (Verification)
專案提供一鍵驗收機制，確保任何異動皆符合規格：
- **[scripts/README.md](scripts/README.md)**: 查看所有驗證腳本說明。

```powershell
# 執行全量驗收 (建議在 PR 前執行)
./scripts/check.ps1 -All
```

## 📂 目錄快照
- `hub/`: Hub 伺服器
- `node/`: Node 客戶端
- `docs/`: 全專案文檔與規格 (已整合 `spec/`)
- `scripts/`: 自動化工具
