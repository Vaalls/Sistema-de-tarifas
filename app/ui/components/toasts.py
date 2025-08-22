# ========================================
# ui/components/toast.py — Toast simples
# ========================================
from PySide6.QtWidgets import ( QWidget, QHBoxLayout,
QLabel,  QDialog, QFrame )
from PySide6.QtCore import (Qt, QTimer)

class Toast(QDialog):
    def __init__(self, parent: QWidget, text: str):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        lay = QHBoxLayout(self)
        frame = QFrame(objectName="Surface")
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.addWidget(QLabel(text))
        lay.addWidget(frame)

    def show_at(self, x: int, y: int, duration_ms: int = 2500):    
        self.adjustSize()
        self.move(x, y)
        self.show()
        QTimer.singleShot(duration_ms, self.close)

    
    def show_centered_in(self, widget, duration_ms: int = 2500):
        self.adjustSize()
        top = widget.window()
        center = top.geometry().center()
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        self.show()
        QTimer.singleShot(duration_ms, self.close)