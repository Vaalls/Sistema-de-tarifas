# ==================================
# ui/main/sidebar.py — Sidebar (nav)
# ==================================
from django.dispatch import Signal
from app.core.i18n.i18n import I18n
from PySide6.QtWidgets import (
    QVBoxLayout, QPushButton, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal


class Sidebar(QFrame):
    navigate = Signal(str)

    def __init__(self, i18n: I18n):
        super().__init__(objectName="Surface")
        self.i18n = i18n
        lay = QVBoxLayout(self); 
        lay.setContentsMargins(12,12,12,12); 
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignTop)

        self.btn_home = QPushButton(self.i18n.tr("menu.home"))
        self.btn_repique = QPushButton(self.i18n.tr("menu.repique"))
        self.btn_cgm = QPushButton(self.i18n.tr("menu.cgm"))
        self.btn_fato = QPushButton(self.i18n.tr("menu.fato"))
        self.btn_cockpit = QPushButton(self.i18n.tr("menu.cockpit"))
        self.btn_dashboard = QPushButton(self.i18n.tr("menu.dashboard"))
        self.btn_cancel = QPushButton(self.i18n.tr("menu.cancel"))
        for b in (self.btn_home, self.btn_repique, self.btn_cgm, self.btn_fato, self.btn_cockpit, self.btn_cancel, self.btn_dashboard):
            b.setMinimumHeight(36)
            lay.addWidget(b)
        lay.addStretch()
        # após criar os botões
        for b in (self.btn_home, self.btn_dashboard, self.btn_repique, self.btn_cgm, self.btn_fato, self.btn_cockpit, self.btn_cancel):
            b.setMinimumHeight(36)
            b.setProperty("role", "sidebar")        # ← aplica QSS do sidebar
            b.style().unpolish(b); b.style().polish(b)  # reaplicar estilo
            lay.addWidget(b)
        
        lay.addStretch()

        # Conexões
        self.btn_home.clicked.connect(lambda: self.navigate.emit("home"))
        self.btn_repique.clicked.connect(lambda: self.navigate.emit("repique"))
        self.btn_dashboard.clicked.connect(lambda: self.navigate.emit("dashboard"))
        self.btn_cgm.clicked.connect(lambda: self.navigate.emit("cgm"))
        self.btn_fato.clicked.connect(lambda: self.navigate.emit("fato"))
        self.btn_cockpit.clicked.connect(lambda: self.navigate.emit("cockpit"))
        self.btn_cancel.clicked.connect(lambda: self.navigate.emit("cancel"))
        self.btn_dashboard.clicked.connect(lambda: self.navigate.emit("dashboard"))

        for b in (self.btn_home, self.btn_repique, self.btn_cgm, self.btn_fato, self.btn_cockpit, self.btn_cancel, self.btn_dashboard):
            b.setCursor(Qt.PointingHandCursor)  # Muda cursor para mãozinha