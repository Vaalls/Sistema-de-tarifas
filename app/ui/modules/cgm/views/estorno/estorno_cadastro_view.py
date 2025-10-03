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
    if accent: b.setProperty("accent", "true")
    b.setMinimumHeight(36)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b

def _date_ddmmyyyy(default_today: bool = True) -> QDateEdit:
    d = QDateEdit()
    d.setCalendarPopup(True)
    d.setDisplayFormat("dd/MM/yyyy")
    d.setButtonSymbols(QAbstractSpinBox.NoButtons)
    if default_today:
        d.setDate(QDate.currentDate())
    if d.lineEdit():
        d.lineEdit().setInputMask("99/99/9999")
    return d


class EstornoCadastroView(QWidget):
    saved = Signal(dict)
    saved_view = Signal(dict)
    saved_close = Signal(dict)
    cancelled = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.inputs: Dict[str, QWidget] = {}
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12); root.setContentsMargins(12, 12, 12, 12)

        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        def add(label: str, w: QWidget, row: int, col: int, span: int = 1, minw: int = 120):
            lab = QLabel(label); lab.setStyleSheet("background:transparent;")
            w.setMinimumWidth(minw)
            self.inputs[label] = w
            g.addWidget(lab, row, col); g.addWidget(w, row, col+1, 1, span)

        # Linha 0
        add("AGÊNCIA",  QLineEdit(), 0, 0, 1, 90)
        add("CONTA",    QLineEdit(), 0, 2, 1, 90)
        add("NM_AGÊNCIA",  QLineEdit(), 0, 4, 1, 90)
        

        #LINHA 1
        add("CNPJ",     QLineEdit(), 1, 0, 1)
        add("DATA_ENT", _date_ddmmyyyy(), 1 , 2, 1)
        add("TARIFA",      QLineEdit(), 1, 4, 1)

        #LINHA 2
        add("CLIENTE", QLineEdit(), 2, 0, 1, 160)
        add("GRUPO", QLineEdit(), 2, 2, 1, 160)
        cb_seg = QComboBox(); cb_seg.addItems(["", "EMPRESA","MIDDLE","CORPORATE", "LARGE", "CAPTAÇÃO", "OUTROS"])
        add("SEGMENTO", cb_seg, 2, 4, 1)

        # Linha 3
        cb_area = QComboBox(); cb_area.addItems(["", "COMISSÕES E MULTA", "MESA DE TARIFAS"])
        add("ÁREA",     cb_area, 3, 0, 1)
        sp_val = QDoubleSpinBox(); sp_val.setMaximum(10_000_000); sp_val.setDecimals(2)
        add("VLR_ESTORNO",  sp_val, 3, 2, 1, 90)
        cb_class = QComboBox(); cb_class.addItems(["", "ERRO OPERACIONAL", "ERRO DE SISTEMA", "COMERCIAL",
                                                    "ENCERRAMENTO DE CONTA", "PACOTE ATIVO", "TARIFA DEVIDA", "CLIENTE APLICADOR", "FRANQUIA"])
        add("CLASS", cb_class, 3, 4, 1)

        # Linha 4
        sp_val_cred = QDoubleSpinBox(); sp_val_cred.setMaximum(10_000_000); sp_val_cred.setDecimals(2)
        add("VLR_CREDITO", sp_val_cred, 4, 0, 1, 90)
        add("DT_ESTORNO",   _date_ddmmyyyy(), 4, 2, 1)
        cb_status = QComboBox(); cb_status.addItems(["","ARQUIVADO", "CREDITADO", "DEVOLVIDO", "ENCAMINHADO", "PENDENTE DE DOM",
                                                     "RECEPCIONADO", "RECUSADO"])
        add("STATUS", cb_status, 4, 4, 1) 
        
        #LINHA 5 
        cb_resp = QComboBox(); cb_resp.addItems(["", "Cristiane", "Nayara","Karian", "Felipe", "Diego"])
        add("RESPONSAVEL",     cb_resp, 5, 0, 1)       
        add("PARECER", QLineEdit(), 5, 2, 3)

        root.addLayout(g)

        # Ações
        actions = QHBoxLayout(); actions.addStretch()
        btn_clear   = _btn("Limpar", accent=False)
        btn_cancel  = _btn("Cancelar", accent=False)
        btn_save    = _btn("Cadastrar", accent=True)
        btn_mass    = _btn("Carregar em massa", accent=True)
        actions.addWidget(btn_clear); actions.addWidget(btn_cancel); actions.addWidget(btn_save)
        actions.addSpacing(12); actions.addWidget(btn_mass)
        root.addLayout(actions)

        btn_clear.clicked.connect(self._clear)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_save.clicked.connect(self._on_save)
        btn_mass.clicked.connect(self._open_mass_import)

    # Helpers
    def _collect(self) -> Dict[str, str]:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        d: Dict[str, str] = {}
        for label, w in self.inputs.items():
            if isinstance(w, QLineEdit): d[label] = w.text().strip()
            elif isinstance(w, QComboBox): d[label] = w.currentText().strip()
            elif isinstance(w, QDateEdit): d[label] = w.date().toString("dd/MM/yyyy")
            elif isinstance(w, QDoubleSpinBox): d[label] = f"{w.value():.2f}".replace(".", ",")
        return d

    def is_empty(self) -> bool:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDoubleSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip(): return False
            if isinstance(w, QComboBox) and w.currentText().strip(): return False
            if isinstance(w, QDoubleSpinBox) and w.value() > 0: return False
        return True

    def _validate(self, d: Dict[str, str]) -> List[str]:
        obrig = ["AGÊNCIA","CONTA","CLIENTE","CNPJ","TARIFA"]
        return [f for f in obrig if not d.get(f)]

    def _clear(self):
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit): w.clear()
            elif isinstance(w, QComboBox): w.setCurrentIndex(0)
            elif isinstance(w, QDoubleSpinBox): w.setValue(0.0)
            elif isinstance(w, QDateEdit): w.setDate(QDate.currentDate())

    # Fluxo
    @Slot()
    def _on_cancel(self):
        if self.is_empty():
            self._clear(); self.cancelled.emit(); return
        m = QMessageBox(self); m.setWindowTitle("Cancelar")
        m.setText("Deseja cancelar? Os dados preenchidos serão descartados.")
        m.setStandardButtons(QMessageBox.Yes | QMessageBox.No); m.setDefaultButton(QMessageBox.No)
        if m.exec() == QMessageBox.Yes:
            self._clear(); self.cancelled.emit()

    @Slot()
    def _on_save(self):
        d = self._collect()
        faltam = self._validate(d)
        if faltam:
            QMessageBox.warning(self, "Campos obrigatórios", "Preencha: " + ", ".join(faltam)); return

        msg = QMessageBox(self); msg.setWindowTitle("Cadastro realizado")
        msg.setText("Estorno cadastrado com sucesso.")
        bt_vis   = msg.addButton("Visualizar", QMessageBox.AcceptRole)
        bt_close = msg.addButton("Fechar",     QMessageBox.RejectRole)
        msg.exec()

        self._clear()
        self.saved.emit(d)
        if msg.clickedButton() is bt_vis: self.saved_view.emit(d)
        else:                              self.saved_close.emit(d)

    def _open_mass_import(self):
        cols = ["Data_Ent","Area","Agencia","Conta","Vlr_Est","Tar","DT_Est","Status",
                "Resp","Segmento","Nome_Ag","Class","Parecer_OP","Nome_Cli","CNPJ"]
        MassImportDialog("Estorno", cols, self).exec()

    def hideEvent(self, ev):
        try: self._clear()
        finally: super().hideEvent(ev)
