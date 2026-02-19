#!/bin/bash

# ============================================
#  Sentinel Bot — Installer
#  https://github.com/sentiox/sentinel-bot
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

INSTALL_DIR="/opt/sentinel-bot"
SERVICE_NAME="sentinel-bot"
REPO_URL="https://github.com/sentiox/sentinel-bot.git"

print_banner() {
    echo -e "${CYAN}"
    echo "  ╔═══════════════════════════════════════════╗"
    echo "  ║                                           ║"
    echo "  ║   🛡  Sentinel Bot — Installer            ║"
    echo "  ║   VPS Management & Monitoring             ║"
    echo "  ║                                           ║"
    echo "  ╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Запустите скрипт от root: sudo bash install.sh"
        exit 1
    fi
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        print_step "Обнаружена ОС: $PRETTY_NAME"
    else
        print_error "Не удалось определить ОС. Поддерживается Ubuntu/Debian."
        exit 1
    fi

    if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
        print_warn "ОС $OS не тестировалась. Продолжаем..."
    fi
}

install_dependencies() {
    print_info "Устанавливаем зависимости..."
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv git wget curl > /dev/null 2>&1
    print_step "Зависимости установлены"

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_step "Python: $PYTHON_VERSION"
}

clone_repo() {
    if [ -d "$INSTALL_DIR" ]; then
        print_warn "Директория $INSTALL_DIR уже существует"
        read -p "$(echo -e "${YELLOW}Перезаписать? (y/n): ${NC}")" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            print_error "Установка отменена"
            exit 1
        fi
    fi

    print_info "Клонируем репозиторий..."
    git clone -q "$REPO_URL" "$INSTALL_DIR"
    print_step "Репозиторий склонирован в $INSTALL_DIR"
}

setup_venv() {
    print_info "Создаём виртуальное окружение..."
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    pip install --upgrade pip -q
    pip install -r "$INSTALL_DIR/requirements.txt" -q
    deactivate
    print_step "Виртуальное окружение готово"
}

configure_bot() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}  ⚙️  Настройка бота${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Bot Token
    echo -e "${YELLOW}🤖 Bot Token${NC}"
    echo -e "   Получить у @BotFather в Telegram:"
    echo -e "   1. Откройте @BotFather"
    echo -e "   2. Отправьте /newbot"
    echo -e "   3. Следуйте инструкциям"
    echo -e "   4. Скопируйте токен"
    echo ""
    read -p "$(echo -e "${WHITE}   Введите Bot Token: ${NC}")" BOT_TOKEN

    while [ -z "$BOT_TOKEN" ]; do
        print_error "   Token не может быть пустым!"
        read -p "$(echo -e "${WHITE}   Введите Bot Token: ${NC}")" BOT_TOKEN
    done
    echo ""

    # Admin ID
    echo -e "${YELLOW}👤 Ваш Telegram ID (Администратор)${NC}"
    echo -e "   Узнать у @userinfobot или @getmyid_bot"
    echo ""
    read -p "$(echo -e "${WHITE}   Введите Telegram ID: ${NC}")" ADMIN_ID

    while [ -z "$ADMIN_ID" ]; do
        print_error "   ID не может быть пустым!"
        read -p "$(echo -e "${WHITE}   Введите Telegram ID: ${NC}")" ADMIN_ID
    done
    echo ""

    # Group or Private
    echo -e "${YELLOW}💬 Режим работы${NC}"
    echo -e "   1) Супергруппа с топиками (рекомендуется)"
    echo -e "   2) Личные сообщения (ЛС)"
    echo ""
    read -p "$(echo -e "${WHITE}   Выберите (1/2): ${NC}")" MODE_CHOICE

    GROUP_ID=""
    if [ "$MODE_CHOICE" = "1" ]; then
        echo ""
        echo -e "${YELLOW}💬 ID Супергруппы${NC}"
        echo -e "   Как узнать Group ID:"
        echo -e "   1. Создайте супергруппу в Telegram"
        echo -e "   2. Включите 'Темы' в настройках группы"
        echo -e "   3. Добавьте бота как администратора"
        echo -e "   4. Добавьте @getmyid_bot в группу"
        echo -e "   5. ID начинается с -100..."
        echo ""
        read -p "$(echo -e "${WHITE}   Введите Group ID: ${NC}")" GROUP_ID
    fi
    echo ""

    # Generate .env
    cat > "$INSTALL_DIR/.env" << EOF
# Sentinel Bot Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

# Telegram Bot
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_ID
GROUP_ID=$GROUP_ID

# Topic IDs (will be auto-created by /setup_topics command)
TOPIC_VPS_PANEL=
TOPIC_PAYMENTS=
TOPIC_BALANCE=
TOPIC_MONITORING=
TOPIC_ADMIN=
TOPIC_BACKUP=

# Monitoring Settings
MONITOR_INTERVAL=300
ALERT_CPU_THRESHOLD=90
ALERT_RAM_THRESHOLD=90
ALERT_DISK_THRESHOLD=85

# Payment Reminder Days
REMINDER_DAYS=7,3,1,0

# Database
DB_PATH=$INSTALL_DIR/data/sentinel.db
EOF

    mkdir -p "$INSTALL_DIR/data"
    print_step "Конфигурация сохранена"
}

create_service() {
    print_info "Создаём systemd сервис..."

    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
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
EOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
    systemctl start "$SERVICE_NAME"
    print_step "Сервис создан и запущен"
}

print_finish() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ Sentinel Bot успешно установлен!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${WHITE}📋 Полезные команды:${NC}"
    echo -e "  ${CYAN}Логи:${NC}      journalctl -u $SERVICE_NAME -f"
    echo -e "  ${CYAN}Статус:${NC}    systemctl status $SERVICE_NAME"
    echo -e "  ${CYAN}Рестарт:${NC}   systemctl restart $SERVICE_NAME"
    echo -e "  ${CYAN}Стоп:${NC}      systemctl stop $SERVICE_NAME"
    echo -e "  ${CYAN}Конфиг:${NC}    nano $INSTALL_DIR/.env"
    echo -e "  ${CYAN}Удалить:${NC}   bash $INSTALL_DIR/uninstall.sh"
    echo ""
    echo -e "  ${WHITE}🚀 Следующие шаги:${NC}"
    echo -e "  1. Откройте бота в Telegram"
    echo -e "  2. Отправьте /start"
    echo -e "  3. В группе отправьте /setup_topics"
    echo -e "     (бот создаст все топики автоматически)"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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
