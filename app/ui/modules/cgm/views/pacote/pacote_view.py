from __future__ import annotations
from typing import List, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)

class PacoteView(QWidget):
    open_cadastro = Signal()
    open_consulta = Signal()
    go_back = Signal()
    open_registro = Signal(dict)

    def __init__(self):
        super().__init__()
        self._kpi1 = QLabel("0"); self._kpi2 = QLabel("0")
        self.table: QTableWidget
        self._build()

    def _gold_btn(self, text, w=220, h=52):
        b = QPushButton(text); b.setProperty("accent","true")
        b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton { border-radius:8px; } QPushButton:hover{background:#C49A2E;}")
        return b

    def _kpi_card(self, title: str, vref: QLabel, action_text: str, slot):
        card = QFrame(objectName="Surface"); card.setFixedWidth(520)
        lay = QVBoxLayout(card); lay.setContentsMargins(16,18,16,18); lay.setSpacing(10)
        t = QLabel(title); t.setAlignment(Qt.AlignHCenter)
        t.setStyleSheet("color:#8B98A5; background:transparent;")
        vref.setAlignment(Qt.AlignHCenter)
        vref.setStyleSheet("font-size:28px; font-weight:700; background:transparent;")
        btn = self._gold_btn(action_text); btn.clicked.connect(slot)
        lay.addWidget(t); lay.addWidget(vref)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(btn); row.addStretch()
        lay.addLayout(row)
        return card

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(18); root.setAlignment(Qt.AlignTop)

        top = QHBoxLayout(); top.addStretch()
        back = self._gold_btn("Voltar ao CGM", 160, 40); back.clicked.connect(self.go_back.emit)
        top.addWidget(back, 0, Qt.AlignRight); root.addLayout(top)

        actions = QHBoxLayout(); actions.setSpacing(20); actions.setAlignment(Qt.AlignHCenter)
        actions.addWidget(self._kpi_card("Registros hoje", self._kpi1, "Cadastro", self.open_cadastro.emit))
        actions.addWidget(self._kpi_card("Pendentes de revisão", self._kpi2, "Consulta", self.open_consulta.emit))
        root.addLayout(actions)

        card = QFrame(objectName="Surface")
        lay = QVBoxLayout(card); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)
        t = QLabel("Últimos cadastros"); t.setStyleSheet("font-weight:700; font-size:16px; background:transparent;")
        lay.addWidget(t, 0, Qt.AlignHCenter)

        # Colunas incluem os filtros: Segmento, Cliente, CNPJ, AG
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Usuário","Data","Cliente","Segmento","CNPJ","AG","Ações"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumHeight(280)

        hh = self.table.horizontalHeader(); hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 150);  # Usuário
        self.table.setColumnWidth(1, 140);  # Data
        self.table.setColumnWidth(2, 300);  # Cliente
        self.table.setColumnWidth(3, 140);  # Segmento
        self.table.setColumnWidth(4, 170);  # CNPJ
        self.table.setColumnWidth(5, 80);   # AG
        self.table.setColumnWidth(6, 120);  # Ações

        lay.addWidget(self.table)
        row_tbl = QHBoxLayout(); row_tbl.setAlignment(Qt.AlignHCenter); row_tbl.addWidget(card)
        root.addLayout(row_tbl, stretch=1)

    def load_recent(self, rows: List[Dict[str,Any]]):
        self.table.setRowCount(len(rows or []))
        for r, it in enumerate(rows or []):
            self.table.setItem(r,0,QTableWidgetItem(str(it.get("usuario",""))))
            self.table.setItem(r,1,QTableWidgetItem(str(it.get("data",""))))
            self.table.setItem(r,2,QTableWidgetItem(str(it.get("cliente",""))))
            self.table.setItem(r,3,QTableWidgetItem(str(it.get("segmento",""))))
            self.table.setItem(r,4,QTableWidgetItem(str(it.get("cnpj",""))))
            self.table.setItem(r,5,QTableWidgetItem(str(it.get("ag",""))))

            btn = self._gold_btn("Visualizar",120,36)
            cell = QFrame(); h = QHBoxLayout(cell); h.setContentsMargins(0,0,0,0); h.setAlignment(Qt.AlignCenter); h.addWidget(btn)
            filtros = {"Segmento": it.get("segmento",""), "Cliente": it.get("cliente",""), "CNPJ": it.get("cnpj",""), "AG": it.get("ag","")}
            btn.clicked.connect(lambda _=None, f=filtros: self.open_registro.emit(f))
            self.table.setCellWidget(r,6,cell)
