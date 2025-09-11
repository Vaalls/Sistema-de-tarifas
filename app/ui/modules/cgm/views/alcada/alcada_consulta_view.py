from __future__ import annotations
from typing import Dict, List, Tuple
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

def _btn(text: str, accent: bool = True, w: int = 120, h: int = 36) -> QPushButton:
    b = QPushButton(text)
    if accent: b.setProperty("accent", "true")
    b.setFixedSize(w, h)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b


class AlcadaConsultaView(QWidget):
    go_back = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._prefilled = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        # filtros: Segmento, Cliente, CNPJ, AG, Tarifa
        filters = QHBoxLayout(); filters.setSpacing(8)
        self.ed_seg = QLineEdit(placeholderText="Segmento"); self.ed_seg.setFixedWidth(140)
        self.ed_cli = QLineEdit(placeholderText="Cliente");  self.ed_cli.setFixedWidth(240)
        self.ed_cnpj= QLineEdit(placeholderText="CNPJ");     self.ed_cnpj.setFixedWidth(160)
        self.ed_ag  = QLineEdit(placeholderText="AG");       self.ed_ag.setFixedWidth(90)
        self.ed_tar = QLineEdit(placeholderText="Tarifa");   self.ed_tar.setFixedWidth(120)
        btn_buscar  = _btn("Buscar")
        for w in (self.ed_seg, self.ed_cli, self.ed_cnpj, self.ed_ag, self.ed_tar, btn_buscar):
            filters.addWidget(w)
        filters.addStretch()

        btn_back = _btn("Voltar", accent=False)
        top = QHBoxLayout(); top.addLayout(filters, 1); top.addWidget(btn_back, 0, Qt.AlignRight)
        root.addLayout(top)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Cliente","CNPJ","Segmento","AG","Tarifa","Qtde Contr.","Situação"])
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in (1,2,3,4,5,6):
            hh.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setVisible(False)
        root.addWidget(self.table, stretch=1)

        btn_buscar.clicked.connect(self._do_query)
        btn_back.clicked.connect(self._on_back)

    # API
    def prefill(self, f: Dict[str,str], autorun: bool=False):
        self._prefilled = True
        self.ed_seg.setText(f.get("Segmento",""))
        self.ed_cli.setText(f.get("Cliente",""))
        self.ed_cnpj.setText(f.get("CNPJ",""))
        self.ed_ag.setText(f.get("AG",""))
        self.ed_tar.setText(f.get("Tarifa",""))
        if autorun: self._do_query()

    def reset_filters(self):
        for w in (self.ed_seg, self.ed_cli, self.ed_cnpj, self.ed_ag, self.ed_tar):
            w.clear()
        self.table.clearContents(); self.table.setRowCount(0); self.table.setVisible(False)

    def hideEvent(self, ev):
        self._prefilled = False
        self.reset_filters()
        super().hideEvent(ev)

    # ações
    @Slot() 
    def _on_back(self): self.go_back.emit()

    @Slot()
    def _do_query(self):
        seg, cli, cnpj, ag, tar = (
            self.ed_seg.text().strip(),
            self.ed_cli.text().strip(),
            self.ed_cnpj.text().strip(),
            self.ed_ag.text().strip(),
            self.ed_tar.text().strip(),
        )
        if not any([seg, cli, cnpj, ag, tar]):
            QMessageBox.information(self, "Consulta", "Informe pelo menos um filtro.")
            return
        rows = self._mock_query(seg, cli, cnpj, ag, tar)
        self.table.setRowCount(len(rows))
        for r, (c, cnpjx, segx, agx, tx, qt, sit) in enumerate(rows):
            for cidx, val in enumerate((c, cnpjx, segx, agx, tx, qt, sit)):
                self.table.setItem(r, cidx, QTableWidgetItem(str(val)))
        self.table.setVisible(True)

    # mock
    def _mock_query(self, seg, cli, cnpj, ag, tar) -> List[Tuple[str,str,str,str,str,int,str]]:
        base = [
            ("ACME LTDA","12.345.678/0001-90","Corporate","0012","660",2,"Ativo"),
            ("XPTO ME",  "11.222.333/0001-55","PJ","0031","665",1,"Revisar"),
        ]
        def ok(a,b): return (not a) or (a.lower() in b.lower())
        out=[]
        for c,cnpjx,segx,agx,tx,qt,sit in base:
            if ok(cli,c) and ok(cnpj,cnpjx) and ok(seg,segx) and ok(ag,agx) and ok(tar,tx):
                out.append((c,cnpjx,segx,agx,tx,qt,sit))
        return out
