# Exuviae 系統接口手冊 (System Interfaces)

> 此文件條列了 Hub 與 Node 之間所有可用的通訊接口與功能。
> 所有的實作均嚴格遵守 [OpenAPI](../hub/contracts/http/openapi.v0.yaml) 與 [WebSocket Schema](../hub/contracts/ws/messages.schema.json)。

---

## 🏗️ Hub 接口 (Hub API - HTTP)

Hub 作為系統的核心調度者，提供以下 REST 接口：

### 1. 節點管理 (Node Management)
| 功能 | 端點 | 方法 | 說明 |
| :--- | :--- | :--- | :--- |
| **報到/註冊** | `/api/v0/nodes/register` | `POST` | Node 啟動時呼叫，傳遞 ID、固件版本與能力。 |
| **列出節點** | `/api/v0/nodes` | `GET` | 查詢目前所有已註冊節點的狀態與最後見面時間。 |

### 2. 影像處理 (Snapshot Data Plane)
| 功能 | 端點 | 方法 | 說明 |
| :--- | :--- | :--- | :--- |
| **請求拍照** | `/api/v0/capture` | `POST` | 觸發指定 Node 的拍照指令（由 Hub 透過 WS 轉發）。 |
| **上傳影像** | `/api/v0/snapshots/upload` | `POST` | Node 完成拍照後，將影像以 Multipart 格式上傳至此。 |

### 3. 控制平面 (Control Plane)
| 功能 | 端點 | 方法 | 說明 |
| :--- | :--- | :--- | :--- |
| **WS 連線** | `/ws/v0` | `GET (Upgrade)` | 持久化 WebSocket 連線。參數：`?node_id=cam-01`。 |

---

## 📷 Node 接口 (Node Capabilities - WS Handler)

Node 作為被動式節點，透過 WebSocket 接收並處理來自 Hub 的指令：

### 1. 接收指令 (Inbound Commands)
當 Hub 廣播或點對點發送訊息時，Node 支援處理以下 `type`：
- **`command.capture_snapshot`**: 
  - **參數需求**: 包含 `snapshot_id`, `format`, `resolution`。
  - **Node 行為**: 執行硬體或 Mock 拍照，完成後自動呼叫 Hub 的上傳接口。

### 2. 發送回饋 (Outbound Feedback)
Node 在執行過程中，會主動向 Hub 發送以下訊息：
- **`ack`**: 報告當前進度（`capturing`, `uploading`, `done`）。
- **`heartbeat`**: 定期發送，向 Hub 證明「我還活著」(Planned)。
- **`error`**: 當拍照或上傳失敗時，回報詳細錯誤代碼（如 `camera_unavailable`）。

---

## 📊 數據格式參考 (Schemas)

### Node Info (報到資訊)
```json
{
  "node_id": "cam-01",
  "kind": "node-runtime",
  "firmware": "0.1.0",
  "capabilities": {
    "camera": true,
    "platform": "rpi"
  }
}
```

### Snapshot Command (拍照指令)
```json
{
  "type": "command.capture_snapshot",
  "snapshot_id": "s-20260224-120000-abcdef12",
  "params": {
    "format": "jpeg",
    "resolution": "1920x1080"
  }
}
```
---
**提示**：開發新功能前，請務必先修改 `hub/contracts/` 下的規格文件。
