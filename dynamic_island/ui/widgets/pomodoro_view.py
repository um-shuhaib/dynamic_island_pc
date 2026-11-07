"""Pomodoro / Focus timer widget for Dynamic Island."""
import sys
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
)


class PomodoroView(QWidget):
    """Pomodoro focus timer with compact pill time and expanded controls."""

    timer_finished = pyqtSignal(str)  # Emits alert message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_seconds = 25 * 60
        self.break_seconds = 5 * 60
        self.remaining_seconds = self.work_seconds
        self.is_running = False
        self.is_work_mode = True

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget(self)
        main_layout.addWidget(self.stack)

        # 0: Compact View
        self.compact_widget = QWidget()
        compact_layout = QHBoxLayout(self.compact_widget)
        compact_layout.setContentsMargins(6, 0, 6, 0)
        compact_layout.setSpacing(6)

        self.compact_label = QLabel("🍅 25:00")
        self.compact_label.setStyleSheet("color: #FF453A; font-size: 11px; font-weight: bold;")
        compact_layout.addWidget(self.compact_label)
        self.stack.addWidget(self.compact_widget)

        # 1: Expanded View
        self.expanded_widget = QWidget()
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(16, 12, 16, 12)
        exp_layout.setSpacing(10)

        # Top row: mode toggle & big timer
        top_layout = QHBoxLayout()
        self.lbl_mode = QLabel("🎯 Focus Time")
        self.lbl_mode.setStyleSheet("color: #FF453A; font-size: 12px; font-weight: bold;")

        self.btn_switch_mode = QPushButton("Switch to Break")
        self.btn_switch_mode.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                font-size: 10px;
                border-radius: 10px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
        """)
        self.btn_switch_mode.clicked.connect(self._switch_mode)

        top_layout.addWidget(self.lbl_mode)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_switch_mode)
        exp_layout.addLayout(top_layout)

        # Big timer display
        self.lbl_timer = QLabel("25:00")
        self.lbl_timer.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: bold;")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        exp_layout.addWidget(self.lbl_timer)

        # Controls row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_start = QPushButton("Start Focus")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #30D158;
                color: #000000;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #34C759;
            }
        """)
        self.btn_start.clicked.connect(self.toggle_timer)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3C;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #48484A;
            }
        """)
        self.btn_reset.clicked.connect(self.reset_timer)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_reset)
        exp_layout.addLayout(btn_layout)

        self.stack.addWidget(self.expanded_widget)
        self.stack.setCurrentIndex(0)

    def set_expanded_mode(self, expanded: bool):
        self.stack.setCurrentIndex(1 if expanded else 0)

    def _switch_mode(self):
        self.is_work_mode = not self.is_work_mode
        if self.is_work_mode:
            self.remaining_seconds = self.work_seconds
            self.lbl_mode.setText("🎯 Focus Time")
            self.lbl_mode.setStyleSheet("color: #FF453A; font-size: 12px; font-weight: bold;")
            self.btn_switch_mode.setText("Switch to Break")
            self.compact_label.setStyleSheet("color: #FF453A; font-size: 11px; font-weight: bold;")
        else:
            self.remaining_seconds = self.break_seconds
            self.lbl_mode.setText("☕ Rest Break")
            self.lbl_mode.setStyleSheet("color: #30D158; font-size: 12px; font-weight: bold;")
            self.btn_switch_mode.setText("Switch to Focus")
            self.compact_label.setStyleSheet("color: #30D158; font-size: 11px; font-weight: bold;")

        self.pause_timer()
        self._update_display()

    def toggle_timer(self):
        if self.is_running:
            self.pause_timer()
        else:
            self.start_timer()

    def start_timer(self):
        self.is_running = True
        self.btn_start.setText("Pause")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #FF9F0A;
                color: #000000;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                padding: 6px 16px;
            }
        """)
        self._tick_timer.start(1000)

    def pause_timer(self):
        self.is_running = False
        self.btn_start.setText("Resume" if self.remaining_seconds < (self.work_seconds if self.is_work_mode else self.break_seconds) else "Start")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #30D158;
                color: #000000;
                font-size: 12px;
                font-weight: bold;
                border-radius: 12px;
                padding: 6px 16px;
            }
        """)
        self._tick_timer.stop()

    def reset_timer(self):
        self.pause_timer()
        self.remaining_seconds = self.work_seconds if self.is_work_mode else self.break_seconds
        self.btn_start.setText("Start")
        self._update_display()

    def _on_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self._update_display()
        else:
            self.pause_timer()
            msg = "Focus session completed! Take a break." if self.is_work_mode else "Break is over! Time to focus."
            self._chime()
            self.timer_finished.emit(msg)
            self._switch_mode()

    def _chime(self):
        try:
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _update_display(self):
        m = self.remaining_seconds // 60
        s = self.remaining_seconds % 60
        time_str = f"{m:02d}:{s:02d}"
        icon = "🍅" if self.is_work_mode else "☕"
        self.compact_label.setText(f"{icon} {time_str}")
        self.lbl_timer.setText(time_str)
