from datetime import datetime, timedelta


def progress_bar(percent: float, length: int = 10) -> str:
    filled = int(length * percent / 100)
    empty = length - filled
    return "\u2593" * filled + "\u2591" * empty


def format_bytes(bytes_val: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def format_uptime(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days}\u0434")
    if hours:
        parts.append(f"{hours}\u0447")
    parts.append(f"{minutes}\u043c")
    return " ".join(parts)


def format_money(amount: float) -> str:
    if amount == int(amount):
        return f"{int(amount):,}\u20bd".replace(",", " ")
    return f"{amount:,.2f}\u20bd".replace(",", " ")


def format_server_status(server: dict, metrics: dict = None) -> str:
    name = server.get("name", "Unknown")
    host = server.get("host", "")

    if not metrics:
        return (
            f"\U0001f5a5 <b>{name}</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f534 \u0421\u0442\u0430\u0442\u0443\u0441: <b>Offline</b>\n"
            f"\U0001f310 Host: <code>{host}</code>\n"
        )

    cpu = metrics.get("cpu_percent", 0)
    cpu_cores = metrics.get("cpu_cores", 0)
    ram_used = metrics.get("ram_used", 0)
    ram_total = metrics.get("ram_total", 0)
    ram_percent = metrics.get("ram_percent", 0)
    disk_used = metrics.get("disk_used", 0)
    disk_total = metrics.get("disk_total", 0)
    disk_percent = metrics.get("disk_percent", 0)
    net_up = metrics.get("net_upload", 0)
    net_down = metrics.get("net_download", 0)
    uptime = metrics.get("uptime", 0)
    ping_ms = metrics.get("ping_ms", 0)

    return (
        f"\U0001f4ca <b>\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433 \u2014 {name}</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f5a5 CPU: {cpu:.0f}% {progress_bar(cpu)} {cpu_cores} \u044f\u0434\u0435\u0440\n"
        f"\U0001f9e0 RAM: {ram_percent:.0f}% {progress_bar(ram_percent)} {format_bytes(ram_used)}/{format_bytes(ram_total)}\n"
        f"\U0001f4be Disk: {disk_percent:.0f}% {progress_bar(disk_percent)} {format_bytes(disk_used)}/{format_bytes(disk_total)}\n"
        f"\U0001f310 Network: \u2191 {format_bytes(net_up)}/s \u2193 {format_bytes(net_down)}/s\n"
        f"\u23f1 Uptime: {format_uptime(uptime)}\n"
        f"\U0001f4e1 Ping: {ping_ms}ms\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f7e2 \u0421\u0442\u0430\u0442\u0443\u0441: <b>Online</b>\n"
        f"\U0001f550 \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    )


def format_payment_reminder(payment: dict, days_left: int) -> str:
    desc = payment.get("description", "")
    amount = payment.get("amount", 0)
    due_date = payment.get("due_date", "")
    server_name = payment.get("server_name", "")

    if days_left == 0:
        urgency = "\U0001f534\U0001f534\U0001f534 \u0421\u0415\u0413\u041e\u0414\u041d\u042f!"
    elif days_left == 1:
        urgency = "\U0001f7e0 \u0417\u0430\u0432\u0442\u0440\u0430!"
    elif days_left <= 3:
        urgency = f"\U0001f7e1 \u0427\u0435\u0440\u0435\u0437 {days_left} \u0434\u043d."
    else:
        urgency = f"\U0001f535 \u0427\u0435\u0440\u0435\u0437 {days_left} \u0434\u043d."

    return (
        f"\U0001f4b0 <b>\u041d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435 \u043e\u0431 \u043e\u043f\u043b\u0430\u0442\u0435</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"{urgency}\n\n"
        f"\U0001f4cb {desc}\n"
        f"\U0001f5a5 \u0421\u0435\u0440\u0432\u0435\u0440: {server_name}\n"
        f"\U0001f4b5 \u0421\u0443\u043c\u043c\u0430: <b>{format_money(amount)}</b>\n"
        f"\U0001f4c5 \u0414\u0430\u0442\u0430: {due_date}\n"
    )


def format_balance_report(balance: float, history: list = None) -> str:
    now = datetime.now()
    text = (
        f"\U0001f4b3 <b>\u042eKassa \u0411\u0430\u043b\u0430\u043d\u0441</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
    )

    if history:
        last = history[0]
        text += f"\U0001f4b0 \u0411\u0430\u043b\u0430\u043d\u0441 \u0431\u044b\u043b: {format_money(last['balance_before'])}\n"

        total_income = sum(h["amount"] for h in history if h["operation_type"] == "income")
        total_expense = sum(h["amount"] for h in history if h["operation_type"] == "expense")
        total_payment = sum(h["amount"] for h in history if h["operation_type"] == "payment")

        if total_income:
            text += f"\U0001f4e5 \u041f\u043e\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435: {format_money(total_income)}\n"
        else:
            text += f"\U0001f4e5 \u041f\u043e\u043f\u043e\u043b\u043d\u0435\u043d\u0438\u0435: \u2014\n"

        if total_expense:
            text += f"\U0001f4e4 \u0421\u043f\u0438\u0441\u0430\u043d\u0438\u0435: {format_money(total_expense)}\n"
        else:
            text += f"\U0001f4e4 \u0421\u043f\u0438\u0441\u0430\u043d\u0438\u0435: \u2014\n"

        if total_payment:
            text += f"\U0001f9fe \u041e\u043f\u043b\u0430\u0442\u0430: {format_money(total_payment)}\n"
        else:
            text += f"\U0001f9fe \u041e\u043f\u043b\u0430\u0442\u0430: \u2014\n"

    text += (
        f"\u2705 \u041e\u0441\u0442\u0430\u0442\u043e\u043a: <b>{format_money(balance)}</b>\n"
        f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f4c5 {now.strftime('%d.%m.%Y')} \u2022 \U0001f550 {now.strftime('%H:%M')}\n"
    )
    return text


def format_server_list(servers: list) -> str:
    if not servers:
        return "\U0001f5a5 <b>\u0421\u043f\u0438\u0441\u043e\u043a \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432</b>\n\n\u041d\u0435\u0442 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0445 \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432."

    text = f"\U0001f5a5 <b>\u0421\u043f\u0438\u0441\u043e\u043a \u0441\u0435\u0440\u0432\u0435\u0440\u043e\u0432</b> ({len(servers)})\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
    for s in servers:
        status = "\U0001f7e2" if s["is_active"] else "\U0001f534"
        text += f"{status} <b>{s['name']}</b> \u2014 <code>{s['host']}:{s['port']}</code>\n"
    return text
