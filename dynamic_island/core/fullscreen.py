"""Fullscreen application detector for Windows and Linux."""
import sys
import time
from PyQt6.QtCore import QThread, pyqtSignal


class FullscreenDetectorThread(QThread):
    """Background worker monitoring whether the active window is full screen."""

    fullscreen_changed = pyqtSignal(bool)

    def __init__(self, parent=None, poll_interval_ms: int = 800):
        super().__init__(parent)
        self.poll_interval = poll_interval_ms / 1000.0
        self._running = True
        self._is_fullscreen = False

    def stop(self):
        self._running = False
        self.wait(1000)

    def run(self):
        while self._running:
            try:
                current_state = self._check_fullscreen()
                if current_state != self._is_fullscreen:
                    self._is_fullscreen = current_state
                    self.fullscreen_changed.emit(self._is_fullscreen)
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def _check_fullscreen(self) -> bool:
        if sys.platform == "win32":
            return self._check_windows()
        else:
            return self._check_linux()

    def _check_windows(self) -> bool:
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False

            # Ignore desktop shell windows
            class_name = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_name, 256)
            if class_name.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
                return False

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))

            # Get monitor info for the window
            hmonitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
            if not hmonitor:
                return False

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi))

            # Check if window covers or exceeds the entire monitor
            is_covering = (
                rect.left <= mi.rcMonitor.left
                and rect.top <= mi.rcMonitor.top
                and rect.right >= mi.rcMonitor.right
                and rect.bottom >= mi.rcMonitor.bottom
            )
            return is_covering
        except Exception:
            return False

    def _check_linux(self) -> bool:
        try:
            import subprocess
            # Try xprop if on X11
            res = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                capture_output=True,
                text=True,
                timeout=0.4,
            )
            if res.returncode != 0:
                return False
            window_id = res.stdout.strip().split()[-1]
            if not window_id or window_id == "0x0":
                return False

            state_res = subprocess.run(
                ["xprop", "-id", window_id, "_NET_WM_STATE"],
                capture_output=True,
                text=True,
                timeout=0.4,
            )
            return "_NET_WM_STATE_FULLSCREEN" in state_res.stdout
        except Exception:
            return False
