from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import db
from config import GROUP_ID, ADMIN_IDS
from keyboards.inline import (
    main_menu_kb,
    vps_panel_topic_kb,
    payments_topic_kb,
    balance_topic_kb,
    monitoring_topic_entry_kb,
    admin_topic_kb,
    backup_topic_kb,
)
from utils.telegram_safe import send_message_safe

router = Router()


async def _safe_callback_answer(callback, *args, **kwargs):
    try:
        await callback.answer(*args, **kwargs)
    except Exception:
        pass

WELCOME_TEXT = (
    "\U0001f6e1 <b>Sentinel Bot</b>\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 VPS \u0441\u0435\u0440\u0432\u0435\u0440\u0430\u043c\u0438,\n"
    "\u043c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u0438 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f.\n"
    "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0430\u0437\u0434\u0435\u043b:"
)

TOPIC_CONFIG = [
    ("vps_panel", "\U0001f5a5 \u041f\u0430\u043d\u0435\u043b\u044c VPS", "\U0001f5a5"),
    ("payments", "\U0001f4b0 \u041e\u043f\u043b\u0430\u0442\u0430 VPS", "\U0001f4b0"),
    ("balance", "\U0001f4b3 \u0411\u0430\u043b\u0430\u043d\u0441 \u042eKassa", "\U0001f4b3"),
    ("monitoring", "\U0001f4ca \u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433", "\U0001f4ca"),
    ("admin", "\u2699\ufe0f \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", "\u2699\ufe0f"),
    ("backup", "\U0001f504 \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f", "\U0001f504"),
]

# Mapping topic keys to their menu callbacks
TOPIC_MENU_MAP = {
    "vps_panel": ("menu:vps", "\U0001f5a5 <b>\u041f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f VPS</b>", vps_panel_topic_kb),
    "payments": ("menu:payments", "\U0001f4b0 <b>\u041e\u043f\u043b\u0430\u0442\u0430 VPS</b>\n\n\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430\u043c\u0438:", payments_topic_kb),
    "balance": ("menu:balance", "\U0001f4b3 <b>\u0411\u0430\u043b\u0430\u043d\u0441 \u042eKassa</b>\n\n\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0431\u0430\u043b\u0430\u043d\u0441\u043e\u043c:", balance_topic_kb),
    "monitoring": ("menu:monitoring", "\U0001f4ca <b>\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433</b>\n\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435:", monitoring_topic_entry_kb),
    "admin": ("menu:admin", "\u2699\ufe0f <b>\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438</b>", admin_topic_kb),
    "backup": ("menu:backup", "\U0001f504 <b>\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f Remnawave</b>", backup_topic_kb),
}


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not await db.is_admin(message.from_user.id):
        await message.answer("\u26d4 \u0414\u043e\u0441\u0442\u0443\u043f \u0437\u0430\u043f\u0440\u0435\u0449\u0451\u043d.")
        return
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(Command("reset_topics"))
async def cmd_reset_topics(message: Message):
    """Clear saved topic IDs so /setup_topics creates them fresh."""
    if not await db.is_admin(message.from_user.id):
        await message.answer("\u26d4 \u0414\u043e\u0441\u0442\u0443\u043f \u0437\u0430\u043f\u0440\u0435\u0449\u0451\u043d.")
        return
    for key, _, _ in TOPIC_CONFIG:
        await db.set_setting(f"topic_{key}", "")
    await message.answer(
        "\U0001f5d1 \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0442\u043e\u043f\u0438\u043a\u043e\u0432 \u0441\u0431\u0440\u043e\u0448\u0435\u043d\u044b.\n"
        "\u0422\u0435\u043f\u0435\u0440\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0438\u0442\u0435 /setup_topics \u0434\u043b\u044f \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f \u043d\u043e\u0432\u044b\u0445."
    )


@router.message(Command("setup_topics"))
async def cmd_setup_topics(message: Message):
    if not await db.is_admin(message.from_user.id):
        await message.answer("\u26d4 \u0414\u043e\u0441\u0442\u0443\u043f \u0437\u0430\u043f\u0440\u0435\u0449\u0451\u043d.")
        return

    chat_id = message.chat.id
    if chat_id > 0:
        await message.answer(
            "\u26a0\ufe0f \u042d\u0442\u0443 \u043a\u043e\u043c\u0430\u043d\u0434\u0443 \u043d\u0443\u0436\u043d\u043e \u0432\u044b\u043f\u043e\u043b\u043d\u044f\u0442\u044c \u0432 \u0441\u0443\u043f\u0435\u0440\u0433\u0440\u0443\u043f\u043f\u0435 \u0441 \u0442\u043e\u043f\u0438\u043a\u0430\u043c\u0438!"
        )
        return

    status = await message.answer("\u23f3 \u041f\u0440\u043e\u0432\u0435\u0440\u044f\u044e \u0442\u043e\u043f\u0438\u043a\u0438...")

    created = 0
    skipped = 0
    for key, name, icon in TOPIC_CONFIG:
        existing_id = await db.get_setting(f"topic_{key}")

        # If topic ID is saved, verify it's still alive by sending a test message
        if existing_id:
            try:
                test_msg = await message.bot.send_message(
                    chat_id=chat_id,
                    message_thread_id=int(existing_id),
                    text="\u2705",
                )
                await test_msg.delete()
                skipped += 1
                continue  # Topic exists and is alive, skip
            except Exception:
                # Topic is gone, clear stale ID
                await db.set_setting(f"topic_{key}", "")

        try:
            topic = await message.bot.create_forum_topic(
                chat_id=chat_id,
                name=name,
            )
            await db.set_setting(f"topic_{key}", str(topic.message_thread_id))
            created += 1

            # Send menu with buttons into each topic
            menu_info = TOPIC_MENU_MAP.get(key)
            if menu_info:
                _, menu_text, kb_func = menu_info
                kb = kb_func() if kb_func else None
                await send_message_safe(
                    message.bot,
                    chat_id=chat_id,
                    message_thread_id=topic.message_thread_id,
                    text=f"{menu_text}",
                    reply_markup=kb,
                    parse_mode="HTML",
                )
            else:
                await send_message_safe(
                    message.bot,
                    chat_id=chat_id,
                    message_thread_id=topic.message_thread_id,
                    text=f"{icon} <b>{name}</b>\n\n\u0422\u043e\u043f\u0438\u043a \u0433\u043e\u0442\u043e\u0432 \u043a \u0440\u0430\u0431\u043e\u0442\u0435!",
                    parse_mode="HTML",
                )
        except Exception as e:
            await message.answer(f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u0440\u0438 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0438 \u0442\u043e\u043f\u0438\u043a\u0430 '{name}': {e}")

    parts = []
    if created:
        parts.append(f"\u0441\u043e\u0437\u0434\u0430\u043d\u043e: {created}")
    if skipped:
        parts.append(f"\u0443\u0436\u0435 \u0431\u044b\u043b\u043e: {skipped}")

    await status.edit_text(
        f"\u2705 \u0413\u043e\u0442\u043e\u0432\u043e! \u0422\u043e\u043f\u0438\u043a\u043e\u0432 {', '.join(parts)}.\n\n"
        f"\u0411\u043e\u0442 \u0433\u043e\u0442\u043e\u0432 \u043a \u0440\u0430\u0431\u043e\u0442\u0435!"
    )

    await db.set_setting("group_id", str(chat_id))
    await db.log_action(message.from_user.id, "setup_topics", f"Created {created} topics")


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    if not await db.is_admin(message.from_user.id):
        return
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "menu:back")
async def cb_back_to_menu(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4 \u0414\u043e\u0441\u0442\u0443\u043f \u0437\u0430\u043f\u0440\u0435\u0449\u0451\u043d", show_alert=True)
        return
    if callback.message.chat.id < 0:
        await _safe_callback_answer(
            callback,
            "\u0412 \u0442\u043e\u043f\u0438\u043a\u0430\u0445 \u043a\u043d\u043e\u043f\u043a\u0430 \u00ab\u041d\u0430\u0437\u0430\u0434\u00bb \u043e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u0430. \u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e \u2014 \u0442\u043e\u043b\u044c\u043a\u043e \u0432 \u041b\u0421.",
            show_alert=True,
        )
        return
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="HTML")
    await _safe_callback_answer(callback)
