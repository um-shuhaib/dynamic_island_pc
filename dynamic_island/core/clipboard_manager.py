"""Clipboard history monitor using QClipboard."""
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class ClipboardManager(QObject):
    """Monitors system clipboard changes and maintains recent history."""

    history_changed = pyqtSignal(list)
    new_clip_added = pyqtSignal(str)

    def __init__(self, max_history: int = 15, parent=None):
        super().__init__(parent)
        self.max_history = max_history
        self._history = deque(maxlen=max_history)
        self._last_text = ""
        self._clipboard = None

    def start(self):
        """Start listening to clipboard events."""
        app = QApplication.instance()
        if app:
            self._clipboard = app.clipboard()
            self._clipboard.dataChanged.connect(self._on_clipboard_changed)
            # Read initial clipboard
            initial_text = self._clipboard.text()
            if initial_text and initial_text.strip():
                self._last_text = initial_text
                self._history.appendleft(initial_text)

    def _on_clipboard_changed(self):
        if not self._clipboard:
            return
        text = self._clipboard.text()
        if text and text.strip() and text != self._last_text:
            self._last_text = text
            # Avoid duplicate consecutive entries
            if text in self._history:
                self._history.remove(text)
            self._history.appendleft(text)
            self.new_clip_added.emit(text)
            self.history_changed.emit(list(self._history))

    def copy_text(self, text: str):
        """Programmatically copy text to clipboard."""
        if self._clipboard:
            self._last_text = text
            self._clipboard.setText(text)

    def clear(self):
        self._history.clear()
        self.history_changed.emit([])

    def get_history(self) -> list:
        return list(self._history)
