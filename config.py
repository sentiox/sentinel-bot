import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
GROUP_ID = int(os.getenv("GROUP_ID", "0")) if os.getenv("GROUP_ID") else 0

TOPIC_IDS = {
    "vps_panel": int(os.getenv("TOPIC_VPS_PANEL", "0") or "0"),
    "payments": int(os.getenv("TOPIC_PAYMENTS", "0") or "0"),
    "balance": int(os.getenv("TOPIC_BALANCE", "0") or "0"),
    "monitoring": int(os.getenv("TOPIC_MONITORING", "0") or "0"),
    "admin": int(os.getenv("TOPIC_ADMIN", "0") or "0"),
    "backup": int(os.getenv("TOPIC_BACKUP", "0") or "0"),
}

MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "300"))
ALERT_CPU_THRESHOLD = int(os.getenv("ALERT_CPU_THRESHOLD", "90"))
ALERT_RAM_THRESHOLD = int(os.getenv("ALERT_RAM_THRESHOLD", "90"))
ALERT_DISK_THRESHOLD = int(os.getenv("ALERT_DISK_THRESHOLD", "85"))

REMINDER_DAYS = [int(x.strip()) for x in os.getenv("REMINDER_DAYS", "7,3,1,0").split(",")]

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "sentinel.db"))
