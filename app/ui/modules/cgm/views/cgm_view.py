from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout as QVBox
)

from app.ui.modules.cgm.viewmodels.cgm_vm import CgmViewModel
# IMPORT CORRETO do ViewModel (evita import circular)



class CgmView(QWidget):
    open_estorno = Signal()
    open_multas = Signal()
    open_lar = Signal()
    open_pacote = Signal()
    open_alcada = Signal()
    open_cadastro = Signal(str)

    def __init__(self):
        super().__init__()
        self.vm = CgmViewModel()
        self._grid_cols = 5  # começa em 5; ajusta no resize
        self._buttons = []
        self.grid = None
        self._build()

    # --------------------- UI ---------------------

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setAlignment(Qt.AlignTop)

        # KPIs centralizados
        kpis_row = QHBoxLayout()
        kpis_row.setSpacing(16)
        kpis_row.setAlignment(Qt.AlignHCenter)
        k1 = self._kpi_card("Negociações ativas", str(self.vm.negociacoes_ativas()))
        k2 = self._kpi_card(f"Vencendo em {self.vm.dias_alerta()} dias", str(self.vm.vencendo_em()))
        k1.setFixedWidth(260)
        k2.setFixedWidth(260)
        kpis_row.addWidget(k1)
        kpis_row.addWidget(k2)
        root.addLayout(kpis_row)

        # Painel de botões (responsivo)
        panel = QFrame(objectName="Surface")
        panel_lay = QVBox(panel)  # layout do panel
        panel_lay.setContentsMargins(16, 16, 16, 16)
        panel_lay.setSpacing(12)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        panel_lay.addLayout(self.grid)

        def mk(text: str, slot):
            b = QPushButton(text)
            b.setProperty("accent", "true")
            b.setFixedHeight(44)
            b.setMinimumWidth(160)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            return b

        self._buttons = [
            mk("Estorno", self.open_estorno.emit),
            mk("Multas e Comissões", self.open_multas.emit),
            mk("LAR", self.open_lar.emit),
            mk("Pacote de Tarifas", self.open_pacote.emit),
            mk("Negociação com Alçada", self.open_alcada.emit),
        ]
        self._relayout_buttons()

        row_center = QHBoxLayout()
        row_center.setAlignment(Qt.AlignHCenter)
        row_center.addWidget(panel)
        root.addLayout(row_center)

        # Título e tabela — dão mais espaço ao histórico
        lbl = QLabel("Últimos cadastros")
        lbl.setStyleSheet("background: transparent;")
        root.addWidget(lbl, alignment=Qt.AlignHCenter)

        tbl_card = QFrame(objectName="Surface")
        tbl_lay = QVBox(tbl_card)
        tbl_lay.setContentsMargins(16, 16, 16, 16)
        tbl_lay.setSpacing(12)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Usuário", "Tipo", "Cliente", "Data"])
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        tbl_lay.addWidget(self.table)

        row_tbl = QHBoxLayout()
        row_tbl.setAlignment(Qt.AlignHCenter)
        row_tbl.addWidget(tbl_card)
        root.addLayout(row_tbl, stretch=1)  # ⬅ ocupa mais

        self._fill_table()

        hint = QLabel("Dica: pesquise por cliente/contrato e veja negociações ativas antes de cadastrar.")
        hint.setStyleSheet("color:#8B98A5; background: transparent;")
        root.addWidget(hint, alignment=Qt.AlignLeft)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # Reposiciona botões conforme largura disponível
        w = self.width()
        cols = 5 if w >= 1200 else 4 if w >= 1000 else 3 if w >= 780 else 2
        if cols != self._grid_cols:
            self._grid_cols = cols
            self._relayout_buttons()

    def _relayout_buttons(self):
        if not self.grid:
            return

        # limpa grid e recoloca
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        c = self._grid_cols
        for i, btn in enumerate(self._buttons):
            r, col = divmod(i, c)
            self.grid.addWidget(btn, r, col)

    # --------------------- Helpers ---------------------

    def _kpi_card(self, title: str, value: str) -> QWidget:
        card = QFrame(objectName="Surface")
        lay = QVBox(card)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(6)
        t = QLabel(title)
        t.setStyleSheet("color:#8B98A5; background: transparent;")
        v = QLabel(value)
        v.setStyleSheet("font-size:22px; font-weight:600; background: transparent;")
        lay.addWidget(t, alignment=Qt.AlignHCenter)
        lay.addWidget(v, alignment=Qt.AlignHCenter)
        return card

    def _fill_table(self):
        rows = self.vm.ultimos_cadastros()
        self.table.setRowCount(len(rows))
        for r, it in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(getattr(it, "usuario", "")))
            self.table.setItem(r, 1, QTableWidgetItem(getattr(it, "tipo", "")))
            self.table.setItem(r, 2, QTableWidgetItem(getattr(it, "cliente", "")))
            self.table.setItem(r, 3, QTableWidgetItem(str(getattr(it, "data", ""))))
