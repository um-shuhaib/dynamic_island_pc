"""Clipboard history viewer for Dynamic Island."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QScrollArea,
)


class ClipboardItemButton(QPushButton):
    """Button representing a single clipboard history snippet."""

    def __init__(self, text: str, on_copy_callback, parent=None):
        super().__init__(parent)
        self.raw_text = text
        self.on_copy = on_copy_callback

        display_text = text.strip().replace("\n", " ")
        if len(display_text) > 45:
            display_text = display_text[:42] + "…"
        self.setText(display_text)

        self.setStyleSheet("""
            QPushButton {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid #2C2C2E;
                border-radius: 8px;
                padding: 6px 10px;
                text-align: left;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2C2C2E;
                border-color: #0A84FF;
            }
            QPushButton:pressed {
                background-color: #0A84FF;
            }
        """)
        self.clicked.connect(self._handle_click)

    def _handle_click(self):
        self.on_copy(self.raw_text)
        prev_text = self.text()
        self.setText("✓ Copied!")
        self.setStyleSheet("""
            QPushButton {
                background-color: #30D158;
                color: #000000;
                font-weight: bold;
                border-radius: 8px;
                padding: 6px 10px;
                text-align: left;
                font-size: 11px;
            }
        """)


class ClipboardView(QWidget):
    """Clipboard history widget for compact and expanded Dynamic Island."""

    def __init__(self, clipboard_mgr, parent=None):
        super().__init__(parent)
        self.mgr = clipboard_mgr
        self._setup_ui()

        if self.mgr:
            self.mgr.history_changed.connect(self.update_history)
            self.mgr.start()

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

        self.compact_label = QLabel("📋 0 clips")
        self.compact_label.setStyleSheet("color: #BF5AF2; font-size: 11px; font-weight: bold;")
        compact_layout.addWidget(self.compact_label)
        self.stack.addWidget(self.compact_widget)

        # 1: Expanded View
        self.expanded_widget = QWidget()
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(14, 10, 14, 10)
        exp_layout.setSpacing(8)

        top_row = QHBoxLayout()
        lbl_title = QLabel("📋 Clipboard History")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")

        btn_clear = QPushButton("Clear")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF453A;
                font-size: 10px;
                border: none;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        btn_clear.clicked.connect(self._clear_all)

        top_row.addWidget(lbl_title)
        top_row.addStretch()
        top_row.addWidget(btn_clear)
        exp_layout.addLayout(top_row)

        # Scroll area for items
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #1C1C1E;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #3A3A3C;
                border-radius: 3px;
            }
        """)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(4)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.items_container)
        exp_layout.addWidget(self.scroll, stretch=1)

        self.stack.addWidget(self.expanded_widget)
        self.stack.setCurrentIndex(0)

    def set_expanded_mode(self, expanded: bool):
        self.stack.setCurrentIndex(1 if expanded else 0)

    def update_history(self, history: list):
        self.compact_label.setText(f"📋 {len(history)} clips")

        # Clear existing buttons
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not history:
            empty_lbl = QLabel("Clipboard is empty")
            empty_lbl.setStyleSheet("color: #8E8E93; font-size: 11px;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_layout.addWidget(empty_lbl)
            return

        for text in history:
            btn = ClipboardItemButton(text, self._copy_item)
            self.items_layout.addWidget(btn)

    def _copy_item(self, text: str):
        if self.mgr:
            self.mgr.copy_text(text)

    def _clear_all(self):
        if self.mgr:
            self.mgr.clear()
