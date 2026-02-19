import asyncio
import logging
from datetime import datetime

from services.ssh_manager import ssh_manager
from database import db
from config import ALERT_CPU_THRESHOLD, ALERT_RAM_THRESHOLD, ALERT_DISK_THRESHOLD

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self):
        self._last_metrics: dict[int, dict] = {}
        self._alerts_sent: dict[str, datetime] = {}

    async def collect_all(self) -> dict[int, dict | None]:
        servers = await db.get_servers()
        results = {}

        tasks = []
        for server in servers:
            tasks.append(self._collect_one(dict(server), server["id"]))

        collected = await asyncio.gather(*tasks, return_exceptions=True)
        for server_id, metrics in collected:
            if isinstance(metrics, Exception):
                results[server_id] = None
            else:
                results[server_id] = metrics
                if metrics:
                    self._last_metrics[server_id] = metrics

        return results

    async def _collect_one(self, server: dict, server_id: int) -> tuple[int, dict | None]:
        try:
            metrics = await ssh_manager.get_metrics(server)
            return server_id, metrics
        except Exception as e:
            logger.error(f"Monitoring error for server {server_id}: {e}")
            return server_id, None

    async def collect_server(self, server_id: int) -> dict | None:
        server = await db.get_server(server_id)
        if not server:
            return None
        metrics = await ssh_manager.get_metrics(dict(server))
        if metrics:
            self._last_metrics[server_id] = metrics
        return metrics

    def get_cached_metrics(self, server_id: int) -> dict | None:
        return self._last_metrics.get(server_id)

    def check_alerts(self, server_id: int, server_name: str, metrics: dict) -> list[str]:
        alerts = []
        now = datetime.now()

        checks = [
            ("cpu", metrics.get("cpu_percent", 0), ALERT_CPU_THRESHOLD, "CPU"),
            ("ram", metrics.get("ram_percent", 0), ALERT_RAM_THRESHOLD, "RAM"),
            ("disk", metrics.get("disk_percent", 0), ALERT_DISK_THRESHOLD, "Disk"),
        ]

        for key, value, threshold, label in checks:
            alert_key = f"{server_id}:{key}"
            if value >= threshold:
                last_sent = self._alerts_sent.get(alert_key)
                if not last_sent or (now - last_sent).seconds > 600:
                    alerts.append(
                        f"\u26a0\ufe0f <b>\u0410\u043b\u0435\u0440\u0442: {server_name}</b>\n"
                        f"{label}: <b>{value:.0f}%</b> (>\u2009{threshold}%)"
                    )
                    self._alerts_sent[alert_key] = now
            else:
                self._alerts_sent.pop(alert_key, None)

        return alerts


monitoring_service = MonitoringService()
