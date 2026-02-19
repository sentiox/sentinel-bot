#!/usr/bin/env bash

SERVICE_NAME="sentinel-bot"
INSTALL_DIR="/opt/sentinel-bot"

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
NC="\033[0m"

printf "${CYAN}\n"
printf "  ╔═══════════════════════════════════════════╗\n"
printf "  ║  Sentinel Bot — Uninstaller               ║\n"
printf "  ╚═══════════════════════════════════════════╝\n"
printf "${NC}\n"

if [ "$(id -u)" -ne 0 ]; then
    printf "${RED}[X] Run as root: sudo bash uninstall.sh${NC}\n"
    exit 1
fi

printf "${YELLOW}Remove Sentinel Bot? All data will be lost! (y/n): ${NC}"
read -r REPLY

if [ "$REPLY" != "y" ] && [ "$REPLY" != "Y" ]; then
    printf "${GREEN}Cancelled.${NC}\n"
    exit 0
fi

printf "${YELLOW}[i] Stopping service...${NC}\n"
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true
rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload

printf "${YELLOW}[i] Removing files...${NC}\n"
rm -rf "$INSTALL_DIR"

printf "\n"
printf "${GREEN}[OK] Sentinel Bot removed.${NC}\n"
