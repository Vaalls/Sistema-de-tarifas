from __future__ import annotations
from typing import List, Dict, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *

class LarView(QWidget):
    open_cadastro = Signal(); open_consulta = Signal(); go_back = Signal(); open_registro = Signal(dict)

    def __init__(self):
        super().__init__(); self._k1=QLabel("0"); self._k2=QLabel("0"); self._build()

    def _gold(self, txt,w=220,h=52):
        b=QPushButton(txt); b.setProperty("accent","true"); b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton{border-radius:8px;} QPushButton:hover{background:#C49A2E;}"); return b
    def _kpi(self,title,vref,btn_txt,slot):
        c=QFrame(objectName="Surface"); c.setFixedWidth(520); l=QVBoxLayout(c); l.setContentsMargins(16,18,16,18); l.setSpacing(10)
        t=QLabel(title); t.setAlignment(Qt.AlignHCenter); t.setStyleSheet("color:#8B98A5; background:transparent;")
        vref.setAlignment(Qt.AlignHCenter); vref.setStyleSheet("font-size:28px; font-weight:700; background:transparent;")
        b=self._gold(btn_txt); b.clicked.connect(slot)
        l.addWidget(t); l.addWidget(vref); r=QHBoxLayout(); r.addStretch(); r.addWidget(b); r.addStretch(); l.addLayout(r); return c
    def _build(self):
        root=QVBoxLayout(self); root.setSpacing(18); root.setAlignment(Qt.AlignTop)
        top=QHBoxLayout(); top.addStretch(); back=self._gold("Voltar ao CGM",160,40); back.clicked.connect(self.go_back.emit)
        top.addWidget(back,0,Qt.AlignRight); root.addLayout(top)
        a=QHBoxLayout(); a.setSpacing(20); a.setAlignment(Qt.AlignHCenter)
        a.addWidget(self._kpi("Registros hoje", self._k1, "Cadastro", self.open_cadastro.emit))
        a.addWidget(self._kpi("Pendentes de revisão", self._k2, "Consulta", self.open_consulta.emit))
        root.addLayout(a)

        card=QFrame(objectName="Surface"); l=QVBoxLayout(card); l.setContentsMargins(16,16,16,16); l.setSpacing(10)
        t=QLabel("Últimos cadastros"); t.setStyleSheet("font-weight:700; font-size:16px; background:transparent;")
        l.addWidget(t,0,Qt.AlignHCenter)

        # Filtros: Segmento, Cliente, CNPJ
        self.table=QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(["Usuário","Data","Cliente","Segmento","CNPJ","Ações"])
        self.table.verticalHeader().setVisible(False)
        hh=self.table.horizontalHeader(); hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0,150); self.table.setColumnWidth(1,140); self.table.setColumnWidth(2,320)
        self.table.setColumnWidth(3,140); self.table.setColumnWidth(4,170); self.table.setColumnWidth(5,120)
        l.addWidget(self.table)

        row=QHBoxLayout(); row.setAlignment(Qt.AlignHCenter); row.addWidget(card); root.addLayout(row,stretch=1)

    def load_recent(self, rows: List[Dict[str,Any]]):
        self.table.setRowCount(len(rows or []))
        for r,it in enumerate(rows or []):
            self.table.setItem(r,0,QTableWidgetItem(str(it.get("usuario",""))))
            self.table.setItem(r,1,QTableWidgetItem(str(it.get("data",""))))
            self.table.setItem(r,2,QTableWidgetItem(str(it.get("cliente",""))))
            self.table.setItem(r,3,QTableWidgetItem(str(it.get("segmento",""))))
            self.table.setItem(r,4,QTableWidgetItem(str(it.get("cnpj",""))))
            btn=self._gold("Visualizar",120,36); cell=QFrame(); h=QHBoxLayout(cell); h.setContentsMargins(0,0,0,0); h.setAlignment(Qt.AlignCenter); h.addWidget(btn)
            filtros={"Segmento":it.get("segmento",""),"Cliente":it.get("cliente",""),"CNPJ":it.get("cnpj","")}
            btn.clicked.connect(lambda _=None,f=filtros: self.open_registro.emit(f))
            self.table.setCellWidget(r,5,cell)
