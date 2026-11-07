"""Transient alert banner widget for notifications and events."""
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel


class AlertBannerView(QWidget):
    """Temporary alert banner widget shown when an event occurs."""

    alert_expired = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._on_timeout)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        self.icon_label = QLabel("🔔")
        self.icon_label.setStyleSheet("font-size: 16px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Alert")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")

        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("color: #AEAEB2; font-size: 11px;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.msg_label)
        layout.addLayout(text_layout, stretch=1)

    def show_alert(self, title: str, message: str, icon: str = "🔔", duration_ms: int = 3500):
        self.icon_label.setText(icon)
        self.title_label.setText(title)
        self.msg_label.setText(message)
        self._dismiss_timer.start(duration_ms)

    def _on_timeout(self):
        self.alert_expired.emit()
