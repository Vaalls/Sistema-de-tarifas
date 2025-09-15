# ==================================
# ui/main/sidebar.py — Sidebar (nav)
# ==================================
from app.core.i18n.i18n import I18n
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal

class Sidebar(QFrame):
    navigate = Signal(str)

    def __init__(self, i18n: I18n):
        super().__init__(objectName="Surface")
        self.i18n = i18n

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignTop)

        self.btn_home      = QPushButton(self.i18n.tr("menu.home"))
        self.btn_repique   = QPushButton(self.i18n.tr("menu.repique"))
        self.btn_cgm       = QPushButton(self.i18n.tr("menu.cgm"))
        self.btn_fato      = QPushButton(self.i18n.tr("menu.fato"))
        self.btn_docs   = QPushButton(self.i18n.tr("menu.docs"))
        self.btn_dashboard = QPushButton(self.i18n.tr("menu.dashboard"))
        self.btn_cancel    = QPushButton(self.i18n.tr("menu.cancel"))

        for b in (self.btn_home, self.btn_repique, self.btn_cgm, self.btn_fato,
                  self.btn_docs, self.btn_dashboard, self.btn_cancel):
            b.setMinimumHeight(36)
            b.setProperty("role", "sidebar")
            b.setCursor(Qt.PointingHandCursor)
            b.style().unpolish(b); b.style().polish(b)
            lay.addWidget(b)

        lay.addStretch()

        # Conexões
        self.btn_home.clicked.connect(lambda: self.navigate.emit("home"))
        self.btn_repique.clicked.connect(lambda: self.navigate.emit("repique"))
        self.btn_cgm.clicked.connect(lambda: self.navigate.emit("cgm"))
        self.btn_fato.clicked.connect(lambda: self.navigate.emit("fato"))
        self.btn_docs.clicked.connect(lambda: self.navigate.emit("docs"))
        self.btn_dashboard.clicked.connect(lambda: self.navigate.emit("dashboard"))
        self.btn_cancel.clicked.connect(lambda: self.navigate.emit("cancel"))
