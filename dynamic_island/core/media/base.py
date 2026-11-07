"""Base classes and data structures for media playback controllers."""
from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class MediaInfo:
    """Current track metadata and playback state."""
    title: str = ""
    artist: str = ""
    album: str = ""
    status: str = "Stopped"  # "Playing", "Paused", "Stopped"
    position_sec: float = 0.0
    duration_sec: float = 0.0
    thumbnail_bytes: Optional[bytes] = None
    player_name: str = ""

    @property
    def is_playing(self) -> bool:
        return self.status.lower() == "playing"

    @property
    def has_media(self) -> bool:
        return bool(self.title.strip())


class BaseMediaController(QObject):
    """Abstract interface for OS media controllers."""

    media_updated = pyqtSignal(object)  # MediaInfo

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_media = MediaInfo()

    def start(self):
        """Start polling or event listeners."""
        pass

    def stop(self):
        """Stop polling or event listeners."""
        pass

    def play_pause(self):
        """Toggle play/pause."""
        pass

    def next_track(self):
        """Skip to next track."""
        pass

    def previous_track(self):
        """Skip to previous track."""
        pass
