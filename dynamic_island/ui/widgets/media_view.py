"""Media player widget for Compact and Expanded Dynamic Island states."""
import math
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
)

from ...core.media.base import MediaInfo


class AnimatedWaveform(QWidget):
    """Mini 3-bar animated sound visualizer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.is_playing = False
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_step)
        self._timer.start(50)

    def set_playing(self, playing: bool):
        self.is_playing = playing
        self.update()

    def _animate_step(self):
        if self.is_playing:
            self._phase += 0.25
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor("#30D158") if self.is_playing else QColor("#8E8E93")
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)

        # 3 bars
        w = 2.5
        spacing = 2.0
        max_h = 13.0
        x_start = 2.0

        for i in range(3):
            if self.is_playing:
                h = 4.0 + (math.sin(self._phase + i * 1.5) * 0.5 + 0.5) * (max_h - 4.0)
            else:
                h = 3.0
            x = x_start + i * (w + spacing)
            y = (self.height() - h) / 2.0
            painter.drawRoundedRect(QRectF(x, y, w, h), 1.2, 1.2)


class MediaView(QWidget):
    """Media view switching between compact pill indicator and expanded player controls."""

    def __init__(self, media_controller, parent=None):
        super().__init__(parent)
        self.controller = media_controller
        self.current_media = MediaInfo()

        self._setup_ui()
        if self.controller:
            self.controller.media_updated.connect(self.update_media)
            self.controller.start()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.stack = QStackedWidget(self)
        self.main_layout.addWidget(self.stack)

        # 0: Compact View
        self.compact_widget = QWidget()
        compact_layout = QHBoxLayout(self.compact_widget)
        compact_layout.setContentsMargins(6, 0, 6, 0)
        compact_layout.setSpacing(6)

        self.compact_waveform = AnimatedWaveform()
        compact_layout.addWidget(self.compact_waveform)

        self.compact_title_label = QLabel("No Media")
        self.compact_title_label.setStyleSheet(
            "color: #FFFFFF; font-size: 11px; font-weight: 600;"
        )
        self.compact_title_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        compact_layout.addWidget(self.compact_title_label, stretch=1)

        self.stack.addWidget(self.compact_widget)

        # 1: Expanded View
        self.expanded_widget = QWidget()
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(16, 12, 16, 12)
        exp_layout.setSpacing(10)

        # Top row: Art + Metadata
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(12)

        self.art_label = QLabel()
        self.art_label.setFixedSize(48, 48)
        self.art_label.setStyleSheet(
            "background-color: #1C1C1E; border-radius: 8px; color: #8E8E93;"
        )
        self.art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art_label.setText("🎵")
        self.art_label.setFont(QFont("Segoe UI", 18))
        meta_layout.addWidget(self.art_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.exp_title = QLabel("No Track Playing")
        self.exp_title.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        self.exp_title.setWordWrap(False)

        self.exp_artist = QLabel("Start playback to see controls")
        self.exp_artist.setStyleSheet("color: #8E8E93; font-size: 12px;")
        self.exp_artist.setWordWrap(False)

        text_layout.addWidget(self.exp_title)
        text_layout.addWidget(self.exp_artist)
        meta_layout.addLayout(text_layout, stretch=1)
        exp_layout.addLayout(meta_layout)

        # Bottom row: Controls
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(24)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_style = """
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                font-size: 18px;
                border: none;
                border-radius: 18px;
                min-width: 36px;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #2C2C2E;
            }
            QPushButton:pressed {
                background-color: #3A3A3C;
            }
        """

        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setStyleSheet(btn_style)
        self.btn_prev.clicked.connect(self._on_prev)

        self.btn_play = QPushButton("▶")
        self.btn_play.setStyleSheet(
            btn_style.replace("font-size: 18px", "font-size: 22px; font-weight: bold;")
        )
        self.btn_play.clicked.connect(self._on_play_pause)

        self.btn_next = QPushButton("⏭")
        self.btn_next.setStyleSheet(btn_style)
        self.btn_next.clicked.connect(self._on_next)

        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_next)
        exp_layout.addLayout(btn_layout)

        self.stack.addWidget(self.expanded_widget)
        self.stack.setCurrentIndex(0)

    def set_expanded_mode(self, expanded: bool):
        self.stack.setCurrentIndex(1 if expanded else 0)

    def update_media(self, media: MediaInfo):
        self.current_media = media
        # Compact update
        display_title = media.title or "Desktop Audio"
        if len(display_title) > 22:
            display_title = display_title[:20] + "…"
        self.compact_title_label.setText(display_title)
        self.compact_waveform.set_playing(media.is_playing)

        # Expanded update
        self.exp_title.setText(media.title or "No Track Playing")
        self.exp_artist.setText(media.artist or (media.player_name or "System Audio"))
        self.btn_play.setText("⏸" if media.is_playing else "▶")

        # Art update
        if media.thumbnail_bytes:
            pix = QPixmap()
            if pix.loadFromData(media.thumbnail_bytes):
                scaled = pix.scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.art_label.setPixmap(scaled)
                self.art_label.setText("")
                return

        self.art_label.setText("🎵")

    def _on_play_pause(self):
        if self.controller:
            self.controller.play_pause()

    def _on_prev(self):
        if self.controller:
            self.controller.previous_track()

    def _on_next(self):
        if self.controller:
            self.controller.next_track()
