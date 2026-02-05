# contracts-harness v0.1.0 (frozen)

這是一份「契約底座」的封存快照，用來固定一個已驗證的基準點。

## 目標
- 可回溯：任何時候都能回到此版本狀態
- 可比對：後續改動可與此版本清楚對照
- 可移植：可直接複製到新專案作為起點（尚未抽取成通用工具）

## 內容
此快照包含：
- SSOT patterns（hub/contracts/_ssot）
- OpenAPI（hub/contracts/http/openapi.v0.yaml）與 components 作為公開 API SSOT
- JSON Schema（WS / logging / capabilities / node config）
- examples（所有 schema 對應 examples）
- 驗證工具（tools/validate_contracts.py、tools/check_contracts.cmd）

## 版本特性
- 強制 `$ref-only`（避免在契約中散落第二份真相）
- patterns 以 SSOT 檔案集中定義，並由工具強制各層一致
- image_path 的完整規則只認 SSOT；hub config 只提供前綴（DATA_ROOT / SNAPSHOT_SUBDIR）
- examples 掃描使用 SSOT regex

## 如何驗證
在專案根目錄執行：

```cmd

tools\check_contracts.cmd

```

預期輸出包含：

[OK] validated OpenAPI ...

各 examples [OK] ...

patterns 一致性檢查 [OK] ...

最後 All contracts OK.

使用方式（移植到新專案）

將此資料夾內的 hub/, node/, tools/ 複製到新 repo 對應位置（保持相對路徑）


視需求調整：

hub/src/.../config.py 的 DATA_ROOT, SNAPSHOT_SUBDIR

hub/contracts/_ssot/patterns.v0.1.json 的 image_path 前綴（若資料根目錄變更）

執行 tools\check_contracts.cmd 確認維持 All contracts OK.

注意：這是封存快照，不代表最新；後續演進以主線為準。
