from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, 
    QPushButton, QLabel, QFrame, QSizePolicy, QTableWidget, 
    QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, Signal
from app.ui.modules.cgm.views.viewmodels.cgm_vm import CgmViewModel

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
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(16)
        root.setAlignment(Qt.AlignTop)
        title = QLabel("Cadastro no CGM"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:600; background: transparent;")
        root.addWidget(title)

        # Cards
        cards = QVBoxLayout(); 
        cards.setSpacing(12)
        cards.addWidget(self._kpi_card("Negociações ativas", str(self.vm.negociacoes_ativas())))
        cards.addWidget(self._kpi_card(f"Vencendo em {self.vm.dias_alerta()} dias", str(self.vm.vencendo_em())))
        cards.addStretch()
        root.addLayout(cards)


        panel = QFrame(objectName="Surface")
        panel.setMaximumHeight(980)
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(16, 16, 16, 16); panel_lay.setSpacing(12)
        grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(12)        
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        def mk(text):
            b = QPushButton(text)
            b.setProperty("accent", "true")
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setCursor(Qt.PointingHandCursor)
            return b
        
        b1 = mk("Estorno");              b1.clicked.connect(self.open_estorno.emit)
        b2 = mk("Multas e Comissões");   b2.clicked.connect(self.open_multas.emit)
        b3 = mk("LAR");                  b3.clicked.connect(self.open_lar.emit)
        b4 = mk("Pacote de Tarifas");    b4.clicked.connect(self.open_pacote.emit)
        b5 = mk("Negociação com Alçada");b5.clicked.connect(self.open_alcada.emit)

        grid.addWidget(b1, 0, 0)
        grid.addWidget(b2, 0, 1)
        grid.addWidget(b3, 1, 0)
        grid.addWidget(b4, 1, 1)
        grid.addWidget(b5, 2, 0, 1, 2)

        panel_lay.addLayout(grid)
        root.addWidget(panel, alignment=Qt.AlignHCenter)

        hint = QLabel("Dica: Pesquise por cliente/contrato e veja negociações ativas antes de cadastrar.")
        hint.setStyleSheet("color:#8B98A5; background: transparent;")
        root.addWidget(hint)


    # ===== Tabela: Últimos cadastros =====
        lbl = QLabel("Últimos cadastros"); lbl.setStyleSheet("background: transparent;")
        root.addWidget(lbl)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Usuário", "Tipo", "Cliente", "Ação"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        root.addWidget(self.table)
        self._fill_table()

        hint = QLabel("Dica: pesquise por cliente/contrato e veja negociações ativas antes de cadastrar.")
        hint.setStyleSheet("color:#8B98A5; background: transparent;")
        root.addWidget(hint)

    def _kpi_card(self, title: str, value: str) -> QWidget:
        card = QFrame(objectName="Surface")
        lay = QVBoxLayout(card); lay.setContentsMargins(12,12,12,12); lay.setSpacing(6)
        t = QLabel(title); t.setStyleSheet("color:#8B98A5; background: transparent;")
        v = QLabel(value); v.setStyleSheet("font-size:22px; font-weight:600; background: transparent;")
        lay.addWidget(t); lay.addWidget(v)
        return card

    def _fill_table(self):
            rows = self.vm.ultimos_cadastros()
            self.table.setRowCount(len(rows))
            for r, it in enumerate(rows):
                self.table.setItem(r, 0, QTableWidgetItem(it.usuario))
                self.table.setItem(r, 1, QTableWidgetItem(it.tipo))
                self.table.setItem(r, 2, QTableWidgetItem(it.cliente))
                btn = QPushButton("Abrir"); btn.setProperty("accent", "true"); btn.setCursor(Qt.PointingHandCursor)
                # passa o id do cadastro para a navegação
                btn.clicked.connect(lambda _=False, id_=it.id: self.open_cadastro.emit(id_))
                self.table.setCellWidget(r, 3, btn)
