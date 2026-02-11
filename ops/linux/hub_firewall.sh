#!/bin/bash
# ops/linux/hub_firewall.sh
# Hub Firewall Management Script for Linux (Strict SSOT)
# Supports: status, open, close

set -e

RULE_COMMENT="exuviae-hub-allow-pi"
ENV_FILE="$(dirname "$0")/../../.agent/local/ops.env"

show_usage() {
    echo "Usage: $0 {status|open|close}"
    exit 1
}

get_config() {
    if [ ! -f "$ENV_FILE" ]; then
        echo "[ERROR] Configuration file not found: $ENV_FILE" >&2
        echo "Please 'cp .agent/local/ops.env.example .agent/local/ops.env' and fill it." >&2
        exit 1
    fi
    # Simple parser for KEY=VALUE
    PI_IP=$(grep '^PI_IP=' "$ENV_FILE" | cut -d'=' -f2-)
    HUB_PORT=$(grep '^HUB_PORT=' "$ENV_FILE" | cut -d'=' -f2-)
}

check_ufw() {
    if ! command -v ufw >/dev/null 2>&1; then
        echo "[ERROR] 'ufw' not found. Please install it or use iptables manually." >&2
        exit 1
    fi
}

do_status() {
    echo "== (OS) Linux Firewall Status (ufw) =="
    if sudo ufw status | grep -q "inactive"; then
        echo "Status: INACTIVE"
    else
        echo "Status: ACTIVE"
        sudo ufw status verbose | grep "$HUB_PORT/tcp" || echo "No specific rules for port $HUB_PORT found."
    fi
    echo ""
    echo "[Note] Please manually verify if the above rules restrict to your PI_IP."
}

do_open() {
    get_config
    if [ -z "$PI_IP" ] || [ -z "$HUB_PORT" ]; then
        echo "[ERROR] Missing PI_IP or HUB_PORT in ops.env" >&2
        exit 1
    fi

    check_ufw
    echo "== Opening Firewall for Pi ($PI_IP) on Port $HUB_PORT =="
    sudo ufw allow from "$PI_IP" to any port "$HUB_PORT" proto tcp comment "$RULE_COMMENT"
}

do_close() {
    get_config
    if [ -z "$PI_IP" ] || [ -z "$HUB_PORT" ]; then
        echo "[ERROR] Missing PI_IP or HUB_PORT in ops.env to identify rule" >&2
        exit 1
    fi

    check_ufw
    echo "== Closing Firewall Rule for Pi ($PI_IP) on Port $HUB_PORT =="
    # ufw doesn't have "disable", so we use deny to 'close' it while keeping a record
    sudo ufw deny from "$PI_IP" to any port "$HUB_PORT" proto tcp comment "$RULE_COMMENT"
}

case "$1" in
    status) do_status ;;
    open)   do_open ;;
    close)  do_close ;;
    *)      show_usage ;;
esac
