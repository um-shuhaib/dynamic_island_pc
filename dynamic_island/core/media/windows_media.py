"""Windows media controller using WinRT GSMTC and fallback multimedia keys."""
import asyncio
import ctypes
import threading
import time
from typing import Optional
from PyQt6.QtCore import QTimer

from .base import BaseMediaController, MediaInfo

# Win32 virtual key codes for media
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


def send_media_key(vk_code: int):
    """Simulate hardware media key press on Windows."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
    except Exception as e:
        print(f"[WindowsMedia] Error sending media key: {e}")


class WindowsMediaController(BaseMediaController):
    """Media controller for Windows 10/11."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._async_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._has_winsdk = False
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_tick)

        self._check_winsdk()

    def _check_winsdk(self):
        try:
            import winsdk.windows.media.control as wmc  # type: ignore
            self._has_winsdk = True
        except ImportError:
            try:
                import winrt.windows.media.control as wmc  # type: ignore
                self._has_winsdk = True
            except ImportError:
                self._has_winsdk = False

    def start(self):
        self._running = True
        if self._has_winsdk:
            self._async_thread = threading.Thread(
                target=self._run_async_loop,
                daemon=True,
                name="WinRTMediaWatcher"
            )
            self._async_thread.start()
        else:
            # Fallback mock/idle info
            self.current_media = MediaInfo(
                title="Desktop Audio Ready",
                artist="Use media keys to play",
                status="Paused",
                player_name="System"
            )
            self.media_updated.emit(self.current_media)

    def stop(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _poll_tick(self):
        pass

    def _run_async_loop(self):
        """Async event loop for WinRT GSMTC events."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._watch_media_sessions())
        except Exception as e:
            print(f"[WindowsMedia] Async loop error: {e}")

    async def _watch_media_sessions(self):
        try:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager as SessionManager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
            )
            manager = await SessionManager.request_async()

            while self._running:
                session = manager.get_current_session()
                if session:
                    info = await session.try_get_media_properties_async()
                    playback_info = session.get_playback_info()

                    status_str = "Paused"
                    if playback_info:
                        if playback_info.playback_status == PlaybackStatus.PLAYING:
                            status_str = "Playing"
                        elif playback_info.playback_status == PlaybackStatus.PAUSED:
                            status_str = "Paused"
                        elif playback_info.playback_status == PlaybackStatus.STOPPED:
                            status_str = "Stopped"

                    title = info.title if info else "Unknown"
                    artist = info.artist if info else "Unknown"
                    album = info.album_title if info else ""

                    thumb_bytes = None
                    if info and info.thumbnail:
                        try:
                            stream = await info.thumbnail.open_read_async()
                            size = stream.size
                            if size > 0:
                                from winsdk.windows.storage.streams import DataReader
                                reader = DataReader(stream)
                                await reader.load_async(size)
                                raw_bytes = bytearray(size)
                                reader.read_bytes(raw_bytes)
                                thumb_bytes = bytes(raw_bytes)
                        except Exception:
                            thumb_bytes = None

                    new_info = MediaInfo(
                        title=title,
                        artist=artist,
                        album=album,
                        status=status_str,
                        thumbnail_bytes=thumb_bytes,
                        player_name=session.source_app_user_model_id or "Media App"
                    )

                    if (new_info.title != self.current_media.title or
                        new_info.status != self.current_media.status or
                        new_info.artist != self.current_media.artist):
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

                await asyncio.sleep(1.0)
        except Exception as e:
            print(f"[WindowsMedia] Session watcher exception: {e}")

    def play_pause(self):
        send_media_key(VK_MEDIA_PLAY_PAUSE)
        # Optimistically toggle state
        if self.current_media.status == "Playing":
            self.current_media.status = "Paused"
        else:
            self.current_media.status = "Playing"
        self.media_updated.emit(self.current_media)

    def next_track(self):
        send_media_key(VK_MEDIA_NEXT_TRACK)

    def previous_track(self):
        send_media_key(VK_MEDIA_PREV_TRACK)
