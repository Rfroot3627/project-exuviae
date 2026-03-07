#!/bin/bash
# 用途: 自動註冊並啟動 Exuviae 的 Systemd 與 Nginx 服務
# 執行方式: sudo bash deploy/install_services.sh node (或 hub, 或 all)

set -e

if [ "$EUID" -ne 0 ]; then
  echo "請使用 root 或 sudo 權限執行此腳本。"
  exit 1
fi

TARGET=$1
if [ -z "$TARGET" ]; then
    echo "Usage: $0 {node|hub|all}"
    exit 1
fi

# 取得目前專案絕對路徑
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
CURRENT_USER=$(logname 2>/dev/null || echo $SUDO_USER || echo $USER)

# 優先使用 $SUDO_USER（sudo 時記錄的原始使用者）
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    CURRENT_USER="$SUDO_USER"
elif [ -z "$CURRENT_USER" ] || [ "$CURRENT_USER" = "root" ]; then
    # 最後以目錄擁有者作為後備
    CURRENT_USER=$(stat -c '%U' "$PROJECT_DIR")
fi

echo "============================================="
echo "安裝 Exuviae 服務"
echo "Project Directory: $PROJECT_DIR"
echo "Service User: $CURRENT_USER"
echo "Target: $TARGET"
echo "============================================="

install_service() {
    local svc_name=$1
    local tpl_path="$PROJECT_DIR/deploy/systemd/${svc_name}.service"
    local dest_path="/etc/systemd/system/${svc_name}.service"

    if [ ! -f "$tpl_path" ]; then
        echo "[錯誤] 找不到服務檔: $tpl_path"
        return 1
    fi

    echo "正在設定 $svc_name ..."
    # 取代佔位符並寫入
    sed -e "s|PLACEHOLDER_PROJECT_DIR|$PROJECT_DIR|g" \
        -e "s|PLACEHOLDER_USER|$CURRENT_USER|g" \
        "$tpl_path" > "$dest_path"

    systemctl daemon-reload
    systemctl enable "$svc_name"
    systemctl restart "$svc_name"
    echo "$svc_name 服務已啟動。狀態檢查: sudo systemctl status $svc_name"
}

install_nginx() {
    echo "正在設定 Nginx 代理 ..."
    if ! command -v nginx >/dev/null 2>&1; then
        echo "[警告] 系統未安裝 Nginx，略過設定。"
        return 0
    fi
    
    # 確保 sites-available 和 sites-enabled 目錄存在 (相容某些發行版)
    mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
    
    cp "$PROJECT_DIR/deploy/nginx/exuviae.conf" "/etc/nginx/sites-available/exuviae.conf"
    ln -sf "/etc/nginx/sites-available/exuviae.conf" "/etc/nginx/sites-enabled/exuviae.conf"
    
    # 移除 nginx 預設的 default，避免 port 80 衝突
    rm -f "/etc/nginx/sites-enabled/default"

    systemctl restart nginx
    echo "Nginx 代理已啟動。"
}

if [ "$TARGET" = "node" ] || [ "$TARGET" = "all" ]; then
    install_service "exuviae-node"
fi

if [ "$TARGET" = "hub" ] || [ "$TARGET" = "all" ]; then
    install_service "exuviae-hub"
    install_nginx
fi

echo "安裝完成！"
