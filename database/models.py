# Database models are defined as SQL in database/db.py
# This file provides dataclass representations for type hints

from dataclasses import dataclass
from typing import Optional


@dataclass
class Server:
    id: int
    name: str
    host: str
    port: int = 22
    username: str = "root"
    auth_type: str = "password"
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    is_active: int = 1


@dataclass
class Payment:
    id: int
    server_id: Optional[int]
    description: str
    amount: float
    currency: str = "RUB"
    due_date: str = ""
    is_recurring: int = 1
    recurring_months: int = 1
    is_paid: int = 0
    notified_days: str = ""


@dataclass
class BalanceRecord:
    id: int
    operation_type: str
    amount: float
    description: Optional[str]
    balance_before: float
    balance_after: float
