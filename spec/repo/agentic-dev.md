# Agentic 開發協議（給 antigravaty / 其他 agent）

## TL;DR（每次任務都必須遵守）
- 僅修改任務允許的路徑；未列入允許範圍的檔案一律不得更動。
- 不得建立「第二真相」：不得在程式中硬編碼 NodeId/SnapshotId/ImagePath 的 regex；不得複製/重寫 schema 定義。
- 任何契約或 examples 變更後，必須通過：`tools\check_contracts.cmd`
- 交付時必須提供：變更檔案清單、如何手動測、以及檢查命令的輸出摘要。

## 不可違反的規則
- SSOT：
  - patterns：`hub/contracts/_ssot/patterns.v0.1.json`
  - 公開 API：`hub/contracts/http/openapi.v0.yaml` 的 components/schemas
- 契約一致性：一律以 tools 驗收結果為準；不得為了「好寫」去改契約。
- $ref-only：node_id/snapshot_id/image_path 相關欄位必須引用 defs/components，不得 inline pattern。

## 提交粒度
- 一次 PR 至少 1 個 commit，最多 3 個 commit；每個 commit 都要能解釋「為何需要」。
- 禁止把不相關的格式化/重排混進同一個 commit。

## 交付格式
- 檔案清單（含新增/修改/刪除）
- 驗收命令與結果（至少貼出最後一段 OK）
- 若有取捨，說明取捨理由與替代方案

## 關於測試與環境
- hub相關測試使用的環境為 hub\.venv\Scripts\python
- node相關測試使用的環境為 node\.venv\Scripts\python
- 文件與規格相關測試使用的環境為 .venv\Scripts\python