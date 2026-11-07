"""Application entry point for Dynamic Island Desktop."""
import os
import sys
import argparse
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Ensure X11/XWayland backend on Linux for frameless transparency and positioning
if sys.platform.startswith("linux"):
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

from .config import config
from .ui.island_window import DynamicIslandWindow
from .ui.tray_icon import IslandTrayIcon


def main():
    parser = argparse.ArgumentParser(description="Dynamic Island Desktop Overlay")
    parser.add_argument(
        "--setup",
        "--calibrate",
        action="store_true",
        help="Open the visual calibration wizard immediately on startup",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("DynamicIslandDesktop")
    app.setQuitOnLastWindowClosed(False)

    # High DPI scaling
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Create main island window
    window = DynamicIslandWindow()
    window.show()

    # Create system tray icon
    tray_icon = IslandTrayIcon(window)
    tray_icon.show()

    # If explicitly requested via CLI flag, open calibration wizard
    if args.setup:
        window.open_calibration_wizard()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
