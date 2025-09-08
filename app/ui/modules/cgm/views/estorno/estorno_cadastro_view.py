from __future__ import annotations
from typing import Dict, List
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QDateEdit, QComboBox,
    QDoubleSpinBox, QPushButton, QMessageBox
)

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

def _btn(text: str, accent: bool = True) -> QPushButton:
    b = QPushButton(text)
    if accent:
        b.setProperty("accent", "true")
    b.setMinimumHeight(38)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b


class EstornoCadastroView(QWidget):
    """
    Cadastro Estorno — sem título interno (Topbar mostra o título).
    Regras:
      - 'Cadastrar': valida mínimos, abre popup (Visualizar | Fechar)
        * Visualizar -> emite saved_view(dados)
        * Fechar     -> emite saved_close(dados)
        * Em ambos os casos limpa o formulário
      - 'Limpar': limpa campos
      - 'Cancelar': se vazio volta direto; se tiver algo preenchido pergunta (sim -> volta)
    """
    saved = Signal(dict)         # compat (não usado pelo fluxo novo, mas mantido)
    saved_view = Signal(dict)    # navegar para a consulta com prefill
    saved_close = Signal(dict)   # voltar ao menu principal
    cancelled = Signal()         # voltar ao menu se vazio ou após confirmação

    def __init__(self) -> None:
        super().__init__()
        self.inputs: Dict[str, QWidget] = {}
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        # Grade organizada por proximidade sem ser tudo “um embaixo do outro”
        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        def add(label: str, w: QWidget, row: int, col: int, span: int = 1, minw: int = 120):
            lab = QLabel(label); lab.setStyleSheet("background:transparent;")
            w.setMinimumWidth(minw)
            self.inputs[label] = w
            g.addWidget(lab, row, col)
            g.addWidget(w,   row, col+1, 1, span)

        # Linha 0
        add("Data_Ent", QDateEdit(calendarPopup=True), 0, 0)
        add("DT_Est",   QDateEdit(calendarPopup=True), 0, 2)
        cb_status = QComboBox(); cb_status.addItems(["Pendente","Aprovado","Negado"])
        add("Status", cb_status, 0, 4)

        # Linha 1
        add("Área",     QLineEdit(), 1, 0, 3, 220)
        add("Segmento", QLineEdit(), 1, 4, 1, 140)
        add("Resp",     QLineEdit(), 1, 6, 1, 180)

        # Linha 2
        add("Agência",  QLineEdit(), 2, 0, 1, 90)
        add("Conta",    QLineEdit(), 2, 2, 1, 160)
        add("Nome_Ag",  QLineEdit(), 2, 4, 3, 220)

        # Linha 3
        add("Nome_Cli", QLineEdit(), 3, 0, 3, 260)
        add("CNPJ",     QLineEdit(), 3, 4, 1, 160)

        # Linha 4
        add("Tar",      QLineEdit(),        4, 0, 1, 100)
        sp_val = QDoubleSpinBox(); sp_val.setMaximum(10_000_000); sp_val.setDecimals(2)
        add("Vlr_Est",  sp_val,             4, 2, 1, 120)
        add("Class",    QLineEdit(),        4, 4, 1, 100)

        # Linha 5 (texto mais longo)
        add("Parecer_OP", QLineEdit(), 5, 0, 7, 420)

        root.addLayout(g)

        # Ações
        row = QGridLayout()
        bt_limpar   = _btn("Limpar", accent=False)
        bt_cancelar = _btn("Cancelar", accent=False)
        bt_cadastrar= _btn("Cadastrar", accent=True)
        row.addWidget(bt_limpar,   0, 0)
        row.addWidget(bt_cancelar, 0, 1)
        row.addWidget(bt_cadastrar,0, 2)
        row.setColumnStretch(3, 1)
        root.addLayout(row)

        bt_limpar.clicked.connect(self._clear)
        bt_cancelar.clicked.connect(self._on_cancel)
        bt_cadastrar.clicked.connect(self._on_save)

    # ------- helpers -------
    def _collect(self) -> Dict[str, str]:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        d: Dict[str,str] = {}
        for label, w in self.inputs.items():
            if isinstance(w, QLineEdit):
                d[label] = w.text().strip()
            elif isinstance(w, QComboBox):
                d[label] = w.currentText().strip()
            elif isinstance(w, QDateEdit):
                d[label] = w.date().toString("dd/MM/yyyy")
            elif isinstance(w, QDoubleSpinBox):
                d[label] = f"{w.value():.2f}".replace(".", ",")
        return d

    def _is_empty(self) -> bool:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip():
                return False
            if isinstance(w, QComboBox) and w.currentText().strip():
                return False
            if isinstance(w, QDoubleSpinBox) and w.value() > 0:
                return False
            # datas: mantemos padrão sem validar “vazio”
        return True

    def _validate(self, d: Dict[str, str]) -> List[str]:
        obrig = ["Agência","Conta","Nome_Cli","CNPJ","Tar"]
        return [f for f in obrig if not d.get(f)]

    def _clear(self):
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit):
                w.clear()
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)
            elif isinstance(w, QDoubleSpinBox):
                w.setValue(0.0)
            elif isinstance(w, QDateEdit):
                pass

    # ------- slots -------
    @Slot()
    def _on_cancel(self):
        if self._is_empty():
            self.cancelled.emit()
            return
        m = QMessageBox(self)
        m.setWindowTitle("Cancelar")
        m.setText("Deseja cancelar? Os dados preenchidos serão descartados.")
        m.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if m.exec() == QMessageBox.Yes:
            self.cancelled.emit()
        else: 
            m.setDefaultButton(QMessageBox.No)

    @Slot()
    def _on_save(self):
        d = self._collect()
        faltam = self._validate(d)
        if faltam:
            QMessageBox.warning(self, "Campos obrigatórios", "Preencha: " + ", ".join(faltam))
            return

        # popup pós-cadastro
        msg = QMessageBox(self)
        msg.setWindowTitle("Cadastro realizado")
        msg.setText("Estorno cadastrado com sucesso.")
        bt_vis   = msg.addButton("Visualizar", QMessageBox.AcceptRole)
        bt_close = msg.addButton("Fechar",     QMessageBox.RejectRole)
        msg.exec()

        # sempre limpa o form após cadastrar
        self._clear()

        # compat
        self.saved.emit(d)

        if msg.clickedButton() is bt_vis:
            self.saved_view.emit(d)   # MainWindow -> abre consulta com prefill
        else:
            self.saved_close.emit(d)  # MainWindow -> volta ao menu principal
