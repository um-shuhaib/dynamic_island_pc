"""System resource monitor widget for Dynamic Island."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QStackedWidget,
    QGridLayout,
)


class SystemView(QWidget):
    """System monitor widget showing CPU, RAM, Battery, and Network metrics."""

    def __init__(self, system_monitor, parent=None):
        super().__init__(parent)
        self.monitor = system_monitor
        self._setup_ui()

        if self.monitor:
            self.monitor.stats_updated.connect(self.update_stats)
            self.monitor.start()

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
        compact_layout.setSpacing(8)

        self.compact_cpu_label = QLabel("⚡ 0%")
        self.compact_cpu_label.setStyleSheet("color: #30D158; font-size: 11px; font-weight: bold;")

        self.compact_ram_label = QLabel("🧠 0%")
        self.compact_ram_label.setStyleSheet("color: #0A84FF; font-size: 11px; font-weight: bold;")

        self.compact_bat_label = QLabel("🔋 100%")
        self.compact_bat_label.setStyleSheet("color: #FFD60A; font-size: 11px; font-weight: bold;")

        compact_layout.addWidget(self.compact_cpu_label)
        compact_layout.addWidget(self.compact_ram_label)
        compact_layout.addWidget(self.compact_bat_label)
        self.stack.addWidget(self.compact_widget)

        # 1: Expanded View
        self.expanded_widget = QWidget()
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(16, 12, 16, 12)
        exp_layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)

        # CPU row
        self.lbl_cpu_title = QLabel("CPU")
        self.lbl_cpu_title.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: bold;")
        self.bar_cpu = self._create_bar("#30D158")
        self.lbl_cpu_val = QLabel("0%")
        self.lbl_cpu_val.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold;")
        self.lbl_cpu_val.setAlignment(Qt.AlignmentFlag.AlignRight)

        grid.addWidget(self.lbl_cpu_title, 0, 0)
        grid.addWidget(self.bar_cpu, 0, 1)
        grid.addWidget(self.lbl_cpu_val, 0, 2)

        # RAM row
        self.lbl_ram_title = QLabel("RAM")
        self.lbl_ram_title.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: bold;")
        self.bar_ram = self._create_bar("#0A84FF")
        self.lbl_ram_val = QLabel("0.0 / 0.0 GB")
        self.lbl_ram_val.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold;")
        self.lbl_ram_val.setAlignment(Qt.AlignmentFlag.AlignRight)

        grid.addWidget(self.lbl_ram_title, 1, 0)
        grid.addWidget(self.bar_ram, 1, 1)
        grid.addWidget(self.lbl_ram_val, 1, 2)

        # Battery row
        self.lbl_bat_title = QLabel("Battery")
        self.lbl_bat_title.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: bold;")
        self.bar_bat = self._create_bar("#FFD60A")
        self.lbl_bat_val = QLabel("100%")
        self.lbl_bat_val.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold;")
        self.lbl_bat_val.setAlignment(Qt.AlignmentFlag.AlignRight)

        grid.addWidget(self.lbl_bat_title, 2, 0)
        grid.addWidget(self.bar_bat, 2, 1)
        grid.addWidget(self.lbl_bat_val, 2, 2)

        # Network row
        self.lbl_net_title = QLabel("Network")
        self.lbl_net_title.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: bold;")
        self.lbl_net_val = QLabel("↓ 0.0 KB/s   ↑ 0.0 KB/s")
        self.lbl_net_val.setStyleSheet("color: #64D2FF; font-size: 11px; font-weight: bold;")

        grid.addWidget(self.lbl_net_title, 3, 0)
        grid.addWidget(self.lbl_net_val, 3, 1, 1, 2)

        exp_layout.addLayout(grid)
        self.stack.addWidget(self.expanded_widget)
        self.stack.setCurrentIndex(0)

    def _create_bar(self, color: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #2C2C2E;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        return bar

    def set_expanded_mode(self, expanded: bool):
        self.stack.setCurrentIndex(1 if expanded else 0)

    def update_stats(self, stats: dict):
        cpu = stats.get("cpu_percent", 0.0)
        ram = stats.get("ram_percent", 0.0)
        ram_used = stats.get("ram_used_gb", 0.0)
        ram_total = stats.get("ram_total_gb", 0.0)
        bat = stats.get("battery_percent")
        plugged = stats.get("battery_plugged", False)
        net_down = stats.get("net_down_kb", 0.0)
        net_up = stats.get("net_up_kb", 0.0)

        # Compact labels
        self.compact_cpu_label.setText(f"⚡ {int(cpu)}%")
        self.compact_ram_label.setText(f"🧠 {int(ram)}%")
        if bat is not None:
            bolt = "⚡" if plugged else ""
            self.compact_bat_label.setText(f"🔋{bolt} {int(bat)}%")
            self.compact_bat_label.setVisible(True)
        else:
            self.compact_bat_label.setVisible(False)

        # Expanded view
        self.bar_cpu.setValue(int(cpu))
        self.lbl_cpu_val.setText(f"{cpu:.1f}%")

        self.bar_ram.setValue(int(ram))
        self.lbl_ram_val.setText(f"{ram_used:.1f} / {ram_total:.1f} GB")

        if bat is not None:
            self.bar_bat.setValue(int(bat))
            bolt = " ⚡" if plugged else ""
            self.lbl_bat_val.setText(f"{int(bat)}%{bolt}")
            self.lbl_bat_title.setVisible(True)
            self.bar_bat.setVisible(True)
            self.lbl_bat_val.setVisible(True)
        else:
            self.lbl_bat_title.setVisible(False)
            self.bar_bat.setVisible(False)
            self.lbl_bat_val.setVisible(False)

        # Network formatting
        down_str = f"{net_down:.1f} KB/s" if net_down < 1000 else f"{net_down/1024:.1f} MB/s"
        up_str = f"{net_up:.1f} KB/s" if net_up < 1000 else f"{net_up/1024:.1f} MB/s"
        self.lbl_net_val.setText(f"↓ {down_str}   ↑ {up_str}")
