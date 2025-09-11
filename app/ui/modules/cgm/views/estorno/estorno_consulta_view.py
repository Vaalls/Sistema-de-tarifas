# app/ui/modules/cgm/views/estorno/estorno_consulta_view.py
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
    if accent:
        b.setProperty("accent","true")
    b.setFixedSize(w, h)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b


class EstornoConsultaView(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        self._prefilled = False
        self._build()

    # ---------------- UI ----------------
    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(12, 12, 12, 12)

        # Filtros (topo-esquerda)
        filters = QHBoxLayout()
        filters.setSpacing(8)

        self.ed_ag  = QLineEdit(placeholderText="Agência"); self.ed_ag.setFixedWidth(120)
        self.ed_cc  = QLineEdit(placeholderText="Conta");   self.ed_cc.setFixedWidth(160)
        self.ed_cli = QLineEdit(placeholderText="Cliente"); self.ed_cli.setFixedWidth(240)
        self.ed_tar = QLineEdit(placeholderText="Tarifa");  self.ed_tar.setFixedWidth(120)

        btn_buscar = _btn("Buscar", True, 120, 36)
        btn_back   = _btn("Voltar", False, 120, 36)

        for w in (self.ed_ag, self.ed_cc, self.ed_cli, self.ed_tar, btn_buscar):
            filters.addWidget(w)
        filters.addStretch()

        top = QHBoxLayout()
        top.addLayout(filters, 1)
        top.addWidget(btn_back, 0, Qt.AlignRight)
        root.addLayout(top)

        # Tabela (oculta até consultar)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Cliente","CNPJ","Agência","Conta","Tarifa","Situação"])
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setVisible(False)
        root.addWidget(self.table, stretch=1)

        # Conexões
        btn_buscar.clicked.connect(self._do_query)
        btn_back.clicked.connect(self._on_back)

    # ------------- API pública -------------
    def prefill(self, filtros: Dict[str, str], autorun: bool = False):
        """Preenche filtros e, se quiser, já executa a busca."""
        self._prefilled = True
        self.ed_ag.setText(filtros.get("Agência",""))
        self.ed_cc.setText(filtros.get("Conta",""))
        self.ed_cli.setText(filtros.get("Cliente",""))
        self.ed_tar.setText(filtros.get("Tarifa",""))
        if autorun:
            self._do_query()

    def reset_filters(self) -> None:
        """Limpa campos e esconde a tabela (usado ao sair da tela)."""
        self.ed_ag.clear()
        self.ed_cc.clear()
        self.ed_cli.clear()
        self.ed_tar.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setVisible(False)

    # ------------- Eventos -------------
    def hideEvent(self, ev):
        """Sempre que sair da view, zera para não manter filtros antigos."""
        self._prefilled = False
        self.reset_filters()
        super().hideEvent(ev)

    # ------------- Ações -------------
    @Slot()
    def _on_back(self):
        self.go_back.emit()

    @Slot()
    def _do_query(self):
        ag  = self.ed_ag.text().strip()
        cc  = self.ed_cc.text().strip()
        cli = self.ed_cli.text().strip()
        tar = self.ed_tar.text().strip()

        if not any([ag, cc, cli, tar]):
            QMessageBox.information(self, "Consulta", "Informe pelo menos um filtro para buscar.")
            return

        rows = self._mock_query(ag, cc, cli, tar)
        self.table.setRowCount(len(rows))
        for r, (c, cnpj, agx, ccx, tx, sit) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(c))
            self.table.setItem(r, 1, QTableWidgetItem(cnpj))
            self.table.setItem(r, 2, QTableWidgetItem(agx))
            self.table.setItem(r, 3, QTableWidgetItem(ccx))
            self.table.setItem(r, 4, QTableWidgetItem(tx))
            self.table.setItem(r, 5, QTableWidgetItem(sit))
        self.table.setVisible(True)

    # ------------- Mock -------------
    def _mock_query(self, ag, cc, cli, tar) -> List[Tuple[str,str,str,str,str,str]]:
        base = [
            ("ACME LTDA","12.345.678/0001-90","0012","123456-7","660","Ativo"),
            ("XPTO ME",  "11.222.333/0001-55","0031","554433-0","662","Revisar"),
            ("Beta SA",  "22.333.444/0001-66","0012","998877-6","665","Ativo"),
        ]
        def ok(a,b): return (not a) or (a.lower() in b.lower())
        out=[]
        for c,cnpj,a,ccx,t,sit in base:
            if ok(cli, c) and ok(ag, a) and ok(cc, ccx) and ok(tar, t):
                out.append((c,cnpj,a,ccx,t,sit))
        return out
