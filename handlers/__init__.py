from aiogram import Router

from handlers.start import router as start_router
from handlers.vps_panel import router as vps_router
from handlers.payments import router as payments_router
from handlers.balance import router as balance_router
from handlers.monitoring import router as monitoring_router
from handlers.admin import router as admin_router
from handlers.backup import router as backup_router


def get_all_routers() -> list[Router]:
    return [
        start_router,
        vps_router,
        payments_router,
        balance_router,
        monitoring_router,
        admin_router,
        backup_router,
    ]
