# Hub Windows Ops Guide

此目錄包含管理 Hub 網路存客與啟動的運維工具。

## 操作順序
1. **檢查狀態**: `.\hub_firewall.ps1 status`
2. **開放連線**: `.\hub_firewall.ps1 open` (需具備管理員權限)
3. **啟動 Hub**: `.\run_hub.ps1`
4. **關閉連線**: `.\hub_firewall.ps1 close` (測試完畢後)

## 配置
請確保 `.agent/local/ops.env` 已建立並填入 `PI_IP` 與 `HUB_PORT`。

## 注意事項
- **權限**: 管理防火牆規則需要以「管理員身分執行 PowerShell」。
- **安全性**: 規則僅開放 `HUB_PORT` 並限制來源位址為 `PI_IP`。
