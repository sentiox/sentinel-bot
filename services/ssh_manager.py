import asyncio
import io
import paramiko
import logging

logger = logging.getLogger(__name__)


class SSHManager:
    def __init__(self):
        self._connections: dict[int, paramiko.SSHClient] = {}

    def _create_client(self, server: dict) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": server["host"],
            "port": server["port"],
            "username": server["username"],
            "timeout": 10,
        }

        if server["auth_type"] == "key" and server.get("ssh_key"):
            key_file = io.StringIO(server["ssh_key"])
            try:
                pkey = paramiko.RSAKey.from_private_key(key_file)
            except paramiko.SSHException:
                key_file.seek(0)
                pkey = paramiko.Ed25519Key.from_private_key(key_file)
            connect_kwargs["pkey"] = pkey
        else:
            connect_kwargs["password"] = server.get("password", "")

        client.connect(**connect_kwargs)
        return client

    async def execute(self, server: dict, command: str, timeout: int = 30) -> tuple[str, str, int]:
        def _run():
            client = None
            try:
                client = self._create_client(server)
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                exit_code = stdout.channel.recv_exit_status()
                out = stdout.read().decode("utf-8", errors="replace")
                err = stderr.read().decode("utf-8", errors="replace")
                return out, err, exit_code
            except Exception as e:
                logger.error(f"SSH error for {server['host']}: {e}")
                return "", str(e), -1
            finally:
                if client:
                    client.close()

        return await asyncio.get_event_loop().run_in_executor(None, _run)

    async def check_connection(self, server: dict) -> bool:
        try:
            out, err, code = await self.execute(server, "echo ok", timeout=10)
            return code == 0 and "ok" in out
        except Exception:
            return False

    async def get_metrics(self, server: dict) -> dict | None:
        command = """
        echo "===CPU==="
        cat /proc/loadavg
        nproc
        echo "===MEM==="
        free -b | grep Mem
        echo "===DISK==="
        df -B1 / | tail -1
        echo "===NET==="
        cat /proc/net/dev | grep -E "eth0|ens|enp" | head -1
        echo "===UPTIME==="
        cat /proc/uptime
        echo "===CPU_PERCENT==="
        top -bn1 | grep "Cpu(s)" | awk '{print $2}'
        """

        out, err, code = await self.execute(server, command, timeout=15)
        if code != 0:
            return None

        try:
            return self._parse_metrics(out)
        except Exception as e:
            logger.error(f"Parse metrics error: {e}")
            return None

    def _parse_metrics(self, output: str) -> dict:
        metrics = {}
        sections = output.split("===")

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            if section == "CPU":
                lines = sections[i + 1].strip().split("\n")
                if len(lines) >= 2:
                    load = lines[0].split()
                    metrics["load_1m"] = float(load[0])
                    metrics["cpu_cores"] = int(lines[1].strip())

            elif section == "MEM":
                line = sections[i + 1].strip()
                parts = line.split()
                if len(parts) >= 3:
                    metrics["ram_total"] = int(parts[1])
                    metrics["ram_used"] = int(parts[2])
                    metrics["ram_percent"] = (metrics["ram_used"] / metrics["ram_total"] * 100) if metrics["ram_total"] else 0

            elif section == "DISK":
                line = sections[i + 1].strip()
                parts = line.split()
                if len(parts) >= 4:
                    metrics["disk_total"] = int(parts[1])
                    metrics["disk_used"] = int(parts[2])
                    metrics["disk_percent"] = (metrics["disk_used"] / metrics["disk_total"] * 100) if metrics["disk_total"] else 0

            elif section == "UPTIME":
                line = sections[i + 1].strip()
                metrics["uptime"] = int(float(line.split()[0]))

            elif section == "CPU_PERCENT":
                line = sections[i + 1].strip()
                try:
                    metrics["cpu_percent"] = float(line.replace(",", "."))
                except ValueError:
                    metrics["cpu_percent"] = metrics.get("load_1m", 0) / max(metrics.get("cpu_cores", 1), 1) * 100

        metrics.setdefault("cpu_percent", 0)
        metrics.setdefault("cpu_cores", 1)
        metrics.setdefault("ram_total", 0)
        metrics.setdefault("ram_used", 0)
        metrics.setdefault("ram_percent", 0)
        metrics.setdefault("disk_total", 0)
        metrics.setdefault("disk_used", 0)
        metrics.setdefault("disk_percent", 0)
        metrics.setdefault("uptime", 0)
        metrics.setdefault("net_upload", 0)
        metrics.setdefault("net_download", 0)
        metrics.setdefault("ping_ms", 0)

        return metrics

    async def change_password(self, server: dict, new_password: str) -> tuple[bool, str]:
        command = f"echo '{server['username']}:{new_password}' | chpasswd"
        out, err, code = await self.execute(server, command)
        if code == 0:
            return True, "Password changed successfully"
        return False, err

    async def execute_remnawave(self, server: dict, component: str) -> tuple[str, str, int]:
        commands = {
            "panel": "cd /opt/remnawave && docker compose pull && docker compose down && docker compose up -d && docker compose logs --tail=50",
            "node": "cd /opt/remnanode && docker compose pull && docker compose down && docker compose up -d && docker compose logs --tail=50",
            "subscription": "cd /opt/remnawave/subscription && docker compose pull && docker compose down && docker compose up -d && docker compose logs --tail=50",
            "clean": "docker image prune -f",
        }
        cmd = commands.get(component, "echo 'Unknown component'")
        return await self.execute(server, cmd, timeout=120)


ssh_manager = SSHManager()
