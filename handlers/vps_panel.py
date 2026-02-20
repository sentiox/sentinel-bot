from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards.inline import (
    vps_panel_kb, server_actions_kb, remnawave_kb, confirm_kb, back_kb
)
from services.ssh_manager import ssh_manager
from utils.telegram_safe import edit_message_text_safe
from utils.formatters import format_server_list, format_money

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


class AddServerFSM(StatesGroup):
    name = State()
    host = State()
    port = State()
    username = State()
    auth_type = State()
    password = State()
    ssh_key = State()


class EditServerFSM(StatesGroup):
    server_id = State()
    field = State()
    value = State()


class TerminalFSM(StatesGroup):
    command = State()
    server_id = State()


class ChangePasswordFSM(StatesGroup):
    server_id = State()
    new_password = State()


# === VPS Panel Menu ===

@router.callback_query(F.data == "menu:vps")
async def cb_vps_panel(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    await callback.message.edit_text(
        "\U0001f5a5 <b>\u041f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f VPS</b>",
        reply_markup=vps_panel_kb(),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


# === Server List ===

@router.callback_query(F.data == "vps:list")
async def cb_server_list(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    servers = await db.get_servers()

    if not servers:
        await callback.message.edit_text(
            "\U0001f5a5 <b>\u0421\u043f\u0438\u0441\u043e\u043a \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432</b>\n\n\u041d\u0435\u0442 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0445 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432.",
            reply_markup=back_kb("menu:vps"),
            parse_mode="HTML",
        )
        await _safe_callback_answer(callback)
        return

    # Get payments to show remaining days per server
    payments = await db.get_payments(active_only=True)
    today = datetime.now().date()
    server_days = {}
    for p in payments:
        sid = p["server_id"]
        if sid:
            due = datetime.strptime(p["due_date"], "%Y-%m-%d").date()
            days_left = (due - today).days
            if sid not in server_days or days_left < server_days[sid]:
                server_days[sid] = days_left

    text = f"\U0001f5a5 <b>\u0421\u043f\u0438\u0441\u043e\u043a \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432</b> ({len(list(servers))})\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    buttons = []
    for s in servers:
        sid = s["id"]
        days_left = server_days.get(sid)

        if days_left is not None:
            if days_left < 0:
                icon = "\U0001f534"
                days_str = f" \u2022 \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e {abs(days_left)}\u0434"
            elif days_left <= 3:
                icon = "\U0001f7e1"
                days_str = f" \u2022 {days_left}\u0434"
            elif days_left <= 7:
                icon = "\U0001f7e0"
                days_str = f" \u2022 {days_left}\u0434"
            else:
                icon = "\U0001f7e2"
                days_str = f" \u2022 {days_left}\u0434"
        else:
            icon = "\u26aa"
            days_str = ""

        text += f"{icon} <b>{s['name']}</b> \u2014 <code>{s['host']}:{s['port']}</code>{days_str}\n"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {s['name']}{days_str}",
            callback_data=f"srv:select:{sid}"
        )])

    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:vps")])

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)


# === Select Server ===

@router.callback_query(F.data.startswith("srv:select:"))
async def cb_server_select(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u0421\u0435\u0440\u0432\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    online = await ssh_manager.check_connection(dict(server))
    status = "\U0001f7e2 Online" if online else "\U0001f534 Offline"

    # Get payment info for this server
    payments = await db.get_payments(active_only=True)
    today = datetime.now().date()
    payment_info = ""
    for p in payments:
        if p["server_id"] == server_id:
            due = datetime.strptime(p["due_date"], "%Y-%m-%d").date()
            days_left = (due - today).days
            if days_left < 0:
                pay_icon = "\U0001f534"
                pay_str = f"\u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e {abs(days_left)}\u0434"
            elif days_left <= 3:
                pay_icon = "\U0001f7e1"
                pay_str = f"{days_left}\u0434 \u043e\u0441\u0442\u0430\u043b\u043e\u0441\u044c"
            else:
                pay_icon = "\U0001f7e2"
                pay_str = f"{days_left}\u0434 \u043e\u0441\u0442\u0430\u043b\u043e\u0441\u044c"
            payment_info += f"\n{pay_icon} \u041e\u043f\u043b\u0430\u0442\u0430: <b>{pay_str}</b> \u2022 {format_money(p['amount'])}"
            payment_info += f"\n\U0001f4c5 \u0414\u043e: {p['due_date']}"

    if not payment_info:
        payment_info = "\n\u26aa \u041e\u043f\u043b\u0430\u0442\u0430: <i>\u043d\u0435 \u043f\u0440\u0438\u0432\u044f\u0437\u0430\u043d\u0430</i>"

    text = (
        f"\U0001f5a5 <b>{server['name']}</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f310 Host: <code>{server['host']}:{server['port']}</code>\n"
        f"\U0001f464 User: <code>{server['username']}</code>\n"
        f"\U0001f511 Auth: {server['auth_type']}\n"
        f"\U0001f4e1 \u0421\u0442\u0430\u0442\u0443\u0441: <b>{status}</b>"
        f"{payment_info}"
    )
    await callback.message.edit_text(
        text, reply_markup=server_actions_kb(server_id), parse_mode="HTML"
    )
    await _safe_callback_answer(callback)


# === Add Server ===

@router.callback_query(F.data == "vps:add")
async def cb_add_server(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    await callback.message.edit_text(
        "\u2795 <b>\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u0441\u0435\u0440\u0432\u0435\u0440\u0430</b>\n\n"
        "\U0001f4dd \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u0435\u0440\u0432\u0435\u0440\u0430:",
        parse_mode="HTML",
    )
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await state.set_state(AddServerFSM.name)
    await _safe_callback_answer(callback)


@router.message(AddServerFSM.name)
async def fsm_server_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await _edit_bot_msg(message, state, "\U0001f310 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 IP-\u0430\u0434\u0440\u0435\u0441 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 (host):")
    await state.set_state(AddServerFSM.host)


@router.message(AddServerFSM.host)
async def fsm_server_host(message: Message, state: FSMContext):
    await state.update_data(host=message.text.strip())
    await _edit_bot_msg(message, state, "\U0001f522 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 SSH \u043f\u043e\u0440\u0442 (Enter = 22):")
    await state.set_state(AddServerFSM.port)


@router.message(AddServerFSM.port)
async def fsm_server_port(message: Message, state: FSMContext):
    port = message.text.strip()
    port = int(port) if port.isdigit() else 22
    await state.update_data(port=port)
    await _edit_bot_msg(message, state, "\U0001f464 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043b\u043e\u0433\u0438\u043d (Enter = root):")
    await state.set_state(AddServerFSM.username)


@router.message(AddServerFSM.username)
async def fsm_server_username(message: Message, state: FSMContext):
    username = message.text.strip() or "root"
    await state.update_data(username=username)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f511 \u041f\u0430\u0440\u043e\u043b\u044c", callback_data="auth:password"),
         InlineKeyboardButton(text="\U0001f510 SSH \u041a\u043b\u044e\u0447", callback_data="auth:key")],
    ])
    await _edit_bot_msg(message, state, "\U0001f512 \u0422\u0438\u043f \u0430\u0443\u0442\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438:", reply_markup=kb)
    await state.set_state(AddServerFSM.auth_type)


@router.callback_query(F.data.startswith("auth:"), AddServerFSM.auth_type)
async def fsm_server_auth(callback: CallbackQuery, state: FSMContext):
    auth_type = callback.data.split(":")[1]
    await state.update_data(auth_type=auth_type)

    if auth_type == "password":
        await callback.message.edit_text("\U0001f511 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c:")
        await state.set_state(AddServerFSM.password)
    else:
        await callback.message.edit_text(
            "\U0001f510 \u0412\u0441\u0442\u0430\u0432\u044c\u0442\u0435 \u043f\u0440\u0438\u0432\u0430\u0442\u043d\u044b\u0439 SSH \u043a\u043b\u044e\u0447\n"
            "(\u0432\u0435\u0441\u044c \u0442\u0435\u043a\u0441\u0442, \u043d\u0430\u0447\u0438\u043d\u0430\u044f \u0441 -----BEGIN):"
        )
        await state.set_state(AddServerFSM.ssh_key)
    await _safe_callback_answer(callback)


@router.message(AddServerFSM.password)
async def fsm_server_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    await _save_server(message, state)


@router.message(AddServerFSM.ssh_key)
async def fsm_server_key(message: Message, state: FSMContext):
    await state.update_data(ssh_key=message.text.strip())
    await _save_server(message, state)


async def _save_server(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_server(
        name=data["name"],
        host=data["host"],
        port=data.get("port", 22),
        username=data.get("username", "root"),
        auth_type=data.get("auth_type", "password"),
        password=data.get("password"),
        ssh_key=data.get("ssh_key"),
    )

    # Test connection
    server_dict = {
        "host": data["host"],
        "port": data.get("port", 22),
        "username": data.get("username", "root"),
        "auth_type": data.get("auth_type", "password"),
        "password": data.get("password"),
        "ssh_key": data.get("ssh_key"),
    }
    online = await ssh_manager.check_connection(server_dict)
    status = "\U0001f7e2 \u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 \u0443\u0441\u043f\u0435\u0448\u043d\u043e!" if online else "\U0001f534 \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f"

    await _edit_bot_msg(message, state,
        f"\u2705 <b>\u0421\u0435\u0440\u0432\u0435\u0440 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d!</b>\n\n"
        f"\U0001f4cb {data['name']}\n"
        f"\U0001f310 {data['host']}:{data.get('port', 22)}\n"
        f"\U0001f4e1 {status}",
        reply_markup=back_kb("vps:list"),
        parse_mode="HTML",
    )
    await db.log_action(message.from_user.id, "add_server", data["name"])
    await state.clear()


# === Edit Server ===

@router.callback_query(F.data.startswith("srv:edit:"))
async def cb_edit_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u0421\u0435\u0440\u0432\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4dd \u0418\u043c\u044f", callback_data=f"srv:editf:name:{server_id}"),
         InlineKeyboardButton(text="\U0001f310 Host", callback_data=f"srv:editf:host:{server_id}")],
        [InlineKeyboardButton(text="\U0001f522 \u041f\u043e\u0440\u0442", callback_data=f"srv:editf:port:{server_id}"),
         InlineKeyboardButton(text="\U0001f464 \u041b\u043e\u0433\u0438\u043d", callback_data=f"srv:editf:username:{server_id}")],
        [InlineKeyboardButton(text="\U0001f511 \u041f\u0430\u0440\u043e\u043b\u044c", callback_data=f"srv:editf:password:{server_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data=f"srv:select:{server_id}")],
    ])
    await callback.message.edit_text(
        f"\u270f\ufe0f <b>\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435: {server['name']}</b>\n\n"
        f"\U0001f310 Host: <code>{server['host']}:{server['port']}</code>\n"
        f"\U0001f464 User: <code>{server['username']}</code>\n"
        f"\U0001f511 Auth: {server['auth_type']}\n\n"
        f"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u043e\u043b\u0435 \u0434\u043b\u044f \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f:",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("srv:editf:"))
async def cb_edit_server_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    field = parts[2]
    server_id = int(parts[3])

    field_names = {
        "name": "\u0438\u043c\u044f \u0441\u0435\u0440\u0432\u0435\u0440\u0430",
        "host": "IP-\u0430\u0434\u0440\u0435\u0441",
        "port": "SSH \u043f\u043e\u0440\u0442",
        "username": "\u043b\u043e\u0433\u0438\u043d",
        "password": "\u043f\u0430\u0440\u043e\u043b\u044c",
    }
    await state.update_data(edit_server_id=server_id, edit_field=field, _bot_msg_id=callback.message.message_id)
    await state.set_state(EditServerFSM.value)
    await callback.message.edit_text(
        f"\u270f\ufe0f \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u0432\u043e\u0435 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435 \u0434\u043b\u044f <b>{field_names.get(field, field)}</b>:\n\n"
        f"(\u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /cancel \u0434\u043b\u044f \u043e\u0442\u043c\u0435\u043d\u044b)",
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.message(EditServerFSM.value)
async def fsm_edit_server_value(message: Message, state: FSMContext):
    if message.text == "/cancel":
        data = await state.get_data()
        await _edit_bot_msg(message, state,
            "\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e.",
            reply_markup=back_kb(f"srv:edit:{data.get('edit_server_id', 0)}"),
        )
        await state.clear()
        return

    data = await state.get_data()
    server_id = data["edit_server_id"]
    field = data["edit_field"]
    value = message.text.strip()

    if field == "port":
        if not value.isdigit():
            await _delete_msg(message)
            return
        value = int(value)

    await db.update_server(server_id, **{field: value})
    await _edit_bot_msg(message, state,
        f"\u2705 \u041f\u043e\u043b\u0435 \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e!",
        reply_markup=back_kb(f"srv:edit:{server_id}"),
    )
    await db.log_action(message.from_user.id, "edit_server", f"id={server_id} {field}")
    await state.clear()


# === Delete Server ===

@router.callback_query(F.data.startswith("srv:delete:"))
async def cb_delete_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return
    await callback.message.edit_text(
        f"\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0441\u0435\u0440\u0432\u0435\u0440 <b>{server['name']}</b>?",
        reply_markup=confirm_kb("del_srv", server_id),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("confirm:del_srv:"))
async def cb_confirm_delete_server(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[2])
    await db.delete_server(server_id)
    await callback.message.edit_text(
        "\u2705 \u0421\u0435\u0440\u0432\u0435\u0440 \u0443\u0434\u0430\u043b\u0451\u043d.",
        reply_markup=back_kb("vps:list"),
    )
    await db.log_action(callback.from_user.id, "delete_server", str(server_id))
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("cancel:del_srv:"))
async def cb_cancel_delete_server(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "\u274c \u0423\u0434\u0430\u043b\u0435\u043d\u0438\u0435 \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u043e.",
        reply_markup=back_kb(f"srv:select:{server_id}"),
    )
    await _safe_callback_answer(callback)


# === Reboot ===

@router.callback_query(F.data.startswith("srv:reboot:"))
async def cb_reboot_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "\U0001f504 \u041f\u0435\u0440\u0435\u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0441\u0435\u0440\u0432\u0435\u0440?",
        reply_markup=confirm_kb("reboot", server_id),
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("confirm:reboot:"))
async def cb_confirm_reboot(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    await callback.message.edit_text("\u23f3 \u041f\u0435\u0440\u0435\u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0430...")
    out, err, code = await ssh_manager.execute(dict(server), "reboot", timeout=10)
    await callback.message.edit_text(
        "\u2705 \u041a\u043e\u043c\u0430\u043d\u0434\u0430 \u043f\u0435\u0440\u0435\u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430!",
        reply_markup=back_kb(f"srv:select:{server_id}"),
    )
    await db.log_action(callback.from_user.id, "reboot_server", server["name"])


@router.callback_query(F.data.startswith("cancel:reboot:"))
async def cb_cancel_reboot(callback: CallbackQuery):
    server_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e.",
        reply_markup=back_kb(f"srv:select:{server_id}"),
    )
    await _safe_callback_answer(callback)


# === Terminal ===

@router.callback_query(F.data.startswith("srv:terminal:"))
async def cb_terminal(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    await state.update_data(terminal_server_id=server_id, _bot_msg_id=callback.message.message_id)
    await state.set_state(TerminalFSM.command)
    await callback.message.edit_text(
        "\U0001f5a5 <b>\u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b</b>\n\n"
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u043c\u0430\u043d\u0434\u0443 \u0434\u043b\u044f \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u044f:\n"
        "(\u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 /cancel \u0434\u043b\u044f \u0432\u044b\u0445\u043e\u0434\u0430)",
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.message(TerminalFSM.command)
async def fsm_terminal_exec(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await _edit_bot_msg(message, state,
            "\u2705 \u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b \u0437\u0430\u043a\u0440\u044b\u0442.", reply_markup=back_kb("menu:vps"))
        await state.clear()
        return

    data = await state.get_data()
    server_id = data.get("terminal_server_id")
    server = await db.get_server(server_id)
    if not server:
        await _edit_bot_msg(message, state, "\u0421\u0435\u0440\u0432\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d")
        await state.clear()
        return

    await _edit_bot_msg(message, state, "\u23f3 \u0412\u044b\u043f\u043e\u043b\u043d\u044f\u044e...")
    out, err, code = await ssh_manager.execute(dict(server), message.text.strip(), timeout=15)

    result = out or err or "(\u043f\u0443\u0441\u0442\u043e\u0439 \u0432\u044b\u0432\u043e\u0434)"
    if len(result) > 3500:
        result = result[:3500] + "\n...\u043e\u0431\u0440\u0435\u0437\u0430\u043d\u043e"

    exit_icon = "\u2705" if code == 0 else "\u274c"
    terminal_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u25c0\ufe0f \u0417\u0430\u043a\u0440\u044b\u0442\u044c \u0442\u0435\u0440\u043c\u0438\u043d\u0430\u043b", callback_data=f"srv:select:{server_id}")],
    ])
    data = await state.get_data()
    bot_msg_id = data.get("_bot_msg_id")
    if bot_msg_id:
        try:
            await edit_message_text_safe(
                message.bot,
                text=f"{exit_icon} <b>Exit: {code}</b>\n"
                     f"<pre>{result}</pre>\n\n"
                     f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0443\u044e \u043a\u043e\u043c\u0430\u043d\u0434\u0443 \u0438\u043b\u0438 /cancel",
                chat_id=message.chat.id,
                message_id=bot_msg_id,
                reply_markup=terminal_kb,
                parse_mode="HTML",
            )
        except Exception:
            msg = await message.answer(
                f"{exit_icon} <b>Exit: {code}</b>\n"
                f"<pre>{result}</pre>\n\n"
                f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0443\u044e \u043a\u043e\u043c\u0430\u043d\u0434\u0443 \u0438\u043b\u0438 /cancel",
                reply_markup=terminal_kb,
                parse_mode="HTML",
            )
            await state.update_data(_bot_msg_id=msg.message_id)
    await db.log_action(message.from_user.id, "terminal", f"{server['name']}: {message.text[:100]}")


# === Remnawave ===

@router.callback_query(F.data.startswith("srv:remna:"))
async def cb_remnawave_menu(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "\U0001f4e6 <b>Remnawave \u2014 \u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:",
        reply_markup=remnawave_kb(server_id),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("remna:"))
async def cb_remnawave_action(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    parts = callback.data.split(":")
    component = parts[1]
    server_id = int(parts[2])

    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u0421\u0435\u0440\u0432\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    names = {"panel": "Panel", "node": "Node", "sub": "Subscription Page", "clean": "Docker Clean"}
    name = names.get(component, component)
    comp_key = {"sub": "subscription"}.get(component, component)

    await callback.message.edit_text(f"\u23f3 \u041e\u0431\u043d\u043e\u0432\u043b\u044f\u044e <b>{name}</b>...", parse_mode="HTML")
    out, err, code = await ssh_manager.execute_remnawave(dict(server), comp_key)

    result = out or err or "(\u043f\u0443\u0441\u0442\u043e)"
    if len(result) > 3500:
        result = result[-3500:]

    icon = "\u2705" if code == 0 else "\u274c"
    await callback.message.edit_text(
        f"{icon} <b>{name}</b> \u2014 {'OK' if code == 0 else '\u041e\u0448\u0438\u0431\u043a\u0430'}\n\n"
        f"<pre>{result}</pre>",
        reply_markup=back_kb(f"srv:remna:{server_id}"),
        parse_mode="HTML",
    )
    await db.log_action(callback.from_user.id, f"remnawave_{component}", server["name"])
    await _safe_callback_answer(callback)


# === SSH Manager ===

@router.callback_query(F.data == "vps:ssh_manager")
async def cb_ssh_manager(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    servers = await db.get_servers()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for s in servers:
        buttons.append([InlineKeyboardButton(
            text=f"\U0001f510 {s['name']}",
            callback_data=f"ssh:manage:{s['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:vps")])

    await callback.message.edit_text(
        "\U0001f510 <b>SSH \u041c\u0435\u043d\u0435\u0434\u0436\u0435\u0440</b>\n\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("ssh:manage:"))
async def cb_ssh_manage_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    server_id = int(callback.data.split(":")[2])
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f511 \u0421\u043c\u0435\u043d\u0438\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c", callback_data=f"ssh:chpwd:{server_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="vps:ssh_manager")],
    ])

    await callback.message.edit_text(
        "\U0001f510 <b>SSH \u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


@router.callback_query(F.data.startswith("ssh:chpwd:"))
async def cb_change_password_start(callback: CallbackQuery, state: FSMContext):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return
    server_id = int(callback.data.split(":")[2])
    await state.update_data(chpwd_server_id=server_id, _bot_msg_id=callback.message.message_id)
    await state.set_state(ChangePasswordFSM.new_password)
    await callback.message.edit_text(
        "\U0001f511 \u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u043e\u0432\u044b\u0439 \u043f\u0430\u0440\u043e\u043b\u044c \u0434\u043b\u044f SSH:",
    )
    await _safe_callback_answer(callback)


@router.message(ChangePasswordFSM.new_password)
async def fsm_change_password(message: Message, state: FSMContext):
    data = await state.get_data()
    server_id = data.get("chpwd_server_id")
    server = await db.get_server(server_id)
    if not server:
        await _edit_bot_msg(message, state, "\u0421\u0435\u0440\u0432\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d")
        await state.clear()
        return

    new_pwd = message.text.strip()
    success, msg = await ssh_manager.change_password(dict(server), new_pwd)

    if success:
        await db.update_server(server_id, password=new_pwd)
        await _edit_bot_msg(message, state,
            f"\u2705 \u041f\u0430\u0440\u043e\u043b\u044c \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0451\u043d!",
            reply_markup=back_kb("vps:ssh_manager"),
        )
        await db.log_action(message.from_user.id, "change_password", server["name"])
    else:
        await _edit_bot_msg(message, state,
            f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430: {msg}", reply_markup=back_kb("vps:ssh_manager"))

    await state.clear()
