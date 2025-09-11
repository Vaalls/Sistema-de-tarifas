from __future__ import annotations
from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QHBoxLayout, QPushButton, QMessageBox, QDoubleSpinBox, QSpinBox
)

from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

_GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"
def _btn(t, accent=True):
    b=QPushButton(t)
    if accent: b.setProperty("accent","true")
    b.setMinimumHeight(36); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(_GOLD_HOVER)
    return b

FIELDS_MULTAS = ["Data_Neg","Segmento","Cliente","CNPJ","AG","CC","TAR","Vlr_tar","Vlr_Aut","Autorização","QTDE","Prazo","Neg_Esp","Prazo_SGN","Vencimento"]

class MultasCadastroView(QWidget):
    saved = Signal(dict)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        self.ed_data = QDateEdit(); self.ed_data.setCalendarPopup(True)
        self.cb_seg = QComboBox(); self.cb_seg.addItems(["PJ","PME","Corporate"])
        self.ed_cliente = QLineEdit(); self.ed_cnpj = QLineEdit()
        self.ed_ag = QLineEdit(); self.ed_cc = QLineEdit()
        self.ed_tar = QLineEdit()
        self.v_tar = QDoubleSpinBox(); self.v_tar.setMaximum(1e9); self.v_tar.setDecimals(2)
        self.v_aut = QDoubleSpinBox(); self.v_aut.setMaximum(1e9); self.v_aut.setDecimals(2)
        self.ed_aut = QLineEdit()
        self.sp_qtde = QSpinBox(); self.sp_qtde.setMaximum(9999)
        self.ed_prazo = QLineEdit()
        self.cb_neg_esp = QComboBox(); self.cb_neg_esp.addItems(["N","S"])
        self.ed_prazo_sgn = QLineEdit()
        self.ed_venc = QDateEdit(); self.ed_venc.setCalendarPopup(True)

        def add(r,c,lab,w,wmin=160):
            g.addWidget(QLabel(lab),r,c); w.setMinimumWidth(wmin); g.addWidget(w,r,c+1)

        r=0
        add(r,0,"Data_Neg",self.ed_data);        add(r,2,"Segmento",self.cb_seg); r+=1
        add(r,0,"Cliente", self.ed_cliente,240); add(r,2,"CNPJ",self.ed_cnpj,160); r+=1
        add(r,0,"AG",self.ed_ag,100);            add(r,2,"CC",self.ed_cc,140); r+=1
        add(r,0,"TAR",self.ed_tar,100);          add(r,2,"Vlr_tar",self.v_tar,120); r+=1
        add(r,0,"Vlr_Aut",self.v_aut,120);       add(r,2,"Autorização",self.ed_aut,180); r+=1
        add(r,0,"QTDE",self.sp_qtde,100);        add(r,2,"Prazo",self.ed_prazo,120); r+=1
        add(r,0,"Neg_Esp",self.cb_neg_esp,100);  add(r,2,"Prazo_SGN",self.ed_prazo_sgn,140); r+=1
        add(r,0,"Vencimento",self.ed_venc,160)

        root.addLayout(g)

        actions = QHBoxLayout(); actions.addStretch()
        bclr=_btn("Limpar",accent=False); bcan=_btn("Voltar",accent=False); bsave=_btn("Cadastrar")
        actions.addWidget(bclr); actions.addWidget(bcan); actions.addWidget(bsave)
        root.addLayout(actions)

        bt_mass = _btn("Carregar em massa", accent=True)
        actions.addStretch(); actions.addWidget(bt_mass)
        bt_mass.clicked.connect(lambda: MassImportDialog("Multas e Comissões", FIELDS_MULTAS, self).exec())

        bclr.clicked.connect(self._clear)
        bcan.clicked.connect(self._cancel)
        bsave.clicked.connect(self._save)

    def _has_any(self):
        for w in [self.ed_cliente,self.ed_cnpj,self.ed_ag,self.ed_cc,self.ed_tar,self.ed_aut,self.ed_prazo,self.ed_prazo_sgn]:
            if isinstance(w, QLineEdit) and w.text().strip(): return True
        return any([self.v_tar.value(), self.v_aut.value(), self.sp_qtde.value()])

    def _clear(self):
        for w in [self.ed_cliente,self.ed_cnpj,self.ed_ag,self.ed_cc,self.ed_tar,self.ed_aut,self.ed_prazo,self.ed_prazo_sgn]:
            w.clear()
        self.v_tar.setValue(0); self.v_aut.setValue(0); self.sp_qtde.setValue(0)
        self.cb_seg.setCurrentIndex(0); self.cb_neg_esp.setCurrentIndex(0)

    def _cancel(self):
        if self._has_any():
            if QMessageBox.question(self,"Cancelar","Cancelar cadastro? Dados serão descartados.")==QMessageBox.Yes:
                self.cancelled.emit()
        else:
            self.cancelled.emit()

    def _save(self):
        falta=[]
        if not self.ed_cliente.text().strip(): falta.append("Cliente")
        if not self.ed_cnpj.text().strip():    falta.append("CNPJ")
        if not self.ed_ag.text().strip():      falta.append("AG")
        if not self.ed_cc.text().strip():      falta.append("CC")
        if not self.ed_tar.text().strip():     falta.append("TAR")
        if falta:
            QMessageBox.warning(self,"Campos obrigatórios","Preencha: "+", ".join(falta)); return

        data: Dict[str,str] = {
            "Data_Neg": self.ed_data.date().toString("dd/MM/yyyy"),
            "Segmento": self.cb_seg.currentText(),
            "Cliente": self.ed_cliente.text().strip(),
            "CNPJ": self.ed_cnpj.text().strip(),
            "AG": self.ed_ag.text().strip(),
            "CC": self.ed_cc.text().strip(),
            "TAR": self.ed_tar.text().strip(),
            "Vlr_tar": f"{self.v_tar.value():,.2f}".replace(",", "X").replace(".", ",").replace("X","."),
            "Vlr_Aut": f"{self.v_aut.value():,.2f}".replace(",", "X").replace(".", ",").replace("X","."),
            "Autorização": self.ed_aut.text().strip(),
            "QTDE": str(self.sp_qtde.value()),
            "Prazo": self.ed_prazo.text().strip(),
            "Neg_Esp": self.cb_neg_esp.currentText(),
            "Prazo_SGN": self.ed_prazo_sgn.text().strip(),
            "Vencimento": self.ed_venc.date().toString("dd/MM/yyyy"),
        }
        m=QMessageBox(self); m.setWindowTitle("Sucesso"); m.setText("Cadastro realizado com sucesso.")
        m.addButton("Visualizar", QMessageBox.AcceptRole); m.addButton("Fechar", QMessageBox.RejectRole); m.exec()
        self.saved.emit(data)

    def _open_mass_import(self):
        cols = ["Data_Neg","Segmento","Cliente","CNPJ",
                "AG","CC","TAR","Vlr_tar","Vlr_Aut","Autorização",
                "QTDE","Prazo","Neg_Esp","Prazo_SGN","Vencimento"]
        dlg = MassImportDialog("Multas e Comissões", cols, self)
        if dlg.exec():
            pass

