"""Core Dynamic Island floating window with squircle geometry, date/time, and zero-click hover engine."""
import sys
from datetime import datetime
from PyQt6.QtCore import (
    Qt,
    QRect,
    QVariantAnimation,
    QEasingCurve,
    QTimer,
    QPoint,
    QEvent,
)
from PyQt6.QtGui import QGuiApplication, QCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QMenu,
    QApplication,
    QLabel,
)

from ..config import config
from ..core.media.media_controller import create_media_controller
from ..core.media.base import MediaInfo
from ..core.system_monitor import SystemMonitorThread
from ..core.clipboard_manager import ClipboardManager
from ..core.fullscreen import FullscreenDetectorThread
from .widgets.pill_base import IslandPillBase
from .widgets.clock_view import ClockView
from .widgets.media_view import MediaView, AnimatedWaveform
from .widgets.system_view import SystemView
from .widgets.pomodoro_view import PomodoroView
from .widgets.clipboard_view import ClipboardView
from .widgets.alert_banner import AlertBannerView
from .calibration_wizard import CalibrationWizard


class DynamicIslandWindow(QWidget):
    """Floating, frameless, translucent Dynamic Island window with zero-click hover morphing."""

    STATE_COMPACT = 0
    STATE_EXPANDED = 1
    STATE_ALERT = 2

    def __init__(self):
        super().__init__()
        self.current_state = self.STATE_COMPACT
        self._is_animating = False
        self._is_hidden_by_fullscreen = False
        self._outside_count = 0
        self._menu_open = False
        self._scroll_accum = 0
        self._scroll_locked = False

        self._init_window_flags()
        self._init_backend_services()
        self._setup_ui()
        self._connect_signals()
        self._init_animations()
        self._init_hover_polling()

        # Install event filter on app to capture mouse wheel scroll anywhere on the island
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        # Apply initial geometry
        self._apply_geometry_from_config(animate=False)

        # Fullscreen detector
        if config.get("auto_hide_fullscreen", True):
            self.fullscreen_detector = FullscreenDetectorThread(self)
            self.fullscreen_detector.fullscreen_changed.connect(self._on_fullscreen_changed)
            self.fullscreen_detector.start()
        else:
            self.fullscreen_detector = None

    def _init_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)

    def _init_backend_services(self):
        self.media_ctrl = create_media_controller(self)
        self.system_mon = SystemMonitorThread(self)
        self.clip_mgr = ClipboardManager(parent=self)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Base pill background
        self.pill = IslandPillBase(self)
        self.pill_layout = QVBoxLayout(self.pill)
        self.pill_layout.setContentsMargins(0, 0, 0, 0)
        self.pill_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 0. Compact View (Small pill showing Date & Time)
        # -------------------------------------------------------------
        self.compact_container = QWidget(self.pill)
        self.compact_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        compact_layout = QHBoxLayout(self.compact_container)
        compact_layout.setContentsMargins(12, 2, 12, 2)
        compact_layout.setSpacing(8)

        # Mini Waveform
        self.compact_waveform = AnimatedWaveform(self.compact_container)
        self.compact_waveform.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.compact_waveform.setVisible(False)
        compact_layout.addWidget(self.compact_waveform)

        # Time label (e.g., 10:45 AM)
        self.compact_time_label = QLabel("12:00 PM", self.compact_container)
        self.compact_time_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.compact_time_label.setStyleSheet(
            "color: #FFFFFF; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;"
        )
        self.compact_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compact_layout.addWidget(self.compact_time_label)

        # Divider dot
        self.compact_dot = QLabel("•", self.compact_container)
        self.compact_dot.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.compact_dot.setStyleSheet("color: #48484A; font-size: 11px;")
        compact_layout.addWidget(self.compact_dot)

        # Date label (e.g., Sat, Nov 7)
        self.compact_date_label = QLabel("Nov 7", self.compact_container)
        self.compact_date_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.compact_date_label.setStyleSheet(
            "color: #0A84FF; font-size: 11px; font-weight: 600;"
        )
        self.compact_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compact_layout.addWidget(self.compact_date_label)

        self.pill_layout.addWidget(self.compact_container)

        # -------------------------------------------------------------
        # 1. Expanded View Drawer
        # -------------------------------------------------------------
        self.expanded_container = QWidget(self.pill)
        exp_layout = QVBoxLayout(self.expanded_container)
        exp_layout.setContentsMargins(10, 8, 10, 8)
        exp_layout.setSpacing(6)

        # Top Navigation Tabs
        self.tabs_bar = QHBoxLayout()
        self.tabs_bar.setSpacing(4)
        self.tabs_bar.setContentsMargins(2, 0, 2, 0)

        tab_style = """
            QPushButton {
                background-color: transparent;
                color: #8E8E93;
                font-size: 11px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background-color: #2C2C2E;
            }
            QPushButton:checked {
                color: #FFFFFF;
                background-color: #3A3A3C;
            }
        """

        self.btn_tab_clock = QPushButton("🕒 Clock")
        self.btn_tab_clock.setCheckable(True)
        self.btn_tab_clock.setChecked(True)
        self.btn_tab_clock.setStyleSheet(tab_style)
        self.btn_tab_clock.clicked.connect(lambda: self._select_tab(0))

        self.btn_tab_media = QPushButton("🎵 Media")
        self.btn_tab_media.setCheckable(True)
        self.btn_tab_media.setStyleSheet(tab_style)
        self.btn_tab_media.clicked.connect(lambda: self._select_tab(1))

        self.btn_tab_sys = QPushButton("⚡ System")
        self.btn_tab_sys.setCheckable(True)
        self.btn_tab_sys.setStyleSheet(tab_style)
        self.btn_tab_sys.clicked.connect(lambda: self._select_tab(2))

        self.btn_tab_pomo = QPushButton("⏱️ Focus")
        self.btn_tab_pomo.setCheckable(True)
        self.btn_tab_pomo.setStyleSheet(tab_style)
        self.btn_tab_pomo.clicked.connect(lambda: self._select_tab(3))

        self.btn_tab_clip = QPushButton("📋 History")
        self.btn_tab_clip.setCheckable(True)
        self.btn_tab_clip.setStyleSheet(tab_style)
        self.btn_tab_clip.clicked.connect(lambda: self._select_tab(4))

        self.btn_collapse = QPushButton("✕")
        self.btn_collapse.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8E8E93;
                font-size: 12px;
                font-weight: bold;
                border: none;
                padding: 2px 6px;
            }
            QPushButton:hover {
                color: #FF453A;
            }
        """)
        self.btn_collapse.clicked.connect(self.collapse)

        self.tabs_bar.addWidget(self.btn_tab_clock)
        self.tabs_bar.addWidget(self.btn_tab_media)
        self.tabs_bar.addWidget(self.btn_tab_sys)
        self.tabs_bar.addWidget(self.btn_tab_pomo)
        self.tabs_bar.addWidget(self.btn_tab_clip)
        self.tabs_bar.addStretch()
        self.tabs_bar.addWidget(self.btn_collapse)
        exp_layout.addLayout(self.tabs_bar)

        # Expanded Views Stack
        self.exp_content_stack = QStackedWidget(self.expanded_container)

        self.clock_expanded = ClockView(self.exp_content_stack)
        self.media_expanded = MediaView(self.media_ctrl, self.exp_content_stack)
        self.media_expanded.set_expanded_mode(True)
        self.system_expanded = SystemView(self.system_mon, self.exp_content_stack)
        self.system_expanded.set_expanded_mode(True)
        self.pomodoro_expanded = PomodoroView(self.exp_content_stack)
        self.pomodoro_expanded.set_expanded_mode(True)
        self.clipboard_expanded = ClipboardView(self.clip_mgr, self.exp_content_stack)
        self.clipboard_expanded.set_expanded_mode(True)

        self.exp_content_stack.addWidget(self.clock_expanded)      # 0
        self.exp_content_stack.addWidget(self.media_expanded)      # 1
        self.exp_content_stack.addWidget(self.system_expanded)     # 2
        self.exp_content_stack.addWidget(self.pomodoro_expanded)   # 3
        self.exp_content_stack.addWidget(self.clipboard_expanded)  # 4
        exp_layout.addWidget(self.exp_content_stack, stretch=1)

        self.pill_layout.addWidget(self.expanded_container)

        # -------------------------------------------------------------
        # 2. Alert Banner View
        # -------------------------------------------------------------
        self.alert_widget = AlertBannerView(self.pill)
        self.alert_widget.alert_expired.connect(self.collapse)
        self.pill_layout.addWidget(self.alert_widget)

        main_layout.addWidget(self.pill)

        # Initial visibility states
        self.compact_container.setVisible(True)
        self.expanded_container.setVisible(False)
        self.alert_widget.setVisible(False)

        # Clock update timer for compact view
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_compact_time)
        self._clock_timer.start(1000)
        self._update_compact_time()

    def _init_hover_polling(self):
        """Active OS cursor position polling for 100% reliable zero-click hover expansion."""
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(35)  # 28 fps check
        self._hover_timer.timeout.connect(self._poll_cursor_hover)
        self._hover_timer.start()

    def _poll_cursor_hover(self):
        if self._is_hidden_by_fullscreen or self._menu_open or self._is_animating:
            return

        cursor_pos = QCursor.pos()
        geo = self.geometry()

        if self.current_state == self.STATE_COMPACT:
            # Generous 4px hitbox around the compact pill for effortless hover entry
            hit_box = geo.adjusted(-4, -4, 4, 4)
            if hit_box.contains(cursor_pos):
                self._outside_count = 0
                self.expand()
        elif self.current_state == self.STATE_EXPANDED:
            # 6px boundary around expanded drawer
            hit_box = geo.adjusted(-4, -4, 4, 8)
            if hit_box.contains(cursor_pos):
                self._outside_count = 0
            else:
                self._outside_count += 1
                # 5 ticks * 35ms = ~175ms of continuous exit before auto-collapsing
                if self._outside_count >= 5:
                    self.collapse()

    def _connect_signals(self):
        self.media_ctrl.media_updated.connect(self._on_media_updated)
        self.pomodoro_expanded.timer_finished.connect(
            lambda msg: self.trigger_alert(msg, title="Focus Timer", icon="🍅")
        )

    def _update_compact_time(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        date_str = now.strftime("%a, %b %d")
        self.compact_time_label.setText(time_str)
        self.compact_date_label.setText(date_str)

    def _on_media_updated(self, media: MediaInfo):
        if media.is_playing:
            self.compact_waveform.set_playing(True)
            self.compact_waveform.setVisible(True)
        else:
            self.compact_waveform.set_playing(False)
            self.compact_waveform.setVisible(False)

    def _init_animations(self):
        self.morph_anim = QVariantAnimation(self)
        self.morph_anim.setDuration(220)
        self.morph_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.morph_anim.valueChanged.connect(self._on_anim_step)
        self.morph_anim.finished.connect(self._on_anim_finished)

    def _select_tab(self, index: int):
        self.btn_tab_clock.setChecked(index == 0)
        self.btn_tab_media.setChecked(index == 1)
        self.btn_tab_sys.setChecked(index == 2)
        self.btn_tab_pomo.setChecked(index == 3)
        self.btn_tab_clip.setChecked(index == 4)
        self.exp_content_stack.setCurrentIndex(index)

    def _get_active_tab_indices(self) -> list:
        active = []
        mods = config.get("modules", {})
        if mods.get("clock", True):
            active.append(0)
        if mods.get("media", True):
            active.append(1)
        if mods.get("system", True):
            active.append(2)
        if mods.get("pomodoro", True):
            active.append(3)
        if mods.get("clipboard", True):
            active.append(4)
        return active if active else [0]

    def _cycle_tab(self, forward: bool):
        active_tabs = self._get_active_tab_indices()
        if not active_tabs:
            return

        current = self.exp_content_stack.currentIndex()
        if current in active_tabs:
            curr_pos = active_tabs.index(current)
        else:
            curr_pos = 0

        if forward:
            new_pos = (curr_pos + 1) % len(active_tabs)
        else:
            new_pos = (curr_pos - 1 + len(active_tabs)) % len(active_tabs)

        self._select_tab(active_tabs[new_pos])

    def _handle_scroll_delta(self, delta: int):
        if self._scroll_locked or self.current_state != self.STATE_EXPANDED:
            return

        self._scroll_accum += delta
        threshold = 60

        if self._scroll_accum <= -threshold:
            self._scroll_accum = 0
            self._scroll_locked = True
            self._cycle_tab(forward=True)
            QTimer.singleShot(140, self._unlock_scroll)
        elif self._scroll_accum >= threshold:
            self._scroll_accum = 0
            self._scroll_locked = True
            self._cycle_tab(forward=False)
            QTimer.singleShot(140, self._unlock_scroll)

    def _unlock_scroll(self):
        self._scroll_locked = False
        self._scroll_accum = 0

    def wheelEvent(self, event):
        if self.current_state == self.STATE_EXPANDED:
            delta = event.angleDelta().y()
            if delta == 0:
                delta = event.angleDelta().x()
            self._handle_scroll_delta(delta)
            event.accept()
        else:
            super().wheelEvent(event)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel:
            if self.current_state == self.STATE_EXPANDED:
                cursor_pos = QCursor.pos()
                if self.geometry().adjusted(-4, -4, 4, 8).contains(cursor_pos):
                    delta = event.angleDelta().y()
                    if delta == 0:
                        delta = event.angleDelta().x()
                    self._handle_scroll_delta(delta)
                    return True
        return super().eventFilter(watched, event)

    def _refresh_module_visibility(self):
        mods = config.get("modules", {})
        self.btn_tab_clock.setVisible(mods.get("clock", True))
        self.btn_tab_media.setVisible(mods.get("media", True))
        self.btn_tab_sys.setVisible(mods.get("system", True))
        self.btn_tab_pomo.setVisible(mods.get("pomodoro", True))
        self.btn_tab_clip.setVisible(mods.get("clipboard", True))

    def _calculate_target_geometry(self, state: int) -> QRect:
        screens = QGuiApplication.screens()
        mon_idx = config.get("monitor_index", 0)
        screen = screens[mon_idx] if 0 <= mon_idx < len(screens) else QGuiApplication.primaryScreen()
        geo = screen.geometry()

        top_offset = config.get("top_offset", 8)

        if state == self.STATE_COMPACT:
            w = config.get("compact_width", 200)
            h = config.get("compact_height", 34)
        elif state == self.STATE_EXPANDED:
            w = config.get("expanded_width", 390)
            h = config.get("expanded_height", 195)
        else:  # STATE_ALERT
            w = 320
            h = 44

        x = geo.x() + (geo.width() - w) // 2
        y = geo.y() + top_offset
        return QRect(x, y, w, h)

    def _apply_geometry_from_config(self, animate: bool = True):
        self._refresh_module_visibility()
        target = self._calculate_target_geometry(self.current_state)
        if animate:
            self._animate_to(target)
        else:
            self.setFixedSize(target.width(), target.height())
            self.move(target.x(), target.y())
            self.pill.set_radius(target.height() // 2 if self.current_state == self.STATE_COMPACT else 16)

    def _animate_to(self, target_rect: QRect):
        if self._is_animating:
            self.morph_anim.stop()

        self._is_animating = True
        self.morph_anim.setStartValue(self.geometry())
        self.morph_anim.setEndValue(target_rect)
        self.morph_anim.start()

    def _on_anim_step(self, val):
        rect = val
        self.setFixedSize(rect.width(), rect.height())
        self.move(rect.x(), rect.y())
        if self.current_state == self.STATE_COMPACT:
            self.pill.set_radius(rect.height() // 2)
        else:
            self.pill.set_radius(16)

    def _on_anim_finished(self):
        self._is_animating = False

    def expand(self):
        if self.current_state == self.STATE_EXPANDED:
            return
        self.current_state = self.STATE_EXPANDED

        # Switch container visibility
        self.compact_container.setVisible(False)
        self.alert_widget.setVisible(False)
        self.expanded_container.setVisible(True)

        self._apply_geometry_from_config(animate=True)

    def collapse(self):
        if self.current_state == self.STATE_COMPACT:
            return
        self.current_state = self.STATE_COMPACT

        # Switch container visibility
        self.expanded_container.setVisible(False)
        self.alert_widget.setVisible(False)
        self.compact_container.setVisible(True)

        self._apply_geometry_from_config(animate=True)

    def trigger_alert(self, message: str, title: str = "Notification", icon: str = "🔔"):
        self.current_state = self.STATE_ALERT
        self.compact_container.setVisible(False)
        self.expanded_container.setVisible(False)
        self.alert_widget.setVisible(True)

        self.alert_widget.show_alert(title, message, icon)
        self._apply_geometry_from_config(animate=True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def _show_context_menu(self, pos: QPoint):
        self._menu_open = True
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid #2C2C2E;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0A84FF;
            }
        """)

        action_toggle = menu.addAction("Collapse" if self.current_state == self.STATE_EXPANDED else "Expand")
        action_toggle.triggered.connect(self.collapse if self.current_state == self.STATE_EXPANDED else self.expand)

        action_calib = menu.addAction("⚙️ Setup & Calibration Wizard")
        action_calib.triggered.connect(self.open_calibration_wizard)

        menu.addSeparator()
        action_quit = menu.addAction("Exit Dynamic Island")
        action_quit.triggered.connect(self.close_application)

        menu.aboutToHide.connect(lambda: setattr(self, "_menu_open", False))
        menu.exec(pos)

    def open_calibration_wizard(self):
        wizard = CalibrationWizard(self)
        wizard.settings_applied.connect(lambda: self._apply_geometry_from_config(animate=True))
        wizard.test_expand_requested.connect(self._run_test_expand)
        wizard.exec()

    def _run_test_expand(self):
        self.expand()
        QTimer.singleShot(2500, self.collapse)

    def _on_fullscreen_changed(self, is_fullscreen: bool):
        if not config.get("auto_hide_fullscreen", True):
            return

        if is_fullscreen and not self._is_hidden_by_fullscreen:
            self._is_hidden_by_fullscreen = True
            self.hide()
        elif not is_fullscreen and self._is_hidden_by_fullscreen:
            self._is_hidden_by_fullscreen = False
            self.show()

    def closeEvent(self, event):
        self.close_application()
        super().closeEvent(event)

    def close_application(self):
        self._hover_timer.stop()
        if self.fullscreen_detector:
            self.fullscreen_detector.stop()
        self.system_mon.stop()
        self.media_ctrl.stop()
        QApplication.quit()
