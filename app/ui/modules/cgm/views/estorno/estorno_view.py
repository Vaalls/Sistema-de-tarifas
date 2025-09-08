from __future__ import annotations
from typing import List, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)

class EstornoView(QWidget):
    open_cadastro = Signal()
    open_consulta = Signal()
    go_back = Signal()
    open_registro = Signal(dict)   # emite filtros para a consulta (Agência/Conta/Cliente)

    def __init__(self):
        super().__init__()
        self._kpi1 = QLabel("0")
        self._kpi2 = QLabel("0")
        self.table: QTableWidget
        self._build()

    # ---------- helpers ----------
    def _gold_btn(self, text: str, w: int = 220, h: int = 52) -> QPushButton:
        b = QPushButton(text)
        b.setProperty("accent", "true")
        b.setFixedSize(w, h)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton { border-radius:8px; } QPushButton:hover{background:#C49A2E;}")
        return b

    def _kpi_card(self, title: str, vref: QLabel, action_text: str, slot) -> QFrame:
        card = QFrame(objectName="Surface")
        card.setFixedWidth(520)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 18, 16, 18)
        lay.setSpacing(10)

        t = QLabel(title)
        t.setAlignment(Qt.AlignHCenter)
        t.setStyleSheet("color:#8B98A5; background:transparent;")

        vref.setAlignment(Qt.AlignHCenter)
        vref.setStyleSheet("font-size:28px; font-weight:700; background:transparent;")

        btn = self._gold_btn(action_text)
        btn.clicked.connect(slot)

        lay.addWidget(t)
        lay.addWidget(vref)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn)
        row.addStretch()
        lay.addLayout(row)
        return card

    # ---------- UI ----------
    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(18)
        root.setAlignment(Qt.AlignTop)

        # Topo: voltar ao CGM (sem título interno — título fica no Topbar)
        top = QHBoxLayout()
        top.addStretch()
        back = self._gold_btn("Voltar ao CGM", 160, 40)
        back.clicked.connect(self.go_back.emit)
        top.addWidget(back, 0, Qt.AlignRight)
        root.addLayout(top)

        # KPIs + ações (exatamente como no PacoteView)
        actions = QHBoxLayout()
        actions.setSpacing(20)
        actions.setAlignment(Qt.AlignHCenter)
        actions.addWidget(self._kpi_card("Registros hoje", self._kpi1, "Cadastro", self.open_cadastro.emit))
        actions.addWidget(self._kpi_card("Pendentes de revisão", self._kpi2, "Consulta", self.open_consulta.emit))
        root.addLayout(actions)

        # Card com tabela de últimos cadastros
        card = QFrame(objectName="Surface")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        t = QLabel("Últimos cadastros")
        t.setStyleSheet("font-weight:700; font-size:16px; background:transparent;")
        lay.addWidget(t, 0, Qt.AlignHCenter)

        # Colunas pensadas para pré-preencher a consulta de Estorno:
        # (Segmento não é obrigatório aqui; priorizamos Cliente/CNPJ/AG/Conta)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Usuário", "Data", "Cliente", "CNPJ", "AG", "Conta", "Ações"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumHeight(280)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        # Larguras por coluna — sem “apertar” o botão de ação
        self.table.setColumnWidth(0, 150)  # Usuário
        self.table.setColumnWidth(1, 140)  # Data
        self.table.setColumnWidth(2, 300)  # Cliente
        self.table.setColumnWidth(3, 170)  # CNPJ
        self.table.setColumnWidth(4, 80)   # AG
        self.table.setColumnWidth(5, 140)  # Conta
        self.table.setColumnWidth(6, 120)  # Ações (botão)

        lay.addWidget(self.table)
        row_tbl = QHBoxLayout()
        row_tbl.setAlignment(Qt.AlignHCenter)
        row_tbl.addWidget(card)
        root.addLayout(row_tbl, stretch=1)

    # ---------- API para preencher "Últimos cadastros" ----------
    def load_recent(self, rows: List[Dict[str, Any]]):
        """rows: [{'usuario','data','cliente','cnpj','ag','conta'}]"""
        self.table.setRowCount(len(rows or []))
        for r, it in enumerate(rows or []):
            self.table.setItem(r, 0, QTableWidgetItem(str(it.get("usuario", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(it.get("data", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(it.get("cliente", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(str(it.get("cnpj", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(str(it.get("ag", ""))))
            self.table.setItem(r, 5, QTableWidgetItem(str(it.get("conta", ""))))

            btn = self._gold_btn("Visualizar", 120, 36)
            cell = QFrame()
            h = QHBoxLayout(cell)
            h.setContentsMargins(0, 0, 0, 0)
            h.setAlignment(Qt.AlignCenter)
            h.addWidget(btn)

            # Filtros usados para pré-preencher a consulta de Estorno
            filtros = {
                "Agência": it.get("ag", ""),
                "Conta": it.get("conta", ""),
                "Cliente": it.get("cliente", ""),
            }
            btn.clicked.connect(lambda _=None, f=filtros: self.open_registro.emit(f))
            self.table.setCellWidget(r, 6, cell)

    # (opcional) ajudantes para atualizar os KPIs a partir do MainWindow
    def set_kpis(self, registros_hoje: int | str, pendentes: int | str):
        self._kpi1.setText(str(registros_hoje))
        self._kpi2.setText(str(pendentes))
