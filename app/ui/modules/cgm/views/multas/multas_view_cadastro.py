from __future__ import annotations
from typing import Dict

from PySide6.QtCore import Qt, QDate, Slot, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QHBoxLayout, QPushButton, QMessageBox, QDoubleSpinBox, QSpinBox, QAbstractSpinBox
)

from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

def _btn(text: str, accent: bool = True) -> QPushButton:
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

FIELDS_MULTAS = ["Data_Neg","Segmento","Cliente","CNPJ","AG","CC","TAR","Vlr_tar","Vlr_Aut",
                 "Autorização","QTDE","Prazo","Neg_Esp","Prazo_SGN","Vencimento"]


class MultasCadastroView(QWidget):
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

        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        def add(label: str, w: QWidget, r: int, c: int, span: int=1, minw: int=140):
            g.addWidget(QLabel(label), r, c)
            w.setMinimumWidth(minw)
            self.inputs[label] = w
            g.addWidget(w, r, c+1, 1, span)

        # Linha 0
        self.ed_data = _date_ddmmyyyy()
        add("Data_Neg", self.ed_data, 0, 0)
        cb_seg = QComboBox(); cb_seg.addItems(["PJ","PME","Corporate"])
        add("Segmento", cb_seg, 0, 2)

        # Linha 1
        add("Cliente", QLineEdit(), 1, 0, 1, 240)
        add("CNPJ",    QLineEdit(), 1, 2, 1, 160)

        # Linha 2
        add("AG", QLineEdit(), 2, 0, 1, 90)
        add("CC", QLineEdit(), 2, 2, 1, 140)

        # Linha 3
        add("TAR",     QLineEdit(),     3, 0, 1, 100)
        v_tar = QDoubleSpinBox(); v_tar.setMaximum(1e9); v_tar.setDecimals(2)
        add("Vlr_tar", v_tar,           3, 2, 1, 120)

        # Linha 4
        v_aut = QDoubleSpinBox(); v_aut.setMaximum(1e9); v_aut.setDecimals(2)
        add("Vlr_Aut", v_aut, 4, 0, 1, 120)
        add("Autorização", QLineEdit(), 4, 2, 1, 200)

        # Linha 5
        sp_qtde = QSpinBox(); sp_qtde.setRange(0, 9999)
        add("QTDE", sp_qtde, 5, 0, 1, 100)

        self.sp_prazo = QSpinBox(); self.sp_prazo.setRange(0, 3650)  # dias
        add("Prazo", self.sp_prazo, 5, 2, 1, 120)

        # Linha 6
        cb_neg_esp = QComboBox(); cb_neg_esp.addItems(["N","S"])
        add("Neg_Esp", cb_neg_esp, 6, 0, 1, 100)
        add("Prazo_SGN", QLineEdit(), 6, 2, 1, 140)

        # Linha 7 — Vencimento calculado
        self.ed_venc = _date_ddmmyyyy()
        self.ed_venc.setReadOnly(True)
        add("Vencimento", self.ed_venc, 7, 0, 1, 140)

        root.addLayout(g)

        # Ações
        actions = QHBoxLayout(); actions.addStretch()
        bclr=_btn("Limpar",accent=False); bcan=_btn("Cancelar",accent=False); bsave=_btn("Cadastrar")
        bmass=_btn("Carregar em massa")
        actions.addWidget(bclr); actions.addWidget(bcan); actions.addWidget(bsave)
        actions.addSpacing(12); actions.addWidget(bmass)
        root.addLayout(actions)

        # Conexões
        bclr.clicked.connect(self._clear)
        bcan.clicked.connect(self._on_cancel)
        bsave.clicked.connect(self._on_save)
        bmass.clicked.connect(lambda: MassImportDialog("Multas e Comissões", FIELDS_MULTAS, self).exec())

        self.ed_data.dateChanged.connect(self._recalc_vencimento)
        self.sp_prazo.valueChanged.connect(self._recalc_vencimento)
        self._recalc_vencimento()

    # Lógica vencimento
    @Slot()
    def _recalc_vencimento(self):
        base = self.ed_data.date()
        dias = int(self.sp_prazo.value())
        self.ed_venc.setDate(base.addDays(dias))

    # Helpers
    def _collect(self) -> Dict[str,str]:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox
        d: Dict[str,str] = {}
        for label, w in self.inputs.items():
            if isinstance(w, QLineEdit): d[label] = w.text().strip()
            elif isinstance(w, QComboBox): d[label] = w.currentText().strip()
            elif isinstance(w, QDateEdit): d[label] = w.date().toString("dd/MM/yyyy")
            elif isinstance(w, QDoubleSpinBox): d[label] = f"{w.value():.2f}".replace(".", ",")
            elif isinstance(w, QSpinBox): d[label] = str(w.value())
        return d

    def _is_empty(self) -> bool:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip(): return False
            if isinstance(w, (QDoubleSpinBox, QSpinBox)) and w.value() > 0: return False
            if isinstance(w, QComboBox) and w.currentIndex() > 0: return False
        return True

    def _clear(self):
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit): w.clear()
            elif isinstance(w, (QDoubleSpinBox, QSpinBox)): w.setValue(0)
            elif isinstance(w, QComboBox): w.setCurrentIndex(0)
            elif isinstance(w, QDateEdit): w.setDate(QDate.currentDate())

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
        obrig = ["Cliente","CNPJ","AG","CC","TAR"]
        faltam = [f for f in obrig if not d.get(f)]
        if faltam:
            QMessageBox.warning(self,"Campos obrigatórios","Preencha: "+", ".join(faltam)); return

        m=QMessageBox(self); m.setWindowTitle("Sucesso"); m.setText("Cadastro realizado com sucesso.")
        vis = m.addButton("Visualizar", QMessageBox.AcceptRole)
        close = m.addButton("Fechar", QMessageBox.RejectRole)
        m.exec()

        self._clear()
        self.saved.emit(d)
        if m.clickedButton() is vis: self.saved_view.emit(d)
        else:                         self.saved_close.emit(d)

    def hideEvent(self, ev):
        try: self._clear()
        finally: super().hideEvent(ev)
