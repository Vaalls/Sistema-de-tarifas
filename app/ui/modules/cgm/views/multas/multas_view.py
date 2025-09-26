from __future__ import annotations
from typing import List, Dict, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *

class MultasView(QWidget):
    open_cadastro = Signal(); open_consulta = Signal(); go_back = Signal(); open_registro = Signal(dict)

    def __init__(self):
        super().__init__()
        self._k1 = QLabel("0"); self._k2 = QLabel("0")
        self._build()

    def _gold(self, txt,w=220,h=52):
        b=QPushButton(txt); b.setProperty("accent","true"); b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton{border-radius:8px;} QPushButton:hover{background:#C49A2E;}"); return b

    def _kpi(self,title,vref,btn_txt,slot):
        card=QFrame(objectName="Surface"); card.setFixedWidth(520)
        lay=QVBoxLayout(card); lay.setContentsMargins(16,18,16,18); lay.setSpacing(10)
        t=QLabel(title); t.setAlignment(Qt.AlignHCenter); t.setStyleSheet("color:#8B98A5; background:transparent;")
        vref.setAlignment(Qt.AlignHCenter); vref.setStyleSheet("font-size:28px; font-weight:700; background:transparent;")
        btn=self._gold(btn_txt); btn.clicked.connect(slot)
        lay.addWidget(t); lay.addWidget(vref); hr=QHBoxLayout(); hr.addStretch(); hr.addWidget(btn); hr.addStretch(); lay.addLayout(hr); return card

    def _configure_recent_table(self, table: QTableWidget):
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Data","Cliente","Segmento","CNPJ","Autorização",""])
        table.verticalHeader().setVisible(False)
        hh=table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.Fixed)
        table.setColumnWidth(5,130)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setMinimumHeight(280)

        # >>> Somente visível
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)

    def _build(self):
        root=QVBoxLayout(self); root.setSpacing(18); root.setAlignment(Qt.AlignTop)
        top=QHBoxLayout(); top.addStretch(); back=self._gold("Voltar ao CGM",160,40); back.clicked.connect(self.go_back.emit)
        top.addWidget(back,0,Qt.AlignRight); root.addLayout(top)
        act=QHBoxLayout(); act.setSpacing(20); act.setAlignment(Qt.AlignHCenter)
        act.addWidget(self._kpi("Registros hoje", self._k1, "Cadastro", self.open_cadastro.emit))
        act.addWidget(self._kpi("Pendentes de revisão", self._k2, "Consulta", self.open_consulta.emit))
        root.addLayout(act)

        card=QFrame(objectName="Surface"); lay=QVBoxLayout(card); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)
        t=QLabel("Últimos cadastros"); t.setStyleSheet("font-weight:700; font-size:16px; background:transparent;")
        lay.addWidget(t,0,Qt.AlignHCenter)

        self.table=QTableWidget(0,6)
        self._configure_recent_table(self.table)
        lay.addWidget(self.table)

        row=QHBoxLayout(); row.setAlignment(Qt.AlignHCenter); row.addWidget(card); root.addLayout(row,stretch=1)

    def load_recent(self, rows: List[Dict[str,Any]]):
        self.table.setRowCount(len(rows or []))
        for r,it in enumerate(rows or []):
            self.table.setItem(r,0,QTableWidgetItem(str(it.get("data",""))))
            self.table.setItem(r,1,QTableWidgetItem(str(it.get("cliente",""))))
            self.table.setItem(r,2,QTableWidgetItem(str(it.get("segmento",""))))
            self.table.setItem(r,3,QTableWidgetItem(str(it.get("cnpj",""))))
            self.table.setItem(r,4,QTableWidgetItem(str(it.get("autorizacao",""))))

            btn=self._gold("Visualizar",120,36)
            wrap=QWidget(); h=QHBoxLayout(wrap); h.setContentsMargins(0,0,0,0); h.addStretch(); h.addWidget(btn)
            self.table.setCellWidget(r,5,wrap)

            filtros={"Segmento":it.get("segmento",""),"Cliente":it.get("cliente",""),"CNPJ":it.get("cnpj",""),
                     "Autorização":it.get("autorizacao","")}
            btn.clicked.connect(lambda _=None,f=filtros: self.open_registro.emit(f))
