"""Cross-platform auto-start manager for Windows and Linux."""
import os
import sys
from pathlib import Path


def get_command_to_run() -> str:
    """Return command string to launch the application."""
    # Find launcher script relative to this file
    launcher = Path(__file__).resolve().parent.parent.parent / "run.py"
    if sys.platform == "win32":
        # Prefer pythonw if available to avoid opening console window
        python_exe = sys.executable
        pythonw = Path(python_exe).parent / "pythonw.exe"
        exe = str(pythonw) if pythonw.exists() else python_exe
        return f'"{exe}" "{launcher}"'
    else:
        return f'"{sys.executable}" "{launcher}"'


class AutoStartManager:
    """Configures application auto-start on system boot."""

    APP_NAME = "DynamicIsland"

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if auto-start is currently configured."""
        if sys.platform == "win32":
            return cls._is_enabled_windows()
        else:
            return cls._is_enabled_linux()

    @classmethod
    def set_enabled(cls, enable: bool) -> bool:
        """Enable or disable auto-start."""
        if sys.platform == "win32":
            return cls._set_windows(enable)
        else:
            return cls._set_linux(enable)

    @classmethod
    def _is_enabled_windows(cls) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            try:
                winreg.QueryValueEx(key, cls.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            print(f"[AutoStart] Windows check failed: {e}")
            return False

    @classmethod
    def _set_windows(cls, enable: bool) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            if enable:
                cmd = get_command_to_run()
                winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, cls.APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[AutoStart] Windows configuration failed: {e}")
            return False

    @classmethod
    def _get_linux_desktop_file(cls) -> Path:
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        return autostart_dir / "dynamic_island.desktop"

    @classmethod
    def _is_enabled_linux(cls) -> bool:
        return cls._get_linux_desktop_file().exists()

    @classmethod
    def _set_linux(cls, enable: bool) -> bool:
        desktop_file = cls._get_linux_desktop_file()
        try:
            if enable:
                cmd = get_command_to_run()
                content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=Dynamic Island
Comment=Dynamic Island Desktop Overlay
Exec={cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
                desktop_file.write_text(content, encoding="utf-8")
            else:
                if desktop_file.exists():
                    desktop_file.unlink()
            return True
        except Exception as e:
            print(f"[AutoStart] Linux configuration failed: {e}")
            return False
