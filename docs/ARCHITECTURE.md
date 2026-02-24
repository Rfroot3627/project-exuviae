# Exuviae System Architecture

> 此文件說明 Exuviae 的核心設計架構，旨在讓維護者與 AI 代理人能快速理解系統運作原理。

## 核心哲學：Strict SSOT
項目的所有開發均遵循 **Single Source of Truth (SSOT)**，即「協議規格先行」。
- **HTTP 規格**: [openapi.v0.yaml](../hub/contracts/http/openapi.v0.yaml)
- **WS 規格**: [messages.schema.json](../hub/contracts/ws/messages.schema.json)

## Hub 架構 (Clean Architecture)
Hub 容器化了複雜的影像處理與日誌紀錄，並透過分層確保擴展性：

### 1. 領域層 (Domain/Core)
- **位置**: `hub/src/exuviae_hub/core/`
- **職責**: 定義 `Node` 模型（ node_id, kind, capabilities 等）與身分生成器 (`ids.py`)。

### 2. 應用層 (Application)
- **位置**: `hub/src/exuviae_hub/application/`
- **職責**: 實作商務邏輯 (`Use Cases`) 與定義外部抽象介面 (`Repositories`)。
  - `RegisterNode`: 處理節點報到。
  - `ListNodes`: 查詢在線節點。
  - `IngestSnapshotUpload`: 處理影像上傳、視覺描述並寫入日誌。

### 3. 基礎設施層 (Infrastructure)
- **位置**: `hub/src/exuviae_hub/infrastructure/`
- **職責**: 實體存儲實作。
  - `InMemoryNodeRepository`: 記憶體中的註冊資訊。
  - `FsSnapshotStore`: 文件系統影像儲存。

### 4. 適配器層 (Adapters/HTTP & WS)
- **位置**: `hub/src/exuviae_hub/adapters/`
- **職責**: 轉換通訊協議。Hub 的廣播機制具備「規格護欄」，會動態解析 JSON Schema 僅允許合法的指令轉發。

## Node 註冊流程
1. **Node 啟動**: 載入本地配置。
2. **HTTP 報到**: 呼叫 `/api/v0/nodes/register`，Hub 將 `Node Info` 存入 Registry。
3. **WS 建立**: 連線至 `/ws/v0?node_id=...`。
4. **準備就緒**: 此時 Hub 的 `/api/v0/nodes` 清單應能即時反映該 Node 的在線狀態。

## 常用工具
- **驗證註冊表**: `scripts/verify_hub_node_registry.ps1`
- **端對端拍照測試**: `scripts/verify_node_capture_local.ps1`
