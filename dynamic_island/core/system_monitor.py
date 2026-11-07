"""Background system metrics monitor using psutil."""
import time
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import psutil
except ImportError:
    psutil = None


class SystemMonitorThread(QThread):
    """Periodically queries CPU, RAM, Battery, and Network statistics."""

    stats_updated = pyqtSignal(dict)

    def __init__(self, parent=None, interval_ms: int = 1500):
        super().__init__(parent)
        self.interval = interval_ms / 1000.0
        self._running = True
        self._last_net_io = None
        self._last_net_time = None

    def stop(self):
        self._running = False
        self.wait(1000)

    def run(self):
        # Prime psutil cpu measurement
        if psutil:
            try:
                psutil.cpu_percent(interval=None)
                self._last_net_io = psutil.net_io_counters()
                self._last_net_time = time.time()
            except Exception:
                pass

        while self._running:
            data = self._gather_stats()
            self.stats_updated.emit(data)
            time.sleep(self.interval)

    def _gather_stats(self) -> dict:
        if not psutil:
            return {
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "ram_used_gb": 0.0,
                "ram_total_gb": 0.0,
                "battery_percent": None,
                "battery_plugged": False,
                "net_down_kb": 0.0,
                "net_up_kb": 0.0,
            }

        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()

            # Battery
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else None
            battery_plugged = battery.power_plugged if battery else False

            # Network throughput
            now = time.time()
            net_io = psutil.net_io_counters()
            net_down_kb = 0.0
            net_up_kb = 0.0

            if self._last_net_io and self._last_net_time:
                dt = max(now - self._last_net_time, 0.01)
                down_bytes = max(net_io.bytes_recv - self._last_net_io.bytes_recv, 0)
                up_bytes = max(net_io.bytes_sent - self._last_net_io.bytes_sent, 0)
                net_down_kb = (down_bytes / 1024.0) / dt
                net_up_kb = (up_bytes / 1024.0) / dt

            self._last_net_io = net_io
            self._last_net_time = now

            return {
                "cpu_percent": round(cpu, 1),
                "ram_percent": round(mem.percent, 1),
                "ram_used_gb": round(mem.used / (1024**3), 1),
                "ram_total_gb": round(mem.total / (1024**3), 1),
                "battery_percent": round(battery_percent, 1) if battery_percent is not None else None,
                "battery_plugged": battery_plugged,
                "net_down_kb": round(net_down_kb, 1),
                "net_up_kb": round(net_up_kb, 1),
            }
        except Exception as e:
            return {
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "ram_used_gb": 0.0,
                "ram_total_gb": 0.0,
                "battery_percent": None,
                "battery_plugged": False,
                "net_down_kb": 0.0,
                "net_up_kb": 0.0,
                "error": str(e),
            }
