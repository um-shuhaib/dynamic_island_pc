"""Media controller factory for platform selection."""
import sys
from .base import BaseMediaController
from .windows_media import WindowsMediaController
from .linux_media import LinuxMediaController


def create_media_controller(parent=None) -> BaseMediaController:
    """Instantiate appropriate media controller based on operating system."""
    if sys.platform == "win32":
        return WindowsMediaController(parent)
    else:
        return LinuxMediaController(parent)
