"""Interactive visual calibration & onboarding setup wizard."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QFont, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
    QCheckBox,
    QGroupBox,
    QScrollArea,
    QWidget,
)

from ..config import config
from ..core.autostart import AutoStartManager


class CalibrationWizard(QDialog):
    """Visual setup wizard to align and calibrate the Dynamic Island on any monitor."""

    settings_applied = pyqtSignal()
    test_expand_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dynamic Island — Setup & Calibration Wizard")
        self.setFixedSize(520, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #121214;
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }
            QLabel {
                color: #E5E5EA;
            }
            QGroupBox {
                background-color: #1C1C1E;
                border: 1px solid #2C2C2E;
                border-radius: 12px;
                margin-top: 14px;
                padding-top: 14px;
                font-weight: bold;
                color: #0A84FF;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #2C2C2E;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #0A84FF;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: 1px solid #555555;
                width: 16px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QCheckBox {
                color: #FFFFFF;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #3A3A3C;
                background-color: #2C2C2E;
            }
            QCheckBox::indicator:checked {
                background-color: #30D158;
                border-color: #30D158;
            }
        """)

        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        header_icon = QLabel("🏝️")
        header_icon.setFont(QFont("Segoe UI", 28))
        header_layout.addWidget(header_icon)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        lbl_title = QLabel("Dynamic Island Setup")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        lbl_sub = QLabel("Calibrate positioning, notch alignment, and features.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #8E8E93;")
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_sub)
        header_layout.addLayout(title_layout, stretch=1)
        main_layout.addLayout(header_layout)

        # Scrollable configuration area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Display & Monitor Selection
        grp_monitor = QGroupBox("1. Display Selection")
        mon_layout = QVBoxLayout(grp_monitor)
        self.combo_monitors = QComboBox()
        self._populate_monitors()
        mon_layout.addWidget(self.combo_monitors)
        layout.addWidget(grp_monitor)

        # 2. Notch & Sizing Alignment
        grp_align = QGroupBox("2. Sizing & Notch Alignment")
        align_layout = QVBoxLayout(grp_align)
        align_layout.setSpacing(10)

        # Top Offset (Notch margin)
        self.slider_top_offset, self.lbl_top_offset = self._create_slider_row(
            align_layout, "Top Margin Offset:", 0, 60, "px"
        )
        # Pill Width
        self.slider_width, self.lbl_width = self._create_slider_row(
            align_layout, "Compact Width:", 150, 320, "px"
        )
        # Pill Height
        self.slider_height, self.lbl_height = self._create_slider_row(
            align_layout, "Compact Height:", 26, 48, "px"
        )

        layout.addWidget(grp_align)

        # 3. Behavior & Integration
        grp_behav = QGroupBox("3. Behavior & Startup")
        behav_layout = QVBoxLayout(grp_behav)
        behav_layout.setSpacing(8)

        self.chk_autostart = QCheckBox("Launch automatically on system boot")
        self.chk_fullscreen = QCheckBox("Auto-hide when running full-screen games or video")
        self.chk_hover = QCheckBox("Expand preview on mouse hover (Click to pin)")

        behav_layout.addWidget(self.chk_autostart)
        behav_layout.addWidget(self.chk_fullscreen)
        behav_layout.addWidget(self.chk_hover)
        layout.addWidget(grp_behav)

        # 4. Enabled Modules
        grp_mods = QGroupBox("4. Active Modules")
        mods_layout = QVBoxLayout(grp_mods)
        mods_layout.setSpacing(8)

        self.chk_mod_clock = QCheckBox("🕒 Clock, Date & Calendar View")
        self.chk_mod_media = QCheckBox("🎵 Media Player (Spotify / Browser / OS Audio)")
        self.chk_mod_sys = QCheckBox("⚡ System Resource Monitor (CPU, RAM, Battery, Net)")
        self.chk_mod_pomo = QCheckBox("⏱️ Pomodoro Focus Timer")
        self.chk_mod_clip = QCheckBox("📋 Clipboard History Quick Access")

        mods_layout.addWidget(self.chk_mod_clock)
        mods_layout.addWidget(self.chk_mod_media)
        mods_layout.addWidget(self.chk_mod_sys)
        mods_layout.addWidget(self.chk_mod_pomo)
        mods_layout.addWidget(self.chk_mod_clip)
        layout.addWidget(grp_mods)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, stretch=1)

        # Action Buttons Row
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.btn_test = QPushButton("Test Live Expand")
        self.btn_test.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2E;
                color: #FFFFFF;
                border: 1px solid #3A3A3C;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3A3A3C;
            }
        """)
        self.btn_test.clicked.connect(self._on_test_clicked)

        self.btn_save = QPushButton("Save & Finish Setup")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0071E3;
            }
        """)
        self.btn_save.clicked.connect(self._on_save_clicked)

        action_layout.addWidget(self.btn_test)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_save)
        main_layout.addLayout(action_layout)

    def _create_slider_row(self, parent_layout, label_text: str, min_val: int, max_val: int, unit: str):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #FFFFFF; font-size: 12px;")

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)

        val_lbl = QLabel(f"{min_val}{unit}")
        val_lbl.setFixedWidth(50)
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        val_lbl.setStyleSheet("color: #0A84FF; font-weight: bold; font-size: 12px;")

        slider.valueChanged.connect(lambda v: val_lbl.setText(f"{v}{unit}"))

        row.addWidget(lbl)
        row.addWidget(slider, stretch=1)
        row.addWidget(val_lbl)
        parent_layout.addLayout(row)
        return slider, val_lbl

    def _populate_monitors(self):
        self.combo_monitors.clear()
        screens = QGuiApplication.screens()
        for idx, screen in enumerate(screens):
            geo = screen.geometry()
            primary = " (Primary)" if screen == QGuiApplication.primaryScreen() else ""
            self.combo_monitors.addItem(
                f"Display {idx + 1}: {screen.name()} [{geo.width()}x{geo.height()}]{primary}",
                idx,
            )

    def _load_current_values(self):
        cfg = config.get_dict()
        mon_idx = cfg.get("monitor_index", 0)
        if 0 <= mon_idx < self.combo_monitors.count():
            self.combo_monitors.setCurrentIndex(mon_idx)

        top_offset = cfg.get("top_offset", 8)
        self.slider_top_offset.setValue(top_offset)
        self.lbl_top_offset.setText(f"{top_offset}px")

        c_width = cfg.get("compact_width", 200)
        self.slider_width.setValue(c_width)
        self.lbl_width.setText(f"{c_width}px")

        c_height = cfg.get("compact_height", 34)
        self.slider_height.setValue(c_height)
        self.lbl_height.setText(f"{c_height}px")

        self.chk_autostart.setChecked(AutoStartManager.is_enabled())
        self.chk_fullscreen.setChecked(cfg.get("auto_hide_fullscreen", True))
        self.chk_hover.setChecked(cfg.get("hover_expand", False))

        mods = cfg.get("modules", {})
        self.chk_mod_clock.setChecked(mods.get("clock", True))
        self.chk_mod_media.setChecked(mods.get("media", True))
        self.chk_mod_sys.setChecked(mods.get("system", True))
        self.chk_mod_pomo.setChecked(mods.get("pomodoro", True))
        self.chk_mod_clip.setChecked(mods.get("clipboard", True))

    def _on_test_clicked(self):
        self._apply_to_config(temporary=True)
        self.test_expand_requested.emit()

    def _apply_to_config(self, temporary: bool = False):
        config.set("monitor_index", self.combo_monitors.currentIndex(), auto_save=not temporary)
        config.set("top_offset", self.slider_top_offset.value(), auto_save=not temporary)
        config.set("compact_width", self.slider_width.value(), auto_save=not temporary)
        config.set("compact_height", self.slider_height.value(), auto_save=not temporary)
        config.set("auto_hide_fullscreen", self.chk_fullscreen.isChecked(), auto_save=not temporary)
        config.set("hover_expand", self.chk_hover.isChecked(), auto_save=not temporary)

        mods = {
            "clock": self.chk_mod_clock.isChecked(),
            "media": self.chk_mod_media.isChecked(),
            "system": self.chk_mod_sys.isChecked(),
            "pomodoro": self.chk_mod_pomo.isChecked(),
            "clipboard": self.chk_mod_clip.isChecked(),
        }
        config.set("modules", mods, auto_save=not temporary)

        if not temporary:
            # Commit autostart
            enable_auto = self.chk_autostart.isChecked()
            AutoStartManager.set_enabled(enable_auto)
            config.set("autostart", enable_auto, auto_save=False)
            config.set("first_run_completed", True, auto_save=True)

        self.settings_applied.emit()

    def _on_save_clicked(self):
        self._apply_to_config(temporary=False)
        self.accept()
