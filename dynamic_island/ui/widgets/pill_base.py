"""Base container widget rendering the iconic iOS Dynamic Island squircle."""
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
from PyQt6.QtWidgets import QWidget


class IslandPillBase(QWidget):
    """Base background widget drawing the ultra-black rounded pill with subtle glow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_color = QColor(0, 0, 0, 250)
        self.border_color = QColor(48, 48, 52, 220)
        self.corner_radius = 17

    def set_radius(self, radius: int):
        self.corner_radius = radius
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0)
        radius = min(self.corner_radius, self.height() / 2.0)

        # Draw dark pill background
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(QPen(self.border_color, 1.2))
        painter.drawRoundedRect(rect, radius, radius)
