#!/usr/bin/env bash

# Auto-relaunch with bash if running under sh/dash
if [ -z "$BASH_VERSION" ]; then
    _tmp=$(mktemp /tmp/sentinel-install.XXXXXX)
    wget -qO "$_tmp" "https://raw.githubusercontent.com/sentiox/sentinel-bot/main/install.sh" 2>/dev/null || \
    curl -fsSL -o "$_tmp" "https://raw.githubusercontent.com/sentiox/sentinel-bot/main/install.sh" 2>/dev/null
    exec bash "$_tmp"
fi

# ============================================
#  Sentinel Bot — Installer
#  https://github.com/sentiox/sentinel-bot
# ============================================

INSTALL_DIR="/opt/sentinel-bot"
SERVICE_NAME="sentinel-bot"
REPO_URL="https://github.com/sentiox/sentinel-bot.git"

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

ok()   { printf "${GREEN}[OK]${NC} %s\n" "$1"; }
info() { printf "${BLUE}[i]${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$1"; }
err()  { printf "${RED}[X]${NC} %s\n" "$1"; }

ask() {
    printf "${WHITE}%s${NC}" "$1" > /dev/tty
    read -r ANSWER < /dev/tty
    echo "$ANSWER"
}

die() { err "$1"; exit 1; }

# === Main ===
print_banner

# Check root
if [ "$(id -u)" -ne 0 ]; then
    die "Run as root: sudo bash install.sh"
fi

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    ok "OS: $PRETTY_NAME"
else
    die "Cannot detect OS"
fi

# Install system packages
info "Installing system packages..."
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq < /dev/null >/dev/null 2>&1 || true
    apt-get install -y python3 python3-pip python3-venv python3-full git wget curl < /dev/null >/dev/null 2>&1 || true
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y python3 python3-pip git wget curl < /dev/null >/dev/null 2>&1 || true
elif command -v yum >/dev/null 2>&1; then
    yum install -y python3 python3-pip git wget curl < /dev/null >/dev/null 2>&1 || true
fi

command -v python3 >/dev/null 2>&1 || die "python3 not found!"
command -v git >/dev/null 2>&1 || die "git not found!"

PYVER=$(python3 --version 2>&1)
ok "System packages installed ($PYVER)"

# Clone repo
if [ -d "$INSTALL_DIR" ]; then
    warn "Directory $INSTALL_DIR already exists"
    REPLY=$(ask "   Overwrite? (y/n): ")
    if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
        rm -rf "$INSTALL_DIR"
    else
        die "Installation cancelled"
    fi
fi

info "Cloning repository..."
git clone -q "$REPO_URL" "$INSTALL_DIR" < /dev/null || die "Failed to clone repository"
ok "Cloned to $INSTALL_DIR"

# Create venv
info "Creating virtual environment..."
if python3 -m venv "$INSTALL_DIR/venv" < /dev/null 2>&1; then
    ok "Venv created"
else
    warn "venv failed, trying --without-pip..."
    if python3 -m venv --without-pip "$INSTALL_DIR/venv" < /dev/null 2>&1; then
        info "Downloading pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        "$INSTALL_DIR/venv/bin/python3" /tmp/get-pip.py < /dev/null 2>&1 || die "Cannot install pip"
        rm -f /tmp/get-pip.py
        ok "Venv created (fallback)"
    else
        die "Cannot create venv. Install python3-venv: apt install python3-venv"
    fi
fi

# Install pip packages
info "Installing Python packages (this may take a minute)..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip < /dev/null >/dev/null 2>&1 || true
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" < /dev/null >/dev/null 2>&1
if [ $? -ne 0 ]; then
    err "pip install failed, retrying with verbose output..."
    "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" < /dev/null 2>&1
    [ $? -ne 0 ] && die "Failed to install packages"
fi
ok "Python packages installed"

# Configure
printf "\n"
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "${WHITE}  Configuration${NC}\n"
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "\n"

printf "${YELLOW}Bot Token${NC} (get from @BotFather)\n"
BOT_TOKEN=""
while [ -z "$BOT_TOKEN" ]; do
    BOT_TOKEN=$(ask "   Token: ")
done
printf "\n"

printf "${YELLOW}Your Telegram ID${NC} (get from @userinfobot)\n"
ADMIN_ID=""
while [ -z "$ADMIN_ID" ]; do
    ADMIN_ID=$(ask "   ID: ")
done
printf "\n"

printf "${YELLOW}Mode${NC}\n"
printf "   1) Supergroup with topics (recommended)\n"
printf "   2) Private messages only\n"
MODE_CHOICE=$(ask "   Choose (1/2): ")

GROUP_ID=""
if [ "$MODE_CHOICE" = "1" ]; then
    printf "\n"
    printf "${YELLOW}Group ID${NC} (starts with -100...)\n"
    printf "   Add @getmyid_bot to your group to find it\n"
    GROUP_ID=$(ask "   Group ID: ")
fi

# Write .env
mkdir -p "$INSTALL_DIR/data"
cat > "$INSTALL_DIR/.env" << ENVEOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_ID
GROUP_ID=$GROUP_ID
TOPIC_VPS_PANEL=
TOPIC_PAYMENTS=
TOPIC_BALANCE=
TOPIC_MONITORING=
TOPIC_ADMIN=
TOPIC_BACKUP=
MONITOR_INTERVAL=300
ALERT_CPU_THRESHOLD=90
ALERT_RAM_THRESHOLD=90
ALERT_DISK_THRESHOLD=85
REMINDER_DAYS=7,3,1,0
DB_PATH=$INSTALL_DIR/data/sentinel.db
ENVEOF
ok "Configuration saved"

# Create systemd service
info "Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << SVCEOF
[Unit]
Description=Sentinel Bot
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
systemctl start "$SERVICE_NAME" || warn "Service failed to start, check: journalctl -u $SERVICE_NAME -f"
ok "Service created"

# Done
printf "\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "${GREEN}  Sentinel Bot installed!${NC}\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "\n"
printf "  ${WHITE}Commands:${NC}\n"
printf "  Logs:      ${CYAN}journalctl -u %s -f${NC}\n" "$SERVICE_NAME"
printf "  Status:    ${CYAN}systemctl status %s${NC}\n" "$SERVICE_NAME"
printf "  Restart:   ${CYAN}systemctl restart %s${NC}\n" "$SERVICE_NAME"
printf "  Stop:      ${CYAN}systemctl stop %s${NC}\n" "$SERVICE_NAME"
printf "  Config:    ${CYAN}nano %s/.env${NC}\n" "$INSTALL_DIR"
printf "  Uninstall: ${CYAN}bash %s/uninstall.sh${NC}\n" "$INSTALL_DIR"
printf "\n"
printf "  ${WHITE}Next:${NC} Open bot in Telegram -> /start\n"
printf "  ${WHITE}Then:${NC} In group -> /setup_topics\n"
printf "\n"
printf "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
