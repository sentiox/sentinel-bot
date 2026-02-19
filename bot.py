import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, GROUP_ID, ADMIN_IDS
from database import db
from handlers import get_all_routers
from services.scheduler import init_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel")


async def on_startup(bot: Bot):
    await db.connect()
    logger.info("Database connected")

    # Add admins from config
    for aid in ADMIN_IDS:
        await db.add_admin(aid)

    # Load topic IDs from database
    topic_ids = {}
    for key in ["vps_panel", "payments", "balance", "monitoring", "admin", "backup"]:
        val = await db.get_setting(f"topic_{key}")
        if val:
            topic_ids[key] = int(val)

    init_scheduler(bot, topic_ids)
    logger.info("Scheduler initialized")

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} ({me.id})")

    # Notify admins
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                "\U0001f6e1 <b>Sentinel Bot \u0437\u0430\u043f\u0443\u0449\u0435\u043d!</b>\n\n"
                "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /start \u0434\u043b\u044f \u043d\u0430\u0447\u0430\u043b\u0430 \u0440\u0430\u0431\u043e\u0442\u044b.",
                parse_mode="HTML",
            )
        except Exception:
            pass


async def on_shutdown(bot: Bot):
    await db.close()
    logger.info("Bot stopped")


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Check .env file.")
        sys.exit(1)

    Path("data").mkdir(exist_ok=True)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    for router in get_all_routers():
        dp.include_router(router)

    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
