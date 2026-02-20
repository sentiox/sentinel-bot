from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards.inline import admin_kb, back_kb
from config import ADMIN_IDS

router = Router()


async def _delete_msg(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


async def _edit_bot_msg(message: Message, state: FSMContext, text: str, **kwargs):
    """Delete user message and edit the stored bot message."""
    await _delete_msg(message)
    data = await state.get_data()
    bot_msg_id = data.get("_bot_msg_id")
    if bot_msg_id:
        try:
            await message.bot.edit_message_text(
                text=text, chat_id=message.chat.id, message_id=bot_msg_id, **kwargs
            )
            return
        except Exception:
            pass
    msg = await message.answer(text, **kwargs)
    await state.update_data(_bot_msg_id=msg.message_id)


async def _safe_callback_answer(callback, *args, **kwargs):
    try:
        await callback.answer(*args, **kwargs)
    except Exception:
        pass


class AddAdminFSM(StatesGroup):
    telegram_id = State()


# === Admin Menu ===

@router.callback_query(F.data == "menu:admin")
async def cb_admin(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    await callback.message.edit_text(
        "\u2699\ufe0f <b>\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0438 \u0430\u0434\u043c\u0438\u043d\u043a\u0430</b>",
        reply_markup=admin_kb(),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


# === Admin List ===

@router.callback_query(F.data == "adm:list")
async def cb_admin_list(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    admins = await db.get_admins()
    text = "\U0001f465 <b>\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u044b</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"

    text += "<b>\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435 (.env):</b>\n"
    for aid in ADMIN_IDS:
        text += f"  \U0001f451 <code>{aid}</code>\n"

    if admins:
        text += "\n<b>\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0435:</b>\n"
        for a in admins:
            username = f" (@{a['username']})" if a["username"] else ""
            text += f"  \U0001f464 <code>{a['telegram_id']}</code>{username}\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for a in admins:
        buttons.append([InlineKeyboardButton(
            text=f"\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c {a['telegram_id']}",
            callback_data=f"adm:remove:{a['telegram_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:admin")])

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)


# === Add Admin ===

@router.callback_query(F.data == "adm:add")
async def cb_add_admin(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await _safe_callback_answer(callback, "\u26d4 \u0422\u043e\u043b\u044c\u043a\u043e \u0433\u043b\u0430\u0432\u043d\u044b\u0439 \u0430\u0434\u043c\u0438\u043d", show_alert=True)
        return

    await callback.message.edit_text(
        "\u2795 <b>\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0430\u0434\u043c\u0438\u043d\u0430</b>\n\n"
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 Telegram ID \u043d\u043e\u0432\u043e\u0433\u043e \u0430\u0434\u043c\u0438\u043d\u0430:\n"
        "(\u0443\u0437\u043d\u0430\u0442\u044c \u043c\u043e\u0436\u043d\u043e \u0443 @userinfobot)",
        parse_mode="HTML",
    )
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await state.set_state(AddAdminFSM.telegram_id)
    await _safe_callback_answer(callback)


@router.message(AddAdminFSM.telegram_id)
async def fsm_add_admin(message: Message, state: FSMContext):
    try:
        tid = int(message.text.strip())
    except ValueError:
        await _delete_msg(message)
        return

    await db.add_admin(tid)
    await _edit_bot_msg(message, state,
        f"\u2705 \u0410\u0434\u043c\u0438\u043d <code>{tid}</code> \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d!",
        reply_markup=back_kb("adm:list"),
        parse_mode="HTML",
    )
    await db.log_action(message.from_user.id, "add_admin", str(tid))
    await state.clear()


# === Remove Admin ===

@router.callback_query(F.data.startswith("adm:remove:"))
async def cb_remove_admin(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await _safe_callback_answer(callback, "\u26d4 \u0422\u043e\u043b\u044c\u043a\u043e \u0433\u043b\u0430\u0432\u043d\u044b\u0439 \u0430\u0434\u043c\u0438\u043d", show_alert=True)
        return

    tid = int(callback.data.split(":")[2])
    await db.remove_admin(tid)
    await callback.message.edit_text(
        f"\u2705 \u0410\u0434\u043c\u0438\u043d <code>{tid}</code> \u0443\u0434\u0430\u043b\u0451\u043d.",
        reply_markup=back_kb("adm:list"),
        parse_mode="HTML",
    )
    await db.log_action(callback.from_user.id, "remove_admin", str(tid))
    await _safe_callback_answer(callback)


# === Notifications Settings ===

@router.callback_query(F.data == "adm:notifications")
async def cb_notifications(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    monitor_enabled = await db.get_setting("monitor_enabled", "1")
    payment_enabled = await db.get_setting("payment_notify_enabled", "1")

    mon_status = "\U0001f7e2 \u0412\u043a\u043b" if monitor_enabled == "1" else "\U0001f534 \u0412\u044b\u043a\u043b"
    pay_status = "\U0001f7e2 \u0412\u043a\u043b" if payment_enabled == "1" else "\U0001f534 \u0412\u044b\u043a\u043b"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"\U0001f4ca \u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433: {mon_status}",
            callback_data="adm:toggle:monitor_enabled"
        )],
        [InlineKeyboardButton(
            text=f"\U0001f4b0 \u041e\u043f\u043b\u0430\u0442\u0430: {pay_status}",
            callback_data="adm:toggle:payment_notify_enabled"
        )],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:admin")],
    ])

    await callback.message.edit_text(
        "\U0001f514 <b>\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u0439</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("adm:toggle:"))
async def cb_toggle_setting(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    key = callback.data.split(":")[2]
    current = await db.get_setting(key, "1")
    new_val = "0" if current == "1" else "1"
    await db.set_setting(key, new_val)

    await db.log_action(callback.from_user.id, f"toggle_{key}", new_val)
    await cb_notifications(callback)


# === Action Logs ===

@router.callback_query(F.data == "adm:logs")
async def cb_logs(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    logs = await db.get_logs(limit=20)
    if not logs:
        await callback.message.edit_text(
            "\U0001f4cb <b>\u041b\u043e\u0433\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439</b>\n\n\u041f\u0443\u0441\u0442\u043e.",
            reply_markup=back_kb("menu:admin"),
            parse_mode="HTML",
        )
        await _safe_callback_answer(callback)
        return

    text = "\U0001f4cb <b>\u041b\u043e\u0433\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    for log in logs:
        details = f" ({log['details']})" if log["details"] else ""
        text += f"\U0001f4cc {log['action']}{details}\n   \U0001f464 {log['admin_id']} \u2022 {log['created_at'][:16]}\n\n"

    await callback.message.edit_text(
        text, reply_markup=back_kb("menu:admin"), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)


# === Export ===

@router.callback_query(F.data == "adm:export")
async def cb_export(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    servers = await db.get_servers()
    payments = await db.get_payments(active_only=False)
    balance = await db.get_balance()

    text = (
        "\U0001f4e4 <b>\u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0434\u0430\u043d\u043d\u044b\u0445</b>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        f"\U0001f5a5 \u0421\u0435\u0440\u0432\u0435\u0440\u043e\u0432: {len(list(servers))}\n"
        f"\U0001f4b0 \u041f\u043b\u0430\u0442\u0435\u0436\u0435\u0439: {len(list(payments))}\n"
        f"\U0001f4b3 \u0411\u0430\u043b\u0430\u043d\u0441: {balance:.2f}\u20bd\n"
    )

    await callback.message.edit_text(
        text, reply_markup=back_kb("menu:admin"), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)
