"""System tray icon and context menu."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def create_tray_icon_pixmap() -> QPixmap:
    """Generate a clean dark pill icon for the system tray."""
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Black pill
    painter.setBrush(QBrush(QColor("#000000")))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 10, 24, 12, 6, 6)

    # Mini cyan dot
    painter.setBrush(QBrush(QColor("#0A84FF")))
    painter.drawEllipse(8, 14, 4, 4)

    painter.end()
    return pix


class IslandTrayIcon(QSystemTrayIcon):
    """System tray manager for background status and options."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setIcon(QIcon(create_tray_icon_pixmap()))
        self.setToolTip("Dynamic Island Desktop")

        self._setup_menu()
        self.activated.connect(self._on_tray_activated)

    def _setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: 1px solid #2C2C2E;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0A84FF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #2C2C2E;
                margin: 4px 8px;
            }
        """)

        action_toggle = menu.addAction("🏝️ Toggle Dynamic Island")
        action_toggle.triggered.connect(self._toggle_visibility)

        action_setup = menu.addAction("⚙️ Setup & Calibration Wizard")
        action_setup.triggered.connect(self.main_window.open_calibration_wizard)

        menu.addSeparator()

        action_quit = menu.addAction("❌ Exit")
        action_quit.triggered.connect(self.main_window.close_application)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self):
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
