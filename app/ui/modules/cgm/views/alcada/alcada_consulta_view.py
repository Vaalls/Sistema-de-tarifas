from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"
def _btn(text, accent=True, w=120, h=36):
    b = QPushButton(text)
    if accent: b.setProperty("accent","true")
    b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD_HOVER)
    return b

class AlcadaConsultaView(QWidget):
    go_back = Signal()
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        filt = QHBoxLayout(); filt.setSpacing(8)
        self.ed_seg = QLineEdit(placeholderText="Segmento"); self.ed_seg.setFixedWidth(160)
        self.ed_cli = QLineEdit(placeholderText="Cliente");  self.ed_cli.setFixedWidth(220)
        self.ed_cnpj= QLineEdit(placeholderText="CNPJ");     self.ed_cnpj.setFixedWidth(160)
        self.ed_ag  = QLineEdit(placeholderText="AG");       self.ed_ag.setFixedWidth(100)
        self.ed_tar = QLineEdit(placeholderText="Tarifa");   self.ed_tar.setFixedWidth(120)
        bt = _btn("Buscar", True)

        for w in (self.ed_seg,self.ed_cli,self.ed_cnpj,self.ed_ag,self.ed_tar): filt.addWidget(w)
        filt.addWidget(bt); filt.addStretch()

        back = _btn("Voltar", False)
        top = QHBoxLayout(); top.addLayout(filt,1); top.addWidget(back,0,Qt.AlignRight)
        root.addLayout(top)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Cliente","CNPJ","Segmento","AG","Tarifa","Situação"])
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for c in [1,2,3,4,5]: hh.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.setVisible(False)
        root.addWidget(self.table, stretch=1)

        bt.clicked.connect(self._do_query)
        back.clicked.connect(self.go_back.emit)

    def hideEvent(self, e):
        super().hideEvent(e)
        for w in (self.ed_seg,self.ed_cli,self.ed_cnpj,self.ed_ag,self.ed_tar): w.clear()
        self.table.clearContents(); self.table.setRowCount(0); self.table.setVisible(False)

    def _do_query(self):
        if not any([self.ed_seg.text().strip(), self.ed_cli.text().strip(), self.ed_cnpj.text().strip(), self.ed_ag.text().strip(), self.ed_tar.text().strip()]):
            QMessageBox.information(self, "Consulta", "Informe pelo menos um filtro para buscar.")
            return
        rows = [
            ("ACME LTDA","12.345.678/0001-90","Corporate","0012","660","Em análise"),
        ]
        self.table.setRowCount(len(rows))
        for r, data in enumerate(rows):
            for c, v in enumerate(data):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.setVisible(True)
