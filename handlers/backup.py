from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import db
from keyboards.inline import backup_kb, back_kb, confirm_kb
from services.ssh_manager import ssh_manager

router = Router()


async def _safe_callback_answer(callback, *args, **kwargs):
    try:
        await callback.answer(*args, **kwargs)
    except Exception:
        pass


# === Backup Menu ===

@router.callback_query(F.data == "menu:backup")
async def cb_backup(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    servers = await db.get_servers()
    if not servers:
        await callback.message.edit_text(
            "\U0001f504 <b>\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f Remnawave</b>\n\n"
            "\u041d\u0435\u0442 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432. \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0434\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440.",
            reply_markup=back_kb("menu:back"),
            parse_mode="HTML",
        )
        await _safe_callback_answer(callback)
        return

    # If only one server — show actions directly
    if len(list(servers)) == 1:
        server = servers[0]
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001f7e2 Update Panel", callback_data=f"bkp:do:panel:{server['id']}")],
            [InlineKeyboardButton(text="\U0001f7e1 Update Node", callback_data=f"bkp:do:node:{server['id']}")],
            [InlineKeyboardButton(text="\U0001f535 Update Subscription", callback_data=f"bkp:do:sub:{server['id']}")],
            [InlineKeyboardButton(text="\U0001f534 Clean Docker Images", callback_data=f"bkp:do:clean:{server['id']}")],
            [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")],
        ])
        await callback.message.edit_text(
            f"\U0001f504 <b>\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f Remnawave</b>\n"
            f"\U0001f5a5 \u0421\u0435\u0440\u0432\u0435\u0440: {server['name']}",
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        # Multiple servers — select first
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for s in servers:
            buttons.append([InlineKeyboardButton(
                text=f"\U0001f5a5 {s['name']}",
                callback_data=f"bkp:srv:{s['id']}"
            )])
        buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")])

        await callback.message.edit_text(
            "\U0001f504 <b>\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f Remnawave</b>\n\n"
            "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    await _safe_callback_answer(callback)


# === Select Server for Backup ===

@router.callback_query(F.data.startswith("bkp:srv:"))
async def cb_backup_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f7e2 Update Panel", callback_data=f"bkp:do:panel:{server_id}")],
        [InlineKeyboardButton(text="\U0001f7e1 Update Node", callback_data=f"bkp:do:node:{server_id}")],
        [InlineKeyboardButton(text="\U0001f535 Update Subscription", callback_data=f"bkp:do:sub:{server_id}")],
        [InlineKeyboardButton(text="\U0001f534 Clean Docker Images", callback_data=f"bkp:do:clean:{server_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:backup")],
    ])

    await callback.message.edit_text(
        f"\U0001f504 <b>\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f Remnawave</b>\n"
        f"\U0001f5a5 \u0421\u0435\u0440\u0432\u0435\u0440: {server['name']}",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


# === Execute Update ===

@router.callback_query(F.data.startswith("bkp:do:"))
async def cb_backup_execute(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    parts = callback.data.split(":")
    component = parts[2]
    server_id = int(parts[3])

    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    names = {
        "panel": "Remnawave Panel",
        "node": "Remnawave Node",
        "sub": "Subscription Page",
        "clean": "Docker Clean",
    }
    name = names.get(component, component)
    comp_key = {"sub": "subscription"}.get(component, component)

    await callback.message.edit_text(
        f"\u23f3 <b>{name}</b>\n\u041e\u0431\u043d\u043e\u0432\u043b\u044f\u044e \u043d\u0430 {server['name']}...",
        parse_mode="HTML",
    )

    out, err, code = await ssh_manager.execute_remnawave(dict(server), comp_key)

    result = out or err or "(\u043f\u0443\u0441\u0442\u043e)"
    if len(result) > 3500:
        result = result[-3500:]

    icon = "\u2705" if code == 0 else "\u274c"
    status = "OK" if code == 0 else "\u041e\u0448\u0438\u0431\u043a\u0430"

    await callback.message.edit_text(
        f"{icon} <b>{name} \u2014 {status}</b>\n"
        f"\U0001f5a5 {server['name']}\n\n"
        f"<pre>{result}</pre>",
        reply_markup=back_kb(f"bkp:srv:{server_id}"),
        parse_mode="HTML",
    )
    await db.log_action(callback.from_user.id, f"update_{component}", server["name"])
    await _safe_callback_answer(callback)


# === Quick backup buttons from main menu ===

@router.callback_query(F.data.startswith("bkp:panel"))
@router.callback_query(F.data.startswith("bkp:node"))
@router.callback_query(F.data.startswith("bkp:sub"))
@router.callback_query(F.data.startswith("bkp:clean"))
async def cb_quick_backup(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    # Redirect to server selection
    servers = await db.get_servers()
    if not servers:
        await _safe_callback_answer(callback, "\u041d\u0435\u0442 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432", show_alert=True)
        return

    if len(list(servers)) == 1:
        component = callback.data.split(":")[1]
        callback.data = f"bkp:do:{component}:{servers[0]['id']}"
        await cb_backup_execute(callback)
    else:
        await cb_backup(callback)
