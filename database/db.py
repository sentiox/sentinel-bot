import aiosqlite
from pathlib import Path
from config import DB_PATH


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._conn = None

    async def connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def _create_tables(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT DEFAULT 'root',
                auth_type TEXT DEFAULT 'password',
                password TEXT,
                ssh_key TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'RUB',
                due_date TEXT NOT NULL,
                is_recurring INTEGER DEFAULT 1,
                recurring_months INTEGER DEFAULT 1,
                is_paid INTEGER DEFAULT 0,
                notified_days TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers(id)
            );

            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                balance_before REAL DEFAULT 0,
                balance_after REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS admins (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # --- Servers ---

    async def add_server(self, name, host, port=22, username="root",
                         auth_type="password", password=None, ssh_key=None):
        await self._conn.execute(
            "INSERT INTO servers (name, host, port, username, auth_type, password, ssh_key) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, host, port, username, auth_type, password, ssh_key)
        )
        await self._conn.commit()

    async def get_servers(self):
        cursor = await self._conn.execute("SELECT * FROM servers WHERE is_active = 1")
        return await cursor.fetchall()

    async def get_server(self, server_id):
        cursor = await self._conn.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
        return await cursor.fetchone()

    async def delete_server(self, server_id):
        await self._conn.execute("UPDATE servers SET is_active = 0 WHERE id = ?", (server_id,))
        await self._conn.commit()

    async def update_server(self, server_id, **kwargs):
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [server_id]
        await self._conn.execute(f"UPDATE servers SET {sets} WHERE id = ?", values)
        await self._conn.commit()

    # --- Payments ---

    async def add_payment(self, server_id, description, amount, due_date,
                          currency="RUB", is_recurring=1, recurring_months=1):
        await self._conn.execute(
            "INSERT INTO payments (server_id, description, amount, due_date, currency, "
            "is_recurring, recurring_months) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (server_id, description, amount, due_date, currency, is_recurring, recurring_months)
        )
        await self._conn.commit()

    async def get_payments(self, active_only=True):
        query = "SELECT p.*, s.name as server_name FROM payments p LEFT JOIN servers s ON p.server_id = s.id"
        if active_only:
            query += " WHERE p.is_paid = 0"
        query += " ORDER BY p.due_date"
        cursor = await self._conn.execute(query)
        return await cursor.fetchall()

    async def get_payment(self, payment_id):
        cursor = await self._conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        return await cursor.fetchone()

    async def mark_paid(self, payment_id):
        await self._conn.execute("UPDATE payments SET is_paid = 1 WHERE id = ?", (payment_id,))
        await self._conn.commit()

    async def update_payment_notified(self, payment_id, notified_days):
        await self._conn.execute(
            "UPDATE payments SET notified_days = ? WHERE id = ?",
            (notified_days, payment_id)
        )
        await self._conn.commit()

    # --- Balance ---

    async def get_balance(self):
        cursor = await self._conn.execute(
            "SELECT balance_after FROM balance_history ORDER BY id DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return row["balance_after"] if row else 0.0

    async def add_balance_operation(self, operation_type, amount, description=None):
        balance_before = await self.get_balance()
        if operation_type == "income":
            balance_after = balance_before + amount
        else:
            balance_after = balance_before - amount
        await self._conn.execute(
            "INSERT INTO balance_history (operation_type, amount, description, balance_before, balance_after) "
            "VALUES (?, ?, ?, ?, ?)",
            (operation_type, amount, description, balance_before, balance_after)
        )
        await self._conn.commit()
        return balance_before, balance_after

    async def get_balance_history(self, limit=10):
        cursor = await self._conn.execute(
            "SELECT * FROM balance_history ORDER BY id DESC LIMIT ?", (limit,)
        )
        return await cursor.fetchall()

    # --- Settings ---

    async def get_setting(self, key, default=None):
        cursor = await self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else default

    async def set_setting(self, key, value):
        await self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value))
        )
        await self._conn.commit()

    # --- Admins ---

    async def get_admins(self):
        cursor = await self._conn.execute("SELECT * FROM admins")
        return await cursor.fetchall()

    async def add_admin(self, telegram_id, username=None):
        await self._conn.execute(
            "INSERT OR IGNORE INTO admins (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        await self._conn.commit()

    async def remove_admin(self, telegram_id):
        await self._conn.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
        await self._conn.commit()

    async def is_admin(self, telegram_id):
        from config import ADMIN_IDS
        if telegram_id in ADMIN_IDS:
            return True
        cursor = await self._conn.execute(
            "SELECT 1 FROM admins WHERE telegram_id = ?", (telegram_id,)
        )
        return await cursor.fetchone() is not None

    # --- Logs ---

    async def log_action(self, admin_id, action, details=None):
        await self._conn.execute(
            "INSERT INTO action_logs (admin_id, action, details) VALUES (?, ?, ?)",
            (admin_id, action, details)
        )
        await self._conn.commit()

    async def get_logs(self, limit=20):
        cursor = await self._conn.execute(
            "SELECT * FROM action_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        return await cursor.fetchall()
