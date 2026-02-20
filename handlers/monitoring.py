from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import db
from keyboards.inline import monitoring_kb, monitoring_topic_kb, monitoring_server_kb, back_kb
from services.monitoring_service import monitoring_service
from utils.formatters import format_server_status

router = Router()


async def _safe_callback_answer(callback: CallbackQuery, *args, **kwargs):
    try:
        await callback.answer(*args, **kwargs)
    except Exception:
        pass


# === Monitoring Menu ===

@router.callback_query(F.data == "menu:monitoring")
async def cb_monitoring(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    is_topic_chat = callback.message.chat.id < 0
    servers = await db.get_servers()
    if not servers:
        await callback.message.edit_text(
            "\U0001f4ca <b>\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433</b>\n\n"
            "\u041d\u0435\u0442 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0445 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432.\n"
            "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0434\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440 \u0432 \u041f\u0430\u043d\u0435\u043b\u044c VPS.",
            reply_markup=back_kb("menu:monitoring") if is_topic_chat else back_kb("menu:back"),
            parse_mode="HTML",
        )
        await _safe_callback_answer(callback)
        return

    await callback.message.edit_text(
        "\U0001f4ca <b>\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432</b>\n\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0441\u0435\u0440\u0432\u0435\u0440:",
        reply_markup=monitoring_topic_kb(list(servers)) if is_topic_chat else monitoring_kb(list(servers)),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


# === Server Monitoring ===

@router.callback_query(F.data.startswith("mon:server:"))
async def cb_monitor_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u0421\u0435\u0440\u0432\u0435\u0440 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    await callback.message.edit_text("\u23f3 \u0421\u0431\u043e\u0440 \u043c\u0435\u0442\u0440\u0438\u043a...")

    metrics = await monitoring_service.collect_server(server_id)
    text = format_server_status(dict(server), metrics)

    await callback.message.edit_text(
        text,
        reply_markup=monitoring_server_kb(server_id),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)


# === Refresh Single ===

@router.callback_query(F.data.startswith("mon:refresh:"))
async def cb_refresh_server(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    await _safe_callback_answer(callback, "\U0001f504 \u041e\u0431\u043d\u043e\u0432\u043b\u044f\u044e...")
    metrics = await monitoring_service.collect_server(server_id)
    text = format_server_status(dict(server), metrics)

    await callback.message.edit_text(
        text,
        reply_markup=monitoring_server_kb(server_id),
        parse_mode="HTML",
    )


# === Refresh All ===

@router.callback_query(F.data == "mon:refresh_all")
async def cb_refresh_all(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    is_topic_chat = callback.message.chat.id < 0
    await _safe_callback_answer(callback, "\U0001f504 \u041e\u0431\u043d\u043e\u0432\u043b\u044f\u044e \u0432\u0441\u0435 \u0441\u0435\u0440\u0432\u0435\u0440\u0430...")
    results = await monitoring_service.collect_all()
    servers = await db.get_servers()

    text = "\U0001f4ca <b>\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u2014 \u0412\u0441\u0435 \u0441\u0435\u0440\u0432\u0435\u0440\u0430</b>\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"

    for server in servers:
        sid = server["id"]
        metrics = results.get(sid)

        if metrics:
            from utils.formatters import progress_bar, format_bytes
            cpu = metrics.get("cpu_percent", 0)
            ram = metrics.get("ram_percent", 0)
            text += (
                f"\U0001f7e2 <b>{server['name']}</b>\n"
                f"   CPU: {cpu:.0f}% {progress_bar(cpu, 8)} "
                f"RAM: {ram:.0f}% {progress_bar(ram, 8)}\n\n"
            )
        else:
            text += f"\U0001f534 <b>{server['name']}</b> \u2014 Offline\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=monitoring_topic_kb(list(servers)) if is_topic_chat else monitoring_kb(list(servers)),
        parse_mode="HTML",
    )


# === Monitor from server actions ===

@router.callback_query(F.data.startswith("srv:monitor:"))
async def cb_srv_monitor(callback: CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await _safe_callback_answer(callback, "\u26d4", show_alert=True)
        return

    server_id = int(callback.data.split(":")[2])
    server = await db.get_server(server_id)
    if not server:
        await _safe_callback_answer(callback, "\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d", show_alert=True)
        return

    await callback.message.edit_text("\u23f3 \u0421\u0431\u043e\u0440 \u043c\u0435\u0442\u0440\u0438\u043a...")
    metrics = await monitoring_service.collect_server(server_id)
    text = format_server_status(dict(server), metrics)

    await callback.message.edit_text(
        text,
        reply_markup=monitoring_server_kb(server_id),
        parse_mode="HTML",
    )
    await _safe_callback_answer(callback)
