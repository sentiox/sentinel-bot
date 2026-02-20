import asyncio
import logging
from typing import Any

from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.types import Message

logger = logging.getLogger(__name__)
_PATCHED_MESSAGE_EDIT = False


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


async def edit_message_text_safe(bot, *args: Any, **kwargs: Any):
    """Edit Telegram message with retry for flood/network errors."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return await bot.edit_message_text(*args, **kwargs)
        except TelegramRetryAfter as e:
            wait_for = float(getattr(e, "retry_after", 1)) + 0.2
            logger.warning("Flood control hit on edit. Sleeping %.1fs before retry", wait_for)
            await asyncio.sleep(wait_for)
        except TelegramNetworkError:
            if attempt >= 3:
                raise
            await asyncio.sleep(0.7 * attempt)


def patch_aiogram_message_edit_text() -> None:
    """Patch Message.edit_text globally to auto-retry on flood/network errors."""
    global _PATCHED_MESSAGE_EDIT
    if _PATCHED_MESSAGE_EDIT:
        return

    original_edit_text = Message.edit_text

    async def _edit_text_with_retry(self, *args: Any, **kwargs: Any):
        attempt = 0
        while True:
            attempt += 1
            try:
                return await original_edit_text(self, *args, **kwargs)
            except TelegramRetryAfter as e:
                wait_for = float(getattr(e, "retry_after", 1)) + 0.2
                logger.warning("Flood control hit on Message.edit_text. Sleeping %.1fs before retry", wait_for)
                await asyncio.sleep(wait_for)
            except TelegramNetworkError:
                if attempt >= 3:
                    raise
                await asyncio.sleep(0.7 * attempt)

    Message.edit_text = _edit_text_with_retry
    _PATCHED_MESSAGE_EDIT = True
