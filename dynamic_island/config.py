"""Persistent configuration manager for Dynamic Island."""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def get_config_dir() -> Path:
    """Return platform-appropriate configuration directory with graceful fallback."""
    candidate_dirs = []

    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        if app_data:
            candidate_dirs.append(Path(app_data) / "dynamic_island")
        candidate_dirs.append(Path.home() / "AppData" / "Roaming" / "dynamic_island")
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            candidate_dirs.append(Path(xdg_config) / "dynamic_island")
        candidate_dirs.append(Path.home() / ".config" / "dynamic_island")

    # Local project fallback (portable mode / sandbox-friendly)
    candidate_dirs.append(Path(__file__).resolve().parent.parent / ".config" / "dynamic_island")

    for c_dir in candidate_dirs:
        try:
            c_dir.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = c_dir / ".write_test"
            test_file.touch(exist_ok=True)
            test_file.unlink(missing_ok=True)
            return c_dir
        except (PermissionError, OSError):
            continue

    # Ultimate fallback to current directory
    fallback = Path.cwd() / ".config" / "dynamic_island"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


DEFAULT_CONFIG: Dict[str, Any] = {
    "first_run_completed": False,
    "monitor_index": 0,
    "top_offset": 8,
    "compact_width": 200,
    "compact_height": 34,
    "expanded_width": 390,
    "expanded_height": 195,
    "corner_radius": 17,
    "auto_hide_fullscreen": True,
    "hover_expand": True,
    "autostart": False,
    "modules": {
        "clock": True,
        "media": True,
        "system": True,
        "pomodoro": True,
        "clipboard": True,
    },
    "pomodoro": {
        "work_minutes": 25,
        "break_minutes": 5,
        "sound_enabled": True,
    },
    "appearance": {
        "bg_color": "#000000",
        "border_color": "#282828",
        "accent_color": "#0A84FF",
        "text_color": "#FFFFFF",
        "subtext_color": "#98989D",
    },
}


class ConfigManager:
    """Manages reading and writing application settings."""

    def __init__(self):
        self.config_path = get_config_dir() / "config.json"
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from disk, falling back to defaults."""
        self._config = DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._merge_deep(self._config, data)
            except Exception as e:
                print(f"[Config] Error loading config: {e}. Using defaults.")
        return self._config

    def _merge_deep(self, target: dict, source: dict):
        """Recursively merge dictionary sources into target."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._merge_deep(target[key], value)
            else:
                target[key] = value

    def save(self) -> bool:
        """Save configuration to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            return True
        except Exception as e:
            print(f"[Config] Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get top-level config value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        """Set a top-level config value and optionally save immediately."""
        self._config[key] = value
        if auto_save:
            self.save()

    def get_dict(self) -> Dict[str, Any]:
        """Return raw configuration dictionary."""
        return self._config


# Global singleton instance
config = ConfigManager()
