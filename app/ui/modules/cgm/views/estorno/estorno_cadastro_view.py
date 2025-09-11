from __future__ import annotations
from typing import Dict, List

from PySide6.QtCore import Qt, Slot, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QDateEdit, QComboBox,
    QDoubleSpinBox, QPushButton, QMessageBox, QHBoxLayout, QAbstractSpinBox
)

from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

def _btn(text: str, accent: bool = True) -> QPushButton:
    b = QPushButton(text)
    if accent:
        b.setProperty("accent", "true")   # dourado padrão do app
    b.setMinimumHeight(36)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b

def _date_ddmmyyyy(default_today: bool = True) -> QDateEdit:
    d = QDateEdit()
    d.setCalendarPopup(True)
    d.setDisplayFormat("dd/MM/yyyy")
    d.setButtonSymbols(QAbstractSpinBox.NoButtons)  # some as setinhas; digite a data
    if default_today:
        d.setDate(QDate.currentDate())
    # permite digitar livremente a data
    d.lineEdit().setInputMask("99/99/9999")
    return d


class EstornoCadastroView(QWidget):
    """
    Cadastro Estorno no padrão visual dos outros cadastros.
    Regras:
      - 'Cadastrar': valida mínimos e abre popup (Visualizar | Fechar)
        * Visualizar -> emite saved_view(dados)
        * Fechar     -> emite saved_close(dados)
        * Em ambos os casos limpa o formulário
      - 'Cancelar': se vazio volta direto; se tiver algo preenchido pergunta
    """
    saved = Signal(dict)         # compat (mantido)
    saved_view = Signal(dict)    # navegar para a consulta com filtros pré-preenchidos
    saved_close = Signal(dict)   # voltar ao menu principal
    cancelled = Signal()         # voltar ao menu

    def __init__(self) -> None:
        super().__init__()
        self.inputs: Dict[str, QWidget] = {}
        self._build()

    # ---------- UI ----------
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(12, 12, 12, 12)

        g = QGridLayout()
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(10)

        def add(label: str, w: QWidget, row: int, col: int, span: int = 1, minw: int = 120):
            lab = QLabel(label); lab.setStyleSheet("background:transparent;")
            w.setMinimumWidth(minw)
            self.inputs[label] = w
            g.addWidget(lab, row, col)
            g.addWidget(w,   row, col+1, 1, span)

        # Linha 0
        add("Data_Ent", _date_ddmmyyyy(), 0, 0)
        add("DT_Est",   _date_ddmmyyyy(), 0, 2)
        cb_status = QComboBox(); cb_status.addItems(["Pendente","Aprovado","Negado"])
        add("Status", cb_status, 0, 4, 1, 140)

        # Linha 1
        add("Area",     QLineEdit(), 1, 0, 3, 240)
        add("Segmento", QLineEdit(), 1, 4, 1, 140)
        add("Resp",     QLineEdit(), 1, 6, 1, 180)

        # Linha 2
        add("Agencia",  QLineEdit(), 2, 0, 1, 90)
        add("Conta",    QLineEdit(), 2, 2, 1, 160)
        add("Nome_Ag",  QLineEdit(), 2, 4, 3, 240)

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

        # Barra de ações — no padrão dos demais (botões médios, lado a lado à direita)
        actions = QHBoxLayout()
        actions.addStretch()
        btn_clear   = _btn("Limpar", accent=False)
        btn_cancel  = _btn("Voltar", accent=False)
        btn_save    = _btn("Cadastrar", accent=True)
        btn_mass    = _btn("Carregar em massa", accent=True)
        actions.addWidget(btn_clear)
        actions.addWidget(btn_cancel)
        actions.addWidget(btn_save)
        actions.addSpacing(12)
        actions.addWidget(btn_mass)  # canto direito
        root.addLayout(actions)

        # Conexões
        btn_clear.clicked.connect(self._clear)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_save.clicked.connect(self._on_save)
        btn_mass.clicked.connect(self._open_mass_import)

    # ---------- helpers ----------
    def _collect(self) -> Dict[str, str]:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        d: Dict[str, str] = {}
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

    def reset_form(self):
        """Limpa todos os campos do formulário."""
        self._clear()

    def is_empty(self) -> bool:
        """Retorna True se não houver nada relevante preenchido."""
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip():
                return False
            if isinstance(w, QComboBox) and w.currentText().strip():
                return False
            if isinstance(w, QDoubleSpinBox) and w.value() > 0:
                return False
        return True

    def _validate(self, d: Dict[str, str]) -> List[str]:
        obrig = ["Agencia","Conta","Nome_Cli","CNPJ","Tar"]
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
                w.setDate(QDate.currentDate())

    # ---------- slots ----------
    @Slot()
    def _on_cancel(self):
        if self._is_empty():
            self.reset_form()
            self.cancelled.emit()
            return
        m = QMessageBox(self)
        m.setWindowTitle("Cancelar")
        m.setText("Deseja cancelar? Os dados preenchidos serão descartados.")
        m.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        m.setDefaultButton(QMessageBox.No)
        if m.exec() == QMessageBox.Yes:
            self.reset_form()
            self.cancelled.emit()

    @Slot()
    def _on_save(self):
        d = self._collect()
        faltam = self._validate(d)
        if faltam:
            QMessageBox.warning(self, "Campos obrigatórios", "Preencha: " + ", ".join(faltam))
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Cadastro realizado")
        msg.setText("Estorno cadastrado com sucesso.")
        bt_vis   = msg.addButton("Visualizar", QMessageBox.AcceptRole)
        bt_close = msg.addButton("Fechar",     QMessageBox.RejectRole)
        msg.exec()

        self._clear()
        self.saved.emit(d)  # compat

        if msg.clickedButton() is bt_vis:
            self.saved_view.emit(d)
        else:
            self.saved_close.emit(d)

    def _open_mass_import(self):
        cols = ["Data_Ent","Area","Agencia","Conta","Vlr_Est","Tar","DT_Est","Status",
                "Resp","Segmento","Nome_Ag","Class","Parecer_OP","Nome_Cli","CNPJ"]
        dlg = MassImportDialog("Estorno", cols, self)
        if dlg.exec():  # QDialog.Accepted
            # caminho do arquivo -> dlg.file_path
            # integração com backend fica para a etapa de carga real
            pass

    def hideEvent(self, ev):
        # sempre que sair do cadastro (troca no QStackedWidget), zera
        try:
            self.reset_form()
        finally:
            super().hideEvent(ev)
