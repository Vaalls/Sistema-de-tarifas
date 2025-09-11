from __future__ import annotations
from typing import Dict

from PySide6.QtCore import Qt, QDate, Slot, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QHBoxLayout, QPushButton, QMessageBox, QDoubleSpinBox, QCheckBox, QAbstractSpinBox
)

from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

GOLD_HOVER="QPushButton:hover{background:#C49A2E;}"

def _btn(t, accent=True):
    b=QPushButton(t)
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

FIELDS_LAR = ["Data_Neg","Segmento","Cliente","AG","CNPJ","Vlr_Tar_Ref","Vlr_Auto","Vlr_Lar",
              "Tipo_Cliente","Autorização","Prazo","Vencimento","Observação","Atuado_SGN"]


class LarCadastroView(QWidget):
    saved = Signal(dict)
    saved_view = Signal(dict)
    saved_close = Signal(dict)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.inputs: Dict[str, QWidget] = {}
        self._build()

    def _build(self):
        root=QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)
        g=QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        def add(r,c,lab,w,minw=160,span=1):
            g.addWidget(QLabel(lab), r, c)
            w.setMinimumWidth(minw); self.inputs[lab]=w
            g.addWidget(w, r, c+1, 1, span)

        add(0,0,"Data_Neg", _date_ddmmyyyy()); cb_seg=QComboBox(); cb_seg.addItems(["PJ","PME","Corporate"])
        add(0,2,"Segmento", cb_seg, 140)
        add(1,0,"Cliente", QLineEdit(), 240); add(1,2,"AG", QLineEdit(), 100)
        add(2,0,"CNPJ", QLineEdit(), 160);  v_ref=QDoubleSpinBox(); v_ref.setMaximum(1e9); v_ref.setDecimals(2)
        add(2,2,"Vlr_Tar_Ref", v_ref, 120)
        v_aut=QDoubleSpinBox(); v_aut.setMaximum(1e9); v_aut.setDecimals(2)
        add(3,0,"Vlr_Auto", v_aut, 120); v_lar=QDoubleSpinBox(); v_lar.setMaximum(1e9); v_lar.setDecimals(2)
        add(3,2,"Vlr_Lar", v_lar, 120)
        cb_tipo=QComboBox(); cb_tipo.addItems(["PJ","PF","MEI"])
        add(4,0,"Tipo_Cliente", cb_tipo, 140); add(4,2,"Autorização", QLineEdit(), 200)
        add(5,0,"Prazo", QLineEdit(), 120); add(5,2,"Vencimento", _date_ddmmyyyy(), 140)
        add(6,0,"Observação", QLineEdit(), 260); chk = QCheckBox("Atuado_SGN"); self.inputs["Atuado_SGN"]=chk; g.addWidget(chk, 6, 2, 1, 2)

        root.addLayout(g)

        actions=QHBoxLayout(); actions.addStretch()
        bclr=_btn("Limpar",accent=False); bcan=_btn("Cancelar",accent=False); bsave=_btn("Cadastrar"); bmass=_btn("Carregar em massa")
        actions.addWidget(bclr); actions.addWidget(bcan); actions.addWidget(bsave)
        actions.addSpacing(12); actions.addWidget(bmass)
        root.addLayout(actions)

        bclr.clicked.connect(self._clear); bcan.clicked.connect(self._on_cancel); bsave.clicked.connect(self._on_save)
        bmass.clicked.connect(lambda: MassImportDialog("LAR", FIELDS_LAR, self).exec())

    # Helpers/fluxo
    def _collect(self)->Dict[str,str]:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QCheckBox
        d:Dict[str,str]={}
        for k,w in self.inputs.items():
            if isinstance(w, QLineEdit): d[k]=w.text().strip()
            elif isinstance(w, QComboBox): d[k]=w.currentText().strip()
            elif isinstance(w, QDateEdit): d[k]=w.date().toString("dd/MM/yyyy")
            elif isinstance(w, QDoubleSpinBox): d[k]=f"{w.value():.2f}".replace(".", ",")
            elif isinstance(w, QCheckBox): d[k]="S" if w.isChecked() else "N"
        return d

    def _is_empty(self)->bool:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip(): return False
            if isinstance(w, QComboBox) and w.currentIndex()>0: return False
            if isinstance(w, QDoubleSpinBox) and w.value()>0: return False
            if isinstance(w, QCheckBox) and w.isChecked(): return False
        return True

    def _clear(self):
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QCheckBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit): w.clear()
            elif isinstance(w, QComboBox): w.setCurrentIndex(0)
            elif isinstance(w, QDateEdit): w.setDate(QDate.currentDate())
            elif isinstance(w, QDoubleSpinBox): w.setValue(0)
            elif isinstance(w, QCheckBox): w.setChecked(False)

    @Slot()
    def _on_cancel(self):
        if self._is_empty():
            self._clear(); self.cancelled.emit(); return
        if QMessageBox.question(self,"Cancelar","Cancelar cadastro? Dados serão descartados.")==QMessageBox.Yes:
            self._clear(); self.cancelled.emit()

    @Slot()
    def _on_save(self):
        d=self._collect()
        falta=[]
        for f in ("Cliente","CNPJ","AG"):
            if not d.get(f): falta.append(f)
        if falta:
            QMessageBox.warning(self,"Campos obrigatórios","Preencha: "+", ".join(falta)); return

        m=QMessageBox(self); m.setWindowTitle("Sucesso"); m.setText("Cadastro realizado com sucesso.")
        vis=m.addButton("Visualizar", QMessageBox.AcceptRole); close=m.addButton("Fechar", QMessageBox.RejectRole); m.exec()
        self._clear(); self.saved.emit(d)
        if m.clickedButton() is vis: self.saved_view.emit(d)
        else:                         self.saved_close.emit(d)

    def hideEvent(self, ev):
        try: self._clear()
        finally: super().hideEvent(ev)
