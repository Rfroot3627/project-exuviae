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
# 核心邏輯：完全根據路徑擁有者決定執行使用者 (路徑導向)
# 這樣管理員用 sudo 部署到他人目錄時，服務仍會以該目錄擁有者執行
DIR_OWNER=$(stat -c '%U' "$PROJECT_DIR")

if [ -n "$DIR_OWNER" ] && [ "$DIR_OWNER" != "root" ]; then
    CURRENT_USER="$DIR_OWNER"
else
    # 如果路徑屬於 root，則嘗試取得下達 sudo 的原始使用者
    if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
        CURRENT_USER="$SUDO_USER"
    else
        # 最後備案
        CURRENT_USER=$(logname 2>/dev/null || echo $USER)
    fi
fi

echo "============================================="
echo "安裝 Exuviae 服務"
echo "Project Directory: $PROJECT_DIR"
echo "Service User: $CURRENT_USER"
echo "Target: $TARGET"
echo "============================================="

install_service() {
    local svc_name=$1
    local sub_dir=""
    
    if [[ "$svc_name" == *"node"* ]]; then
        sub_dir="$PROJECT_DIR/node"
    elif [[ "$svc_name" == *"hub"* ]]; then
        sub_dir="$PROJECT_DIR/hub"
    fi

    local tpl_path="$PROJECT_DIR/deploy/systemd/${svc_name}.service"
    local dest_path="/etc/systemd/system/${svc_name}.service"

    if [ ! -f "$tpl_path" ]; then
        echo "[錯誤] 找不到服務檔: $tpl_path"
        return 1
    fi

    echo "正在設定 $svc_name ..."
    
    # 自動建立虛擬環境與安裝相依性
    if [ -d "$sub_dir" ]; then
        if [ ! -d "$sub_dir/.venv" ]; then
            echo "[環境] 正在為 $svc_name 建立虛擬環境 (.venv) ..."
            sudo -u "$CURRENT_USER" python3 -m venv "$sub_dir/.venv"
        fi
        echo "[環境] 正在為 $svc_name 安裝/更新相依性 ..."
        sudo -u "$CURRENT_USER" "$sub_dir/.venv/bin/pip" install -q -e "$sub_dir"
    fi

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
