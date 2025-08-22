# ======================================
# ui/modules/home/views/home_view.py — UI
# ======================================

from __future__ import annotations
from logging import root
from PySide6.QtCore import Qt, Signal
from django.dispatch import Signal
from app.core.i18n.i18n import I18n
from app.ui.modules.home.viewmodels.home_vm import HomeViewModel
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QGridLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView
)

class HomeView(QWidget):

    new_repique = Signal()

    def __init__(self, i18n: I18n):
        super().__init__()
        self.i18n = i18n
        self.vm = HomeViewModel(i18n)
        self._build()
        


    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(10)

        # KPIs (como cards)
        kpi_frame = QFrame(objectName="Surface")
        kpi_lay = QGridLayout(kpi_frame); kpi_lay.setContentsMargins(12, 12, 12, 12)
        col = 0
        for label, value in self.vm.kpis().items():
            box = QVBoxLayout();
            t = QLabel(label); t.setStyleSheet("color:#8B98A5;")
            v = QLabel(str(value)); v.setStyleSheet("font-size:22px; font-weight:600;")
            c = QFrame(); bl = QVBoxLayout(c); bl.addWidget(t); bl.addWidget(v)
            c.setFrameShape(QFrame.NoFrame)
            kpi_lay.addWidget(c, 0, col)
            col += 1
    
        # Recentes (tabela)
        table_title = QLabel(self.i18n.tr("recent"))
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Tipo", "ID", "Cliente", "Data", "Status", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self._populate_table()

        view_all = QPushButton(self.i18n.tr("view.all"))
        view_all.setFixedWidth(120)

        root.addWidget(kpi_frame)
        root.addWidget(table_title)
        root.addWidget(self.table)
        root.addWidget(view_all, alignment=Qt.AlignRight)

    def _populate_table(self):
        items = self.vm.recentes()
        self.table.setRowCount(len(items))
        for r, it in enumerate(items):
            self.table.setItem(r, 0, QTableWidgetItem(it.tipo))
            self.table.setItem(r, 1, QTableWidgetItem(it.id))
            self.table.setItem(r, 2, QTableWidgetItem(it.cliente))
            self.table.setItem(r, 3, QTableWidgetItem(it.data))
            self.table.setItem(r, 4, QTableWidgetItem(it.status))
            btn = QPushButton("Abrir")
            self.table.setCellWidget(r, 5, btn)