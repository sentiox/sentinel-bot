#!/usr/bin/env bash

# Auto-relaunch with bash if running under sh/dash
if [ -z "$BASH_VERSION" ]; then
    exec bash "$0" "$@"
fi

# ============================================
#  Sentinel Bot — Installer
#  https://github.com/sentiox/sentinel-bot
# ============================================

set -euo pipefail
trap 'print_error "Failed at line $LINENO. Run with: bash -x install.sh for debug"; exit 1' ERR

INSTALL_DIR="/opt/sentinel-bot"
SERVICE_NAME="sentinel-bot"
REPO_URL="https://github.com/sentiox/sentinel-bot.git"

# Colors
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
WHITE="\033[1;37m"
NC="\033[0m"

print_banner() {
    printf "${CYAN}\n"
    printf "  ╔═══════════════════════════════════════════╗\n"
    printf "  ║                                           ║\n"
    printf "  ║   Sentinel Bot — Installer                ║\n"
    printf "  ║   VPS Management & Monitoring             ║\n"
    printf "  ║                                           ║\n"
    printf "  ╚═══════════════════════════════════════════╝\n"
    printf "${NC}\n"
}

print_step()  { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
print_info()  { printf "${BLUE}[i]${NC} %s\n" "$1"; }
print_warn()  { printf "${YELLOW}[!]${NC} %s\n" "$1"; }
print_error() { printf "${RED}[X]${NC} %s\n" "$1"; }

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        print_error "Run as root: sudo bash install.sh"
        exit 1
    fi
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS="$ID"
        print_step "OS: $PRETTY_NAME"
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

install_dependencies() {
    print_info "Installing dependencies..."

    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq >/dev/null 2>&1
        apt-get install -y -qq python3 python3-pip python3-venv git wget curl >/dev/null 2>&1
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y -q python3 python3-pip git wget curl >/dev/null 2>&1
    elif command -v yum >/dev/null 2>&1; then
        yum install -y -q python3 python3-pip git wget curl >/dev/null 2>&1
    elif command -v pacman >/dev/null 2>&1; then
        pacman -Sy --noconfirm python python-pip git wget curl >/dev/null 2>&1
    else
        print_error "Unsupported package manager. Install python3, pip, git manually."
        exit 1
    fi

    print_step "Dependencies installed"

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_step "Python: $PYTHON_VERSION"
}

clone_repo() {
    if [ -d "$INSTALL_DIR" ]; then
        print_warn "Directory $INSTALL_DIR already exists"
        printf "${YELLOW}Overwrite? (y/n): ${NC}"
        read -r REPLY < /dev/tty
        if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
            rm -rf "$INSTALL_DIR"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    fi

    print_info "Cloning repository..."
    git clone -q "$REPO_URL" "$INSTALL_DIR"
    print_step "Cloned to $INSTALL_DIR"
}

setup_venv() {
    print_info "Creating virtual environment..."

    # Ensure python3-venv is available
    if ! python3 -m venv --help >/dev/null 2>&1; then
        print_info "Installing python3-venv..."
        if command -v apt-get >/dev/null 2>&1; then
            apt-get install -y -qq python3-venv >/dev/null 2>&1
        fi
    fi

    python3 -m venv "$INSTALL_DIR/venv" || {
        print_error "Failed to create venv. Trying with --without-pip..."
        python3 -m venv --without-pip "$INSTALL_DIR/venv"
        curl -sS https://bootstrap.pypa.io/get-pip.py | "$INSTALL_DIR/venv/bin/python3"
    }

    print_step "Virtual environment created"

    print_info "Installing pip packages..."
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip 2>&1 | tail -1
    "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" 2>&1 | tail -5
    print_step "Dependencies installed"
}

configure_bot() {
    printf "\n"
    printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    printf "${WHITE}  Settings${NC}\n"
    printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    printf "\n"

    # Bot Token
    printf "${YELLOW}Bot Token${NC}\n"
    printf "   Get from @BotFather in Telegram:\n"
    printf "   1. Open @BotFather\n"
    printf "   2. Send /newbot\n"
    printf "   3. Copy the token\n"
    printf "\n"
    printf "${WHITE}   Enter Bot Token: ${NC}"
    read -r BOT_TOKEN < /dev/tty

    while [ -z "$BOT_TOKEN" ]; do
        print_error "   Token cannot be empty!"
        printf "${WHITE}   Enter Bot Token: ${NC}"
        read -r BOT_TOKEN < /dev/tty
    done
    printf "\n"

    # Admin ID
    printf "${YELLOW}Your Telegram ID (Admin)${NC}\n"
    printf "   Get from @userinfobot or @getmyid_bot\n"
    printf "\n"
    printf "${WHITE}   Enter Telegram ID: ${NC}"
    read -r ADMIN_ID < /dev/tty

    while [ -z "$ADMIN_ID" ]; do
        print_error "   ID cannot be empty!"
        printf "${WHITE}   Enter Telegram ID: ${NC}"
        read -r ADMIN_ID < /dev/tty
    done
    printf "\n"

    # Group or Private
    printf "${YELLOW}Mode${NC}\n"
    printf "   1) Supergroup with topics (recommended)\n"
    printf "   2) Private messages (DM)\n"
    printf "\n"
    printf "${WHITE}   Choose (1/2): ${NC}"
    read -r MODE_CHOICE < /dev/tty

    GROUP_ID=""
    if [ "$MODE_CHOICE" = "1" ]; then
        printf "\n"
        printf "${YELLOW}Supergroup ID${NC}\n"
        printf "   How to get Group ID:\n"
        printf "   1. Create a supergroup in Telegram\n"
        printf "   2. Enable 'Topics' in group settings\n"
        printf "   3. Add bot as admin\n"
        printf "   4. Add @getmyid_bot to group\n"
        printf "   5. ID starts with -100...\n"
        printf "\n"
        printf "${WHITE}   Enter Group ID: ${NC}"
        read -r GROUP_ID < /dev/tty
    fi
    printf "\n"

    # Generate .env
    cat > "$INSTALL_DIR/.env" << ENVEOF
# Sentinel Bot Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

# Telegram Bot
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_ID
GROUP_ID=$GROUP_ID

# Topic IDs (auto-created by /setup_topics)
TOPIC_VPS_PANEL=
TOPIC_PAYMENTS=
TOPIC_BALANCE=
TOPIC_MONITORING=
TOPIC_ADMIN=
TOPIC_BACKUP=

# Monitoring
MONITOR_INTERVAL=300
ALERT_CPU_THRESHOLD=90
ALERT_RAM_THRESHOLD=90
ALERT_DISK_THRESHOLD=85

# Payment Reminders
REMINDER_DAYS=7,3,1,0

# Database
DB_PATH=$INSTALL_DIR/data/sentinel.db
ENVEOF

    mkdir -p "$INSTALL_DIR/data"
    print_step "Configuration saved"
}

create_service() {
    print_info "Creating systemd service..."

    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SVCEOF
[Unit]
Description=Sentinel Bot — Telegram VPS Management
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" >/dev/null 2>&1
    systemctl start "$SERVICE_NAME"
    print_step "Service created and started"
}

print_finish() {
    printf "\n"
    printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    printf "${GREEN}  Sentinel Bot installed!${NC}\n"
    printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    printf "\n"
    printf "  ${WHITE}Commands:${NC}\n"
    printf "  ${CYAN}Logs:${NC}      journalctl -u %s -f\n" "$SERVICE_NAME"
    printf "  ${CYAN}Status:${NC}    systemctl status %s\n" "$SERVICE_NAME"
    printf "  ${CYAN}Restart:${NC}   systemctl restart %s\n" "$SERVICE_NAME"
    printf "  ${CYAN}Stop:${NC}      systemctl stop %s\n" "$SERVICE_NAME"
    printf "  ${CYAN}Config:${NC}    nano %s/.env\n" "$INSTALL_DIR"
    printf "  ${CYAN}Uninstall:${NC} bash %s/uninstall.sh\n" "$INSTALL_DIR"
    printf "\n"
    printf "  ${WHITE}Next steps:${NC}\n"
    printf "  1. Open the bot in Telegram\n"
    printf "  2. Send /start\n"
    printf "  3. In the group send /setup_topics\n"
    printf "     (bot will create all topics automatically)\n"
    printf "\n"
    printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# === Main ===
print_banner
check_root
check_os
install_dependencies
clone_repo
setup_venv
configure_bot
create_service
print_finish
