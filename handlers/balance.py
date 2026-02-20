from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ForceReply
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards.inline import balance_kb, balance_topic_kb, back_kb
from utils.telegram_safe import edit_message_text_safe
from utils.formatters import format_balance_report, format_money

router = Router()


class BalanceOpFSM(StatesGroup):
    op_type = State()
    amount = State()
    description = State()


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
            await edit_message_text_safe(
                message.bot,
                text=text, chat_id=message.chat.id, message_id=bot_msg_id, **kwargs
            )
            return
        except Exception:
            pass
    msg = await message.answer(text, **kwargs)
    await state.update_data(_bot_msg_id=msg.message_id)


async def _safe_callback_answer(callback: CallbackQuery, *args, **kwargs):
    try:
        await callback.answer(*args, **kwargs)
    except Exception:
        pass


def _topic_force_reply(chat_id: int):
    if chat_id < 0:
        return ForceReply(selective=True)
    return None


# === Balance Menu ===

@router.callback_query(F.data == "menu:balance")
async def cb_balance(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    balance = await db.get_balance()
    await callback.message.edit_text(
        f"\U0001f4b3 <b>\u0411\u0430\u043b\u0430\u043d\u0441 \u042eKassa</b>\n\n"
        f"\U0001f4b0 \u0411\u0430\u043b\u0430\u043d\u0441: <b>{format_money(balance)}</b>\n\n"
        f"\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0431\u0430\u043b\u0430\u043d\u0441\u043e\u043c:",
        reply_markup=balance_topic_kb() if callback.message.chat.id < 0 else balance_kb(),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


# === Show Balance ===

@router.callback_query(F.data == "bal:show")
async def cb_show_balance(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    balance = await db.get_balance()
    history = await db.get_balance_history(limit=10)
    text = format_balance_report(balance, list(history) if history else None)

    await callback.message.edit_text(
        text, reply_markup=back_kb("menu:balance"), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)


# === Income / Expense / Payment ===

@router.callback_query(F.data.in_({"bal:income", "bal:expense", "bal:payment"}))
async def cb_balance_operation(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    op_map = {
        "bal:income": ("income", "\U0001f4e5 \u041f\u043e\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435"),
        "bal:expense": ("expense", "\U0001f4e4 \u0421\u043f\u0438\u0441\u0430\u043d\u0438\u0435"),
        "bal:payment": ("payment", "\U0001f9fe \u041e\u043f\u043b\u0430\u0442\u0430"),
    }
    op_type, op_name = op_map[callback.data]
    await state.update_data(op_type=op_type, op_name=op_name, _bot_msg_id=callback.message.message_id)
    await state.set_state(BalanceOpFSM.amount)

    await callback.message.edit_text(
        f"{op_name}\n\n\U0001f4b5 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443 (\u0432 \u0440\u0443\u0431\u043b\u044f\u0445):",
        reply_markup=_topic_force_reply(callback.message.chat.id),
    )
    await _safe_callback_answer(callback)


@router.message(BalanceOpFSM.amount)
async def fsm_balance_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await _delete_msg(message)
        return

    if amount <= 0:
        await _delete_msg(message)
        return

    await state.update_data(amount=amount)
    await _edit_bot_msg(message, state,
        "\U0001f4dd \u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 (\u0438\u043b\u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 - \u0434\u043b\u044f \u043f\u0440\u043e\u043f\u0443\u0441\u043a\u0430):",
        reply_markup=_topic_force_reply(message.chat.id))
    await state.set_state(BalanceOpFSM.description)


@router.message(BalanceOpFSM.description)
async def fsm_balance_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    desc = message.text.strip() if message.text.strip() != "-" else None

    balance_before, balance_after = await db.add_balance_operation(
        operation_type=data["op_type"],
        amount=data["amount"],
        description=desc,
    )

    op_name = data.get("op_name", data["op_type"])
    text = (
        f"\u2705 <b>{op_name}</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4b0 \u0411\u044b\u043b\u043e: {format_money(balance_before)}\n"
        f"\U0001f4b5 \u0421\u0443\u043c\u043c\u0430: {format_money(data['amount'])}\n"
        f"\u2705 \u0421\u0442\u0430\u043b\u043e: <b>{format_money(balance_after)}</b>\n"
    )
    if desc:
        text += f"\U0001f4dd {desc}\n"

    await _edit_bot_msg(message, state, text, reply_markup=back_kb("menu:balance"), parse_mode="HTML")
    await db.log_action(
        message.from_user.id, f"balance_{data['op_type']}", f"{data['amount']} - {desc}"
    )
    await state.clear()


# === History ===

@router.callback_query(F.data == "bal:history")
async def cb_balance_history(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    history = await db.get_balance_history(limit=15)
    if not history:
        await callback.message.edit_text(
            "\U0001f4dc <b>\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0439</b>\n\n\u041f\u0443\u0441\u0442\u043e.",
            reply_markup=back_kb("menu:balance"),
            parse_mode="HTML",
        )
        await _safe_callback_answer(callback)
        return

    op_icons = {"income": "\U0001f4e5", "expense": "\U0001f4e4", "payment": "\U0001f9fe"}
    text = "\U0001f4dc <b>\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043e\u043f\u0435\u0440\u0430\u0446\u0438\u0439</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"

    for h in history:
        icon = op_icons.get(h["operation_type"], "\U0001f4b0")
        desc = h["description"] or ""
        text += f"{icon} {format_money(h['amount'])} \u2192 {format_money(h['balance_after'])}"
        if desc:
            text += f" ({desc})"
        text += f"\n   {h['created_at'][:16]}\n\n"

    await callback.message.edit_text(
        text, reply_markup=back_kb("menu:balance"), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)
