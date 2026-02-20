import asyncio
import logging
from typing import Any

from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter

logger = logging.getLogger(__name__)


async def send_message_safe(bot, *args: Any, **kwargs: Any):
    """Send Telegram message with retry for flood/network errors."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return await bot.send_message(*args, **kwargs)
        except TelegramRetryAfter as e:
            # Telegram explicitly tells how many seconds to wait.
            wait_for = float(getattr(e, "retry_after", 1)) + 0.2
            logger.warning("Flood control hit. Sleeping %.1fs before retry", wait_for)
            await asyncio.sleep(wait_for)
        except TelegramNetworkError:
            if attempt >= 3:
                raise
            await asyncio.sleep(0.7 * attempt)
