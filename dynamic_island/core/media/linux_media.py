"""Linux media controller using MPRIS2 via playerctl or D-Bus."""
import subprocess
import shutil
from typing import Optional
from PyQt6.QtCore import QTimer

from .base import BaseMediaController, MediaInfo


class LinuxMediaController(BaseMediaController):
    """Media controller for Linux desktop environments."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_playerctl = bool(shutil.which("playerctl"))
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_media)

    def start(self):
        if self._has_playerctl:
            self._poll_timer.start(1500)
            self._poll_media()
        else:
            self.current_media = MediaInfo(
                title="Linux Media Ready",
                artist="Install playerctl for full MPRIS",
                status="Paused",
                player_name="System"
            )
            self.media_updated.emit(self.current_media)

    def stop(self):
        self._poll_timer.stop()

    def _poll_media(self):
        if not self._has_playerctl:
            return
        try:
            # Query playerctl metadata
            cmd = [
                "playerctl",
                "metadata",
                "--format",
                "{{title}};;;{{artist}};;;{{album}};;;{{status}};;;{{playerName}}",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=0.8)
            if res.returncode == 0 and res.stdout.strip():
                parts = res.stdout.strip().split(";;;")
                title = parts[0] if len(parts) > 0 else ""
                artist = parts[1] if len(parts) > 1 else ""
                album = parts[2] if len(parts) > 2 else ""
                status = parts[3] if len(parts) > 3 else "Paused"
                player = parts[4] if len(parts) > 4 else "Media Player"

                new_info = MediaInfo(
                    title=title,
                    artist=artist,
                    album=album,
                    status=status,
                    player_name=player,
                )

                if (new_info.title != self.current_media.title or
                    new_info.status != self.current_media.status):
                    self.current_media = new_info
                    self.media_updated.emit(self.current_media)
            else:
                if self.current_media.has_media:
                    self.current_media = MediaInfo(
                        title="No Active Media",
                        artist="Play audio in Spotify or Browser",
                        status="Stopped",
                        player_name="System"
                    )
                    self.media_updated.emit(self.current_media)
        except Exception:
            pass

    def play_pause(self):
        if self._has_playerctl:
            try:
                subprocess.run(["playerctl", "play-pause"], check=False)
            except Exception:
                pass
        if self.current_media.status == "Playing":
            self.current_media.status = "Paused"
        else:
            self.current_media.status = "Playing"
        self.media_updated.emit(self.current_media)

    def next_track(self):
        if self._has_playerctl:
            try:
                subprocess.run(["playerctl", "next"], check=False)
            except Exception:
                pass

    def previous_track(self):
        if self._has_playerctl:
            try:
                subprocess.run(["playerctl", "previous"], check=False)
            except Exception:
                pass
