#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE_NAME="sentinel-bot"
INSTALL_DIR="/opt/sentinel-bot"

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║  🛡  Sentinel Bot — Uninstaller           ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[✗] Запустите от root: sudo bash uninstall.sh${NC}"
    exit 1
fi

read -p "$(echo -e "${YELLOW}Удалить Sentinel Bot? Все данные будут потеряны! (y/n): ${NC}")" -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Отменено.${NC}"
    exit 0
fi

echo -e "${YELLOW}[i] Останавливаем сервис...${NC}"
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true
rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload

echo -e "${YELLOW}[i] Удаляем файлы...${NC}"
rm -rf "$INSTALL_DIR"

echo ""
echo -e "${GREEN}[✓] Sentinel Bot полностью удалён.${NC}"
