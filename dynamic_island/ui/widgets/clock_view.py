"""Clock, date, and calendar widget for Dynamic Island."""
import time
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)


class ClockView(QWidget):
    """Expanded view displaying current time, date, and day of week."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_time)
        self._timer.start(1000)
        self.update_time()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Big Digital Clock
        self.lbl_time = QLabel("12:00:00 PM")
        self.lbl_time.setStyleSheet(
            "color: #FFFFFF; font-size: 28px; font-weight: bold; letter-spacing: 1px;"
        )
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_time)

        # Full Date
        self.lbl_date = QLabel("Saturday, November 7, 2026")
        self.lbl_date.setStyleSheet("color: #0A84FF; font-size: 13px; font-weight: 600;")
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_date)

        # Day of week row
        self.days_layout = QHBoxLayout()
        self.days_layout.setSpacing(6)
        self.days_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_labels = []

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for name in day_names:
            lbl = QLabel(name)
            lbl.setFixedSize(36, 22)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                color: #8E8E93;
                font-size: 10px;
                font-weight: bold;
                border-radius: 6px;
                background-color: #1C1C1E;
            """)
            self.day_labels.append(lbl)
            self.days_layout.addWidget(lbl)

        layout.addLayout(self.days_layout)

    def update_time(self):
        now = datetime.now()

        # Format time with AM/PM
        time_str = now.strftime("%I:%M:%S %p").lstrip("0")
        self.lbl_time.setText(time_str)

        # Format date
        date_str = now.strftime("%A, %B %d, %Y")
        self.lbl_date.setText(date_str)

        # Highlight current weekday (0 = Monday, 6 = Sunday)
        weekday = now.weekday()
        for idx, lbl in enumerate(self.day_labels):
            if idx == weekday:
                lbl.setStyleSheet("""
                    color: #FFFFFF;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 6px;
                    background-color: #0A84FF;
                """)
            else:
                lbl.setStyleSheet("""
                    color: #8E8E93;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 6px;
                    background-color: #1C1C1E;
                """)
