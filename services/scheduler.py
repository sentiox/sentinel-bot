import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import MONITOR_INTERVAL, REMINDER_DAYS, GROUP_ID
from database import db
from services.monitoring_service import monitoring_service
from utils.formatters import format_server_status, format_payment_reminder

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

_bot = None
_topic_ids = {}


def init_scheduler(bot, topic_ids: dict):
    global _bot, _topic_ids
    _bot = bot
    _topic_ids = topic_ids

    scheduler.add_job(
        monitoring_job,
        "interval",
        seconds=MONITOR_INTERVAL,
        id="monitoring",
        replace_existing=True,
    )

    scheduler.add_job(
        payment_reminder_job,
        "cron",
        hour=9,
        minute=0,
        id="payment_reminders",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")


async def monitoring_job():
    if not _bot or not GROUP_ID:
        return

    topic_id = _topic_ids.get("monitoring")
    results = await monitoring_service.collect_all()
    servers = await db.get_servers()

    for server in servers:
        sid = server["id"]
        metrics = results.get(sid)
        server_dict = dict(server)

        if metrics:
            alerts = monitoring_service.check_alerts(sid, server["name"], metrics)
            for alert_text in alerts:
                try:
                    await _bot.send_message(
                        chat_id=GROUP_ID,
                        message_thread_id=topic_id,
                        text=alert_text,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.error(f"Failed to send alert: {e}")


async def payment_reminder_job():
    if not _bot or not GROUP_ID:
        return

    topic_id = _topic_ids.get("payments")
    payments = await db.get_payments(active_only=True)
    today = datetime.now().date()

    for payment in payments:
        due = datetime.strptime(payment["due_date"], "%Y-%m-%d").date()
        days_left = (due - today).days
        notified = payment["notified_days"] or ""
        notified_list = [x.strip() for x in notified.split(",") if x.strip()]

        if days_left in REMINDER_DAYS and str(days_left) not in notified_list:
            text = format_payment_reminder(dict(payment), days_left)
            try:
                await _bot.send_message(
                    chat_id=GROUP_ID,
                    message_thread_id=topic_id,
                    text=text,
                    parse_mode="HTML",
                )
                notified_list.append(str(days_left))
                await db.update_payment_notified(
                    payment["id"], ",".join(notified_list)
                )
            except Exception as e:
                logger.error(f"Failed to send payment reminder: {e}")
