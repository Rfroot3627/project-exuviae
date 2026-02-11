# Hub Linux Ops Guide

此目錄包含管理 Linux 環境下 Hub 網路存取與啟動的運維工具。

## 操作順序
1. **檢查狀態**: `./hub_firewall.sh status`
2. **開放連線**: `./hub_firewall.sh open` (需 sudo 權限)
3. **啟動 Hub**: `./run_hub.sh`
4. **關閉連線**: `./hub_firewall.sh close`

## 配置
請確保 `.agent/local/ops.env` 已建立並填入 `PI_IP` 與 `HUB_PORT`。

## 注意事項
- **權限**: 防火牆操作需具備 `sudo` 權限。
- **工具**: 預設使用 `ufw`。若系統未安裝，請先執行 `sudo apt install ufw`。
