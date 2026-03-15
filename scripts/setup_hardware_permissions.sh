#!/bin/bash
# 用途: 設定 Linux 節點的硬體相機權限與相依套件 (ffmpeg, v4l-utils)
# 執行方式: sudo bash scripts/setup_hardware_permissions.sh

set -e

if [ "$EUID" -ne 0 ]; then
  echo "請使用 root 或 sudo 權限執行此腳本。"
  exit 1
fi

# 取得目前專案絕對路徑
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
DIR_OWNER=$(stat -c '%U' "$PROJECT_DIR")

if [ -n "$DIR_OWNER" ] && [ "$DIR_OWNER" != "root" ]; then
    CURRENT_USER="$DIR_OWNER"
else
    if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
        CURRENT_USER="$SUDO_USER"
    else
        CURRENT_USER=$(logname 2>/dev/null || echo $USER)
    fi
fi

echo "============================================="
echo "安裝硬體相機依賴與設定權限"
echo "Target User: $CURRENT_USER"
echo "============================================="

echo "[1/3] 更新 apt 套件清單並安裝 ffmpeg 與 v4l-utils..."
apt-get update -qq
apt-get install -y ffmpeg v4l-utils

echo "[2/3] 將使用者 $CURRENT_USER 加入 video 群組..."
usermod -aG video "$CURRENT_USER"

echo "[3/3] 測試 /dev/video* 裝置狀態..."
if ls /dev/video* 1> /dev/null 2>&1; then
    ls -l /dev/video*
    echo "[成功] 系統已偵測到影像裝置。"
    echo "       (注意: 群組變更對執行中的 Systemd 服務可能需在 restart 後生效)"
else
    echo "[警告] 系統目前找不到 /dev/video* 裝置，請確認 USB WebCam 是否已正確連接。"
fi

echo "============================================="
echo "硬體權限設定完成！"
echo "建議: 若此節點的 Node 服務已在運行，請執行 'sudo systemctl restart exuviae-node'"
