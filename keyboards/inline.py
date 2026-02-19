from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# === Main Menu ===

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f5a5 \u041f\u0430\u043d\u0435\u043b\u044c VPS", callback_data="menu:vps"),
         InlineKeyboardButton(text="\U0001f4ca \u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433", callback_data="menu:monitoring")],
        [InlineKeyboardButton(text="\U0001f4b0 \u041e\u043f\u043b\u0430\u0442\u0430", callback_data="menu:payments"),
         InlineKeyboardButton(text="\U0001f4b3 \u0411\u0430\u043b\u0430\u043d\u0441", callback_data="menu:balance")],
        [InlineKeyboardButton(text="\U0001f504 \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f", callback_data="menu:backup"),
         InlineKeyboardButton(text="\u2699\ufe0f \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", callback_data="menu:admin")],
    ])


# === VPS Panel ===

def vps_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4cb \u0421\u043f\u0438\u0441\u043e\u043a \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432", callback_data="vps:list")],
        [InlineKeyboardButton(text="\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0441\u0435\u0440\u0432\u0435\u0440", callback_data="vps:add")],
        [InlineKeyboardButton(text="\U0001f510 SSH \u041c\u0435\u043d\u0435\u0434\u0436\u0435\u0440", callback_data="vps:ssh_manager")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")],
    ])


def server_actions_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4ca \u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433", callback_data=f"srv:monitor:{server_id}"),
         InlineKeyboardButton(text="\U0001f504 \u0420\u0435\u0441\u0442\u0430\u0440\u0442", callback_data=f"srv:reboot:{server_id}")],
        [InlineKeyboardButton(text="\U0001f4e6 Remnawave", callback_data=f"srv:remna:{server_id}"),
         InlineKeyboardButton(text="\U0001f5a5 \u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b", callback_data=f"srv:terminal:{server_id}")],
        [InlineKeyboardButton(text="\u270f\ufe0f \u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c", callback_data=f"srv:edit:{server_id}"),
         InlineKeyboardButton(text="\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c", callback_data=f"srv:delete:{server_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="vps:list")],
    ])


def server_list_kb(servers: list) -> InlineKeyboardMarkup:
    buttons = []
    for s in servers:
        status = "\U0001f7e2" if s["is_active"] else "\U0001f534"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {s['name']}",
            callback_data=f"srv:select:{s['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:vps")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# === Remnawave ===

def remnawave_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f7e2 Update Panel", callback_data=f"remna:panel:{server_id}")],
        [InlineKeyboardButton(text="\U0001f7e1 Update Node", callback_data=f"remna:node:{server_id}")],
        [InlineKeyboardButton(text="\U0001f535 Update Subscription", callback_data=f"remna:sub:{server_id}")],
        [InlineKeyboardButton(text="\U0001f534 Clean Docker Images", callback_data=f"remna:clean:{server_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data=f"srv:select:{server_id}")],
    ])


# === Payments ===

def payments_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4cb \u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0438", callback_data="pay:list")],
        [InlineKeyboardButton(text="\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043f\u043b\u0430\u0442\u0451\u0436", callback_data="pay:add")],
        [InlineKeyboardButton(text="\U0001f4dc \u0418\u0441\u0442\u043e\u0440\u0438\u044f", callback_data="pay:history")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")],
    ])


def payment_actions_kb(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2705 \u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e", callback_data=f"pay:paid:{payment_id}"),
         InlineKeyboardButton(text="\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c", callback_data=f"pay:del:{payment_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="pay:list")],
    ])


# === Balance ===

def balance_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4b3 \u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u0431\u0430\u043b\u0430\u043d\u0441", callback_data="bal:show")],
        [InlineKeyboardButton(text="\U0001f4e5 \u041f\u043e\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435", callback_data="bal:income"),
         InlineKeyboardButton(text="\U0001f4e4 \u0421\u043f\u0438\u0441\u0430\u043d\u0438\u0435", callback_data="bal:expense")],
        [InlineKeyboardButton(text="\U0001f9fe \u041e\u043f\u043b\u0430\u0442\u0430", callback_data="bal:payment")],
        [InlineKeyboardButton(text="\U0001f4dc \u0418\u0441\u0442\u043e\u0440\u0438\u044f", callback_data="bal:history")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")],
    ])


# === Monitoring ===

def monitoring_kb(servers: list) -> InlineKeyboardMarkup:
    buttons = []
    for s in servers:
        buttons.append([InlineKeyboardButton(
            text=f"\U0001f4ca {s['name']}",
            callback_data=f"mon:server:{s['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="\U0001f504 \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0432\u0441\u0435", callback_data="mon:refresh_all")])
    buttons.append([InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def monitoring_server_kb(server_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f504 \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c", callback_data=f"mon:refresh:{server_id}")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:monitoring")],
    ])


# === Admin ===

def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f465 \u0410\u0434\u043c\u0438\u043d\u044b", callback_data="adm:list"),
         InlineKeyboardButton(text="\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0430\u0434\u043c\u0438\u043d\u0430", callback_data="adm:add")],
        [InlineKeyboardButton(text="\U0001f514 \u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f", callback_data="adm:notifications")],
        [InlineKeyboardButton(text="\U0001f4cb \u041b\u043e\u0433\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439", callback_data="adm:logs")],
        [InlineKeyboardButton(text="\U0001f4e4 \u042d\u043a\u0441\u043f\u043e\u0440\u0442 \u0434\u0430\u043d\u043d\u044b\u0445", callback_data="adm:export")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")],
    ])


# === Backup / Updates ===

def backup_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f7e2 Update Remnawave Panel", callback_data="bkp:panel")],
        [InlineKeyboardButton(text="\U0001f7e1 Update Remnawave Node", callback_data="bkp:node")],
        [InlineKeyboardButton(text="\U0001f535 Update Subscription Page", callback_data="bkp:sub")],
        [InlineKeyboardButton(text="\U0001f534 Clean Docker Images", callback_data="bkp:clean")],
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:back")],
    ])


def confirm_kb(action: str, item_id: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2705 \u0414\u0430", callback_data=f"confirm:{action}:{item_id}"),
         InlineKeyboardButton(text="\u274c \u041d\u0435\u0442", callback_data=f"cancel:{action}:{item_id}")],
    ])


def back_kb(callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data=callback)],
    ])
