from __future__ import annotations
from typing import Dict

from PySide6.QtCore import Qt, QDate, Slot, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QHBoxLayout, QPushButton, QMessageBox, QSpinBox, QAbstractSpinBox
)

from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

def _btn(text:str, accent=True):
    b = QPushButton(text)
    if accent: b.setProperty("accent","true")
    b.setMinimumHeight(36); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD_HOVER)
    return b

def _date_ddmmyyyy(default_today: bool = True) -> QDateEdit:
    d = QDateEdit()
    d.setCalendarPopup(True)
    d.setDisplayFormat("dd/MM/yyyy")
    d.setButtonSymbols(QAbstractSpinBox.NoButtons)
    if default_today: d.setDate(QDate.currentDate())
    if d.lineEdit(): d.lineEdit().setInputMask("99/99/9999")
    return d

# acrescentei OBS aqui para o import em massa (opcional)
FIELDS_PACOTE = ["Data_Neg","Segmento","Cliente","CNPJ","Pacote","AG","CC","Prazo","Data_Rev","Motivo","Tipo","OBS"]


class PacoteCadastroView(QWidget):
    saved = Signal(dict)
    saved_view = Signal(dict)
    saved_close = Signal(dict)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.inputs: Dict[str, QWidget] = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        form = QGridLayout(); form.setHorizontalSpacing(12); form.setVerticalSpacing(10)

        def add(r,c,lab,w,minw=160,span=1):
            labw = QLabel(lab); labw.setStyleSheet("background:transparent;")
            w.setMinimumWidth(minw)
            self.inputs[lab] = w
            form.addWidget(labw, r, c)
            form.addWidget(w,   r, c+1, 1, span)

        # ---- Disposição ----
        r = 0
        # linha 0: Data / Segmento / Tipo
        self.ed_data_neg = _date_ddmmyyyy()
        add(r, 0, "DATA_NEG", self.ed_data_neg); r += 1
        cb_segmento = QComboBox(); cb_segmento.addItems(["","OUTROS","CAPTAÇÃO","LARGE","EMPRESA","CORPORATE","MIDDLE"])
        add(r, 2, "SEGMENTO", cb_segmento, 160); r += 1

        # linha 1: Cliente (largo) + CNPJ
        add(r, 0, "CLIENTE", QLineEdit(), 360, span=3)  # ocupa colunas 1..3
        add(r, 4, "CNPJ",    QLineEdit(), 160); r += 1

        # linha 2: AG / CC / Pacote
        add(r, 0, "AGENCIA",     QLineEdit(), 100)
        add(r, 2, "CONTA",     QLineEdit(), 100)
        cb_pacote = QComboBox(); cb_pacote.addItems(["","901","902","903","904","905","906","907","908"])
        add(r, 4, "PACOTE", cb_pacote, 140); r += 1

        self.ed_venc = _date_ddmmyyyy(); self.ed_venc.setReadOnly(True)

        # linha 3: Prazo / Data_Rev / Status
        self.sp_prazo = QSpinBox(); self.sp_prazo.setRange(0, 3650)
        add(r, 0, "PRAZO", self.sp_prazo, 100)
        add(r, 2, "DATA_REV", self.ed_venc, 140)
        cb_status = QComboBox(); cb_status.addItems([
            "","Outros","Migração Pct cli Investidor","Conta com Restrição","Conta sem Movimentação",
            "Conta Encerrada/Prevista","DE/PARA","Solicitação do Cliente","Alteração de Pacote"
        ])
        add(r, 4, "STATUS", cb_status, 220); r += 1

        # linha 4: Motivo (largo)
        cb_motivo = QComboBox(); cb_motivo.addItems([
            "","ERRO OPERACIONAL","ERRO DE SISTEMA","COMERCIAL","ARQUIVADO","PENDENTE DE DOM","RECEPCIONADO",
            "RECUSADO","CLIENTE APLICADOR","ENCERRAMENTO DE CONTA","PACOTE ATIVO","TARIFA DEVIDA","CREDITADO",
            "DEVOLVIDO","ENCAMINHADO","FRANQUIA"
        ])
        add(r, 0, "MOTIVO", cb_motivo, 300, span=5); r += 1

        # linha 5: OBS (bem largo)
        add(r, 0, "OBS", QLineEdit(), 420, span=5); r += 1

        root.addLayout(form)

        # Ações
        actions = QHBoxLayout(); actions.addStretch()
        bt_clear = _btn("Limpar", accent=False)
        bt_cancel= _btn("Cancelar", accent=False)
        bt_save  = _btn("Cadastrar")
        bt_mass  = _btn("Carregar em massa")
        actions.addWidget(bt_clear); actions.addWidget(bt_cancel); actions.addWidget(bt_save)
        actions.addSpacing(12); actions.addWidget(bt_mass)
        root.addLayout(actions)

        bt_clear.clicked.connect(self._clear)
        bt_cancel.clicked.connect(self._on_cancel)
        bt_save.clicked.connect(self._on_save)
        bt_mass.clicked.connect(lambda: MassImportDialog("Pacote de Tarifas", FIELDS_PACOTE, self).exec())

        self.ed_data_neg.dateChanged.connect(self._recalc_vencimento)
        self.sp_prazo.valueChanged.connect(self._recalc_vencimento)
        self._recalc_vencimento()  # inicial

    # Helpers
    def _collect(self) -> Dict[str,str]:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QSpinBox
        d: Dict[str,str] = {}
        for k,w in self.inputs.items():
            if isinstance(w, QLineEdit): d[k] = w.text().strip()
            elif isinstance(w, QComboBox): d[k] = w.currentText().strip()
            elif isinstance(w, QDateEdit): d[k] = w.date().toString("dd/MM/yyyy")
            elif isinstance(w, QSpinBox): d[k] = str(w.value())
        return d

    def _is_empty(self) -> bool:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip(): return False
            if isinstance(w, QComboBox) and w.currentIndex() > 0: return False
            if isinstance(w, QSpinBox) and w.value() > 0: return False
        return True

    def _clear(self):
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit): w.clear()
            elif isinstance(w, QComboBox): w.setCurrentIndex(0)
            elif isinstance(w, QDateEdit): w.setDate(QDate.currentDate())
            elif isinstance(w, QSpinBox): w.setValue(0)

    # Fluxo
    @Slot()
    def _on_cancel(self):
        if self._is_empty():
            self._clear(); self.cancelled.emit(); return
        if QMessageBox.question(self,"Cancelar","Cancelar cadastro? Dados serão descartados.") == QMessageBox.Yes:
            self._clear(); self.cancelled.emit()

    @Slot()
    def _on_save(self):
        d = self._collect()
        falta = [f for f in ("CLIENTE","CNPJ","PACOTE","AGENCIA","CONTA") if not d.get(f)]
        if falta:
            QMessageBox.warning(self,"Campos obrigatórios","Preencha: " + ", ".join(falta)); return

        m = QMessageBox(self); m.setWindowTitle("Sucesso")
        m.setText("Cadastro realizado com sucesso.")
        vis = m.addButton("Visualizar", QMessageBox.AcceptRole)
        close = m.addButton("Fechar", QMessageBox.RejectRole)
        m.exec()

        self._clear()
        self.saved.emit(d)
        if m.clickedButton() is vis: self.saved_view.emit(d)
        else:                        
            self.saved_close.emit(d)

    def hideEvent(self, ev):
        try: self._clear()
        finally: super().hideEvent(ev)

    @Slot()
    def _recalc_vencimento(self):
        base = self.ed_data_neg.date()
        dias = int(self.sp_prazo.value())
        self.ed_venc.setDate(base.addDays(dias))
