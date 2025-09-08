from __future__ import annotations
from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QHBoxLayout, QPushButton, QMessageBox, QDoubleSpinBox, QSpinBox
)

_GOLD_HOVER="QPushButton:hover{background:#C49A2E;}"
def _btn(t, accent=True):
    b=QPushButton(t)
    if accent: b.setProperty("accent","true")
    b.setMinimumHeight(36); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(_GOLD_HOVER)
    return b

class AlcadaCadastroView(QWidget):
    saved = Signal(dict)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        root=QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        g=QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        self.ed_data=QDateEdit(); self.ed_data.setCalendarPopup(True)
        self.cb_seg=QComboBox(); self.cb_seg.addItems(["PJ","PME","Corporate"])
        self.ed_cnpj=QLineEdit()
        self.ed_ag=QLineEdit(); self.ed_cc=QLineEdit()
        self.ed_tarifa=QLineEdit()
        self.v_ref=QDoubleSpinBox(); self.v_ref.setMaximum(1e9); self.v_ref.setDecimals(2)
        self.v_aut=QDoubleSpinBox(); self.v_aut.setMaximum(1e9); self.v_aut.setDecimals(2)
        self.ed_aut=QLineEdit()
        self.sp_qtd=QSpinBox(); self.sp_qtd.setMaximum(9999)
        self.ed_prazo=QLineEdit()
        self.ed_venc=QDateEdit(); self.ed_venc.setCalendarPopup(True)
        self.ed_obs=QLineEdit()

        def add(r,c,lab,w,wmin=160):
            g.addWidget(QLabel(lab),r,c); w.setMinimumWidth(wmin); g.addWidget(w,r,c+1)

        r=0
        add(r,0,"Data_Neg",self.ed_data);  add(r,2,"Segmento",self.cb_seg); r+=1
        add(r,0,"CNPJ",self.ed_cnpj,160);  add(r,2,"AG",self.ed_ag,100); r+=1
        add(r,0,"CC",self.ed_cc,140);      add(r,2,"Tarifa",self.ed_tarifa,120); r+=1
        add(r,0,"Vlr_Tar_Ref",self.v_ref,120); add(r,2,"Vlr_Aut",self.v_aut,120); r+=1
        add(r,0,"Autorização",self.ed_aut,180); add(r,2,"Qtde_De_Contrato",self.sp_qtd,120); r+=1
        add(r,0,"Prazo",self.ed_prazo,120); add(r,2,"Vencimento",self.ed_venc,140); r+=1
        add(r,0,"Observação",self.ed_obs,280)

        root.addLayout(g)

        actions=QHBoxLayout(); actions.addStretch()
        bclr=_btn("Limpar",accent=False); bcan=_btn("Cancelar",accent=False); bsave=_btn("Cadastrar")
        actions.addWidget(bclr); actions.addWidget(bcan); actions.addWidget(bsave)
        root.addLayout(actions)

        bclr.clicked.connect(self._clear)
        bcan.clicked.connect(self._cancel)
        bsave.clicked.connect(self._save)

    def _has_any(self):
        for w in [self.ed_cnpj,self.ed_ag,self.ed_cc,self.ed_tarifa,self.ed_aut,self.ed_prazo,self.ed_obs]:
            if w.text().strip(): return True
        return any([self.v_ref.value(), self.v_aut.value(), self.sp_qtd.value()])

    def _clear(self):
        for w in [self.ed_cnpj,self.ed_ag,self.ed_cc,self.ed_tarifa,self.ed_aut,self.ed_prazo,self.ed_obs]:
            w.clear()
        self.v_ref.setValue(0); self.v_aut.setValue(0); self.sp_qtd.setValue(0)
        self.cb_seg.setCurrentIndex(0)

    def _cancel(self):
        if self._has_any():
            if QMessageBox.question(self,"Cancelar","Cancelar cadastro?") == QMessageBox.Yes:
                self.cancelled.emit()
        else:
            self.cancelled.emit()

    def _save(self):
        falta=[]
        if not self.ed_cnpj.text().strip(): falta.append("CNPJ")
        if not self.ed_ag.text().strip():   falta.append("AG")
        if not self.ed_cc.text().strip():   falta.append("CC")
        if not self.ed_tarifa.text().strip(): falta.append("Tarifa")
        if falta:
            QMessageBox.warning(self,"Campos obrigatórios","Preencha: "+", ".join(falta)); return
        data:Dict[str,str]={
            "Data_Neg": self.ed_data.date().toString("dd/MM/yyyy"),
            "Segmento": self.cb_seg.currentText(),
            "CNPJ": self.ed_cnpj.text().strip(),
            "AG": self.ed_ag.text().strip(),
            "CC": self.ed_cc.text().strip(),
            "Tarifa": self.ed_tarifa.text().strip(),
        }
        m=QMessageBox(self); m.setWindowTitle("Sucesso"); m.setText("Cadastro realizado com sucesso.")
        m.addButton("Visualizar", QMessageBox.AcceptRole); m.addButton("Fechar", QMessageBox.RejectRole); m.exec()
        self.saved.emit(data)
