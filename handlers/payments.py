from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards.inline import payments_kb, back_kb, confirm_kb
from utils.formatters import format_money, format_payment_reminder

router = Router()


class AddPaymentFSM(StatesGroup):
    server = State()
    description = State()
    amount = State()
    due_date = State()


class EditPaymentFSM(StatesGroup):
    new_date = State()
    payment_id = State()


# === Payments Menu ===

@router.callback_query(F.data == "menu:payments")
async def cb_payments(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return
    await callback.message.edit_text(
        "\U0001f4b0 <b>\u041e\u043f\u043b\u0430\u0442\u0430 VPS</b>\n\n"
        "\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430\u043c\u0438 \u0438 \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u044f\u043c\u0438:",
        reply_markup=payments_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# === Payment List ===

@router.callback_query(F.data == "pay:list")
async def cb_payment_list(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    payments = await db.get_payments(active_only=True)
    if not payments:
        await callback.message.edit_text(
            "\U0001f4b0 <b>\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438</b>\n\n\u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439.",
            reply_markup=back_kb("menu:payments"),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    today = datetime.now().date()
    text = "\U0001f4b0 <b>\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"

    buttons = []
    for p in payments:
        due = datetime.strptime(p["due_date"], "%Y-%m-%d").date()
        days_left = (due - today).days
        if days_left < 0:
            icon = "\U0001f534"
            days_str = f"\u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e {abs(days_left)}\u0434"
        elif days_left == 0:
            icon = "\U0001f534"
            days_str = "\u0421\u0415\u0413\u041e\u0414\u041d\u042f"
        elif days_left <= 3:
            icon = "\U0001f7e1"
            days_str = f"\u0447\u0435\u0440\u0435\u0437 {days_left}\u0434"
        elif days_left <= 7:
            icon = "\U0001f7e0"
            days_str = f"\u0447\u0435\u0440\u0435\u0437 {days_left}\u0434"
        else:
            icon = "\U0001f7e2"
            days_str = f"\u0447\u0435\u0440\u0435\u0437 {days_left}\u0434"

        server_name = p["server_name"] or ""
        text += f"{icon} <b>{p['description']}</b>\n"
        text += f"   \U0001f5a5 {server_name} \u2022 {format_money(p['amount'])} \u2022 {days_str}\n"
        text += f"   \U0001f4c5 {p['due_date']}\n\n"

        buttons.append([InlineKeyboardButton(
            text=f"{icon} {p['description']} \u2014 {days_str}",
            callback_data=f"pay:view:{p['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:payments")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


# === View Payment ===

@router.callback_query(F.data.startswith("pay:view:"))
async def cb_payment_view(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await db.get_payment(payment_id)
    if not payment:
        await callback.answer("\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    today = datetime.now().date()
    due = datetime.strptime(payment["due_date"], "%Y-%m-%d").date()
    days_left = (due - today).days

    text = format_payment_reminder(dict(payment), days_left)

    # Enhanced action buttons
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2705 \u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e?", callback_data=f"pay:confirm_paid:{payment_id}")],
        [InlineKeyboardButton(text="\u270f\ufe0f \u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0434\u0430\u0442\u0443", callback_data=f"pay:edit_date:{payment_id}"),
         InlineKeyboardButton(text="\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c", callback_data=f"pay:del:{payment_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="pay:list")],
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# === Confirm Paid — asks "Вы оплатили? На сколько дней?" ===

@router.callback_query(F.data.startswith("pay:confirm_paid:"))
async def cb_confirm_paid(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await db.get_payment(payment_id)
    if not payment:
        await callback.answer("\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    text = (
        f"\u2705 <b>\u0412\u044b \u043e\u043f\u043b\u0430\u0442\u0438\u043b\u0438?</b>\n\n"
        f"\U0001f4cb {payment['description']}\n"
        f"\U0001f4b5 {format_money(payment['amount'])}\n\n"
        f"\u041d\u0430 \u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0434\u043d\u0435\u0439 \u043f\u0440\u043e\u0434\u043b\u0435\u0432\u0430\u0435\u0442\u0435?"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f7e2 30 \u0434\u043d\u0435\u0439", callback_data=f"pay:renew:30:{payment_id}"),
            InlineKeyboardButton(text="\U0001f535 60 \u0434\u043d\u0435\u0439", callback_data=f"pay:renew:60:{payment_id}"),
        ],
        [
            InlineKeyboardButton(text="\U0001f7e1 90 \u0434\u043d\u0435\u0439", callback_data=f"pay:renew:90:{payment_id}"),
            InlineKeyboardButton(text="\U0001f7e0 180 \u0434\u043d\u0435\u0439", callback_data=f"pay:renew:180:{payment_id}"),
        ],
        [
            InlineKeyboardButton(text="\U0001f534 360 \u0434\u043d\u0435\u0439", callback_data=f"pay:renew:360:{payment_id}"),
        ],
        [InlineKeyboardButton(text="\u274c \u041d\u0435\u0442, \u043e\u0442\u043c\u0435\u043d\u0430", callback_data=f"pay:view:{payment_id}")],
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# === Renew Payment — set new due date ===

@router.callback_query(F.data.startswith("pay:renew:"))
async def cb_renew_payment(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    parts = callback.data.split(":")
    days = int(parts[2])
    payment_id = int(parts[3])

    payment = await db.get_payment(payment_id)
    if not payment:
        await callback.answer("\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    # New due date = today + days
    new_due = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    new_due_display = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")

    await db.update_payment_notified(payment_id, "")  # Reset notifications
    await db._conn.execute(
        "UPDATE payments SET due_date = ?, is_paid = 0, notified_days = '' WHERE id = ?",
        (new_due, payment_id)
    )
    await db._conn.commit()

    text = (
        f"\u2705 <b>\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e \u0438 \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u043e!</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
        f"\U0001f4cb {payment['description']}\n"
        f"\U0001f4b5 {format_money(payment['amount'])}\n"
        f"\U0001f4c5 \u041d\u043e\u0432\u0430\u044f \u0434\u0430\u0442\u0430: <b>{new_due_display}</b>\n"
        f"\u23f3 \u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: <b>{days} \u0434\u043d\u0435\u0439</b>\n\n"
        f"\u041d\u0435 \u0442\u043e\u0442 \u0441\u0440\u043e\u043a? \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u270f\ufe0f \u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0434\u0430\u0442\u0443/\u0434\u043d\u0438", callback_data=f"pay:edit_date:{payment_id}")],
        [InlineKeyboardButton(text="\u2705 \u0412\u0441\u0451 \u0432\u0435\u0440\u043d\u043e", callback_data="pay:list")],
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await db.log_action(callback.from_user.id, "renew_payment", f"{payment['description']} +{days}d")
    await callback.answer()


# === Edit Payment Date ===

@router.callback_query(F.data.startswith("pay:edit_date:"))
async def cb_edit_date(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[2])
    await state.update_data(edit_payment_id=payment_id)
    await state.set_state(EditPaymentFSM.new_date)

    await callback.message.edit_text(
        "\u270f\ufe0f <b>\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0434\u0430\u0442\u0443 \u043e\u043f\u043b\u0430\u0442\u044b</b>\n\n"
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u0432\u0443\u044e \u0434\u0430\u0442\u0443 \u0438\u043b\u0438 \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0434\u043d\u0435\u0439:\n\n"
        "\u2022 \u0414\u0430\u0442\u0430: <b>DD.MM.YYYY</b> (\u043d\u0430\u043f\u0440. 15.03.2026)\n"
        "\u2022 \u0414\u043d\u0438: <b>+30</b> (\u043f\u0440\u0438\u0431\u0430\u0432\u0438\u0442 30 \u0434\u043d\u0435\u0439 \u043e\u0442 \u0441\u0435\u0433\u043e\u0434\u043d\u044f)\n\n"
        "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /cancel \u0434\u043b\u044f \u043e\u0442\u043c\u0435\u043d\u044b.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EditPaymentFSM.new_date)
async def fsm_edit_date(message: Message, state: FSMContext):
    if message.text == "/cancel":
        data = await state.get_data()
        pid = data.get("edit_payment_id", 0)
        await state.clear()
        await message.answer("\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e.", reply_markup=back_kb(f"pay:view:{pid}"))
        return

    data = await state.get_data()
    payment_id = data.get("edit_payment_id")
    text = message.text.strip()

    # Check if it's +days format
    if text.startswith("+") and text[1:].isdigit():
        days = int(text[1:])
        new_due = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        new_due_display = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
    else:
        # Try date format
        try:
            parsed = datetime.strptime(text, "%d.%m.%Y")
            new_due = parsed.strftime("%Y-%m-%d")
            new_due_display = text
        except ValueError:
            await message.answer(
                "\u274c \u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442!\n"
                "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435: <b>DD.MM.YYYY</b> \u0438\u043b\u0438 <b>+30</b>",
                parse_mode="HTML",
            )
            return

    await db._conn.execute(
        "UPDATE payments SET due_date = ?, notified_days = '' WHERE id = ?",
        (new_due, payment_id)
    )
    await db._conn.commit()

    today = datetime.now().date()
    due = datetime.strptime(new_due, "%Y-%m-%d").date()
    days_left = (due - today).days

    await message.answer(
        f"\u2705 <b>\u0414\u0430\u0442\u0430 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0430!</b>\n\n"
        f"\U0001f4c5 \u041d\u043e\u0432\u0430\u044f \u0434\u0430\u0442\u0430: <b>{new_due_display}</b>\n"
        f"\u23f3 \u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: <b>{days_left} \u0434\u043d\u0435\u0439</b>",
        reply_markup=back_kb(f"pay:view:{payment_id}"),
        parse_mode="HTML",
    )
    await db.log_action(message.from_user.id, "edit_payment_date", f"id={payment_id} -> {new_due}")
    await state.clear()


# === Delete Payment ===

@router.callback_query(F.data.startswith("pay:del:"))
async def cb_delete_payment(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return
    payment_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043b\u0430\u0442\u0451\u0436?",
        reply_markup=confirm_kb("del_pay", payment_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:del_pay:"))
async def cb_confirm_del_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[2])
    await db.mark_paid(payment_id)
    await callback.message.edit_text(
        "\u2705 \u041f\u043b\u0430\u0442\u0451\u0436 \u0443\u0434\u0430\u043b\u0451\u043d.",
        reply_markup=back_kb("pay:list"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:del_pay:"))
async def cb_cancel_del_payment(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e.",
        reply_markup=back_kb(f"pay:view:{payment_id}"),
    )
    await callback.answer()


# === Add Payment ===

@router.callback_query(F.data == "pay:add")
async def cb_add_payment(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    servers = await db.get_servers()
    if not servers:
        await callback.message.edit_text(
            "\u26a0\ufe0f \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0434\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440!",
            reply_markup=back_kb("menu:payments"),
        )
        await callback.answer()
        return

    buttons = [[InlineKeyboardButton(
        text=f"\U0001f5a5 {s['name']}",
        callback_data=f"pay:srv:{s['id']}"
    )] for s in servers]
    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="menu:payments")])

    await callback.message.edit_text(
        "\u2795 <b>\u041d\u043e\u0432\u044b\u0439 \u043f\u043b\u0430\u0442\u0451\u0436</b>\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await state.set_state(AddPaymentFSM.server)
    await callback.answer()


@router.callback_query(F.data.startswith("pay:srv:"), AddPaymentFSM.server)
async def fsm_payment_server(callback: CallbackQuery, state: FSMContext):
    server_id = int(callback.data.split(":")[2])
    await state.update_data(server_id=server_id)
    await callback.message.edit_text(
        "\U0001f4dd \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430:\n"
        "(\u043d\u0430\u043f\u0440. \"\u0410\u0440\u0435\u043d\u0434\u0430 VPS Hetzner\")"
    )
    await state.set_state(AddPaymentFSM.description)
    await callback.answer()


@router.message(AddPaymentFSM.description)
async def fsm_payment_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("\U0001f4b5 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443 (\u0432 \u0440\u0443\u0431\u043b\u044f\u0445):")
    await state.set_state(AddPaymentFSM.amount)


@router.message(AddPaymentFSM.amount)
async def fsm_payment_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("\u274c \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u043e!")
        return
    await state.update_data(amount=amount)

    # Offer quick date buttons
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="30 \u0434\u043d\u0435\u0439", callback_data="pay:setdays:30"),
            InlineKeyboardButton(text="60 \u0434\u043d\u0435\u0439", callback_data="pay:setdays:60"),
        ],
        [
            InlineKeyboardButton(text="90 \u0434\u043d\u0435\u0439", callback_data="pay:setdays:90"),
            InlineKeyboardButton(text="180 \u0434\u043d\u0435\u0439", callback_data="pay:setdays:180"),
        ],
        [
            InlineKeyboardButton(text="360 \u0434\u043d\u0435\u0439", callback_data="pay:setdays:360"),
        ],
    ])

    await message.answer(
        "\U0001f4c5 \u041d\u0430 \u0441\u043a\u043e\u043b\u044c\u043a\u043e \u0434\u043d\u0435\u0439?\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u0438\u043b\u0438 \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u0434\u0430\u0442\u0443 \u0432\u0440\u0443\u0447\u043d\u0443\u044e:\n"
        "<b>DD.MM.YYYY</b> (\u043d\u0430\u043f\u0440. 15.03.2026)",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await state.set_state(AddPaymentFSM.due_date)


@router.callback_query(F.data.startswith("pay:setdays:"), AddPaymentFSM.due_date)
async def fsm_payment_quick_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split(":")[2])
    due_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    due_display = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
    await _save_payment(callback, state, due_date, due_display, days)
    await callback.answer()


@router.message(AddPaymentFSM.due_date)
async def fsm_payment_date(message: Message, state: FSMContext):
    text = message.text.strip()

    # Support +days format
    if text.startswith("+") and text[1:].isdigit():
        days = int(text[1:])
        due_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        due_display = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
    else:
        try:
            parsed = datetime.strptime(text, "%d.%m.%Y")
            due_date = parsed.strftime("%Y-%m-%d")
            due_display = text
            days = (parsed.date() - datetime.now().date()).days
        except ValueError:
            await message.answer("\u274c \u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442! DD.MM.YYYY \u0438\u043b\u0438 +30")
            return

    data = await state.get_data()
    await db.add_payment(
        server_id=data["server_id"],
        description=data["description"],
        amount=data["amount"],
        due_date=due_date,
    )

    await message.answer(
        f"\u2705 <b>\u041f\u043b\u0430\u0442\u0451\u0436 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d!</b>\n\n"
        f"\U0001f4cb {data['description']}\n"
        f"\U0001f4b5 {format_money(data['amount'])}\n"
        f"\U0001f4c5 {due_display}\n"
        f"\u23f3 \u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: {days} \u0434\u043d\u0435\u0439",
        reply_markup=back_kb("pay:list"),
        parse_mode="HTML",
    )
    await db.log_action(message.from_user.id, "add_payment", data["description"])
    await state.clear()


async def _save_payment(callback: CallbackQuery, state: FSMContext, due_date: str, due_display: str, days: int):
    data = await state.get_data()
    await db.add_payment(
        server_id=data["server_id"],
        description=data["description"],
        amount=data["amount"],
        due_date=due_date,
    )

    await callback.message.edit_text(
        f"\u2705 <b>\u041f\u043b\u0430\u0442\u0451\u0436 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d!</b>\n\n"
        f"\U0001f4cb {data['description']}\n"
        f"\U0001f4b5 {format_money(data['amount'])}\n"
        f"\U0001f4c5 {due_display}\n"
        f"\u23f3 \u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c: {days} \u0434\u043d\u0435\u0439",
        reply_markup=back_kb("pay:list"),
        parse_mode="HTML",
    )
    await db.log_action(callback.from_user.id, "add_payment", data["description"])
    await state.clear()


# === History ===

@router.callback_query(F.data == "pay:history")
async def cb_payment_history(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("\u26d4", show_alert=True)
        return

    payments = await db.get_payments(active_only=False)
    if not payments:
        await callback.message.edit_text(
            "\U0001f4dc <b>\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439</b>\n\n\u041f\u0443\u0441\u0442\u043e.",
            reply_markup=back_kb("menu:payments"),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    text = "\U0001f4dc <b>\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043f\u043b\u0430\u0442\u0435\u0436\u0435\u0439</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    for p in payments[:15]:
        status = "\u2705" if p["is_paid"] else "\u23f3"
        text += f"{status} {p['description']} \u2014 {format_money(p['amount'])} ({p['due_date']})\n"

    await callback.message.edit_text(
        text, reply_markup=back_kb("menu:payments"), parse_mode="HTML"
    )
    await callback.answer()
