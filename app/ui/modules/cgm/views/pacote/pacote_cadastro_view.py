from __future__ import annotations
from typing import Dict
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QHBoxLayout, QPushButton, QMessageBox
)

from app.ui.modules.cgm.views.mass_import_dialog import MassImportDialog

_GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

FIELDS_PACOTE = ["Data_Neg","Segmento","Cliente","CNPJ","Pacote","AG","CC","Prazo","Data_Rev","Motivo","Tipo"]

def _btn(text:str, accent=True):
    b = QPushButton(text)
    if accent: b.setProperty("accent","true")
    b.setMinimumHeight(36)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(_GOLD_HOVER)
    return b

from PySide6.QtCore import Qt

class PacoteCadastroView(QWidget):
    saved = Signal(dict)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PacoteCadastroView")
        self._build()

    # ---------- UI ----------
    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        form = QGridLayout(); form.setHorizontalSpacing(12); form.setVerticalSpacing(10)

        # esquerda
        self.ed_data_neg = QDateEdit(); self.ed_data_neg.setCalendarPopup(True)
        self.cb_segmento = QComboBox(); self.cb_segmento.addItems(["PJ","PME","Corporate"])
        self.ed_cliente = QLineEdit()
        self.ed_cnpj = QLineEdit()
        self.ed_pacote = QLineEdit()
        self.ed_ag = QLineEdit()
        self.ed_cc = QLineEdit()
        self.ed_prazo = QLineEdit()
        self.ed_data_rev = QDateEdit(); self.ed_data_rev.setCalendarPopup(True)
        self.ed_motivo = QLineEdit()
        self.cb_tipo = QComboBox(); self.cb_tipo.addItems(["Novo","Renovação","Revisão"])

        def add(r,c,lab,w, wmin=200):
            labw = QLabel(lab); labw.setStyleSheet("background:transparent;")
            w.setMinimumWidth(wmin)
            form.addWidget(labw, r, c); form.addWidget(w, r, c+1)

        # Layout em 4 colunas (label/campo | label/campo)
        r=0
        add(r,0,"Data_Neg", self.ed_data_neg);      add(r,2,"Segmento", self.cb_segmento); r+=1
        add(r,0,"Cliente",  self.ed_cliente, 300);  add(r,2,"CNPJ",     self.ed_cnpj);     r+=1
        add(r,0,"Pacote",   self.ed_pacote, 240);   add(r,2,"AG",       self.ed_ag, 120);  r+=1
        add(r,0,"CC",       self.ed_cc, 160);       add(r,2,"Prazo",    self.ed_prazo, 140); r+=1
        add(r,0,"Data_Rev", self.ed_data_rev);      add(r,2,"Motivo",   self.ed_motivo, 240); r+=1
        add(r,0,"Tipo",     self.cb_tipo)

        root.addLayout(form)

        # ações
        actions = QHBoxLayout(); actions.addStretch()
        self.bt_clear = _btn("Limpar", accent=False)
        self.bt_cancel = _btn("Voltar", accent=False)
        self.bt_save   = _btn("Cadastrar")
        # no _build(), na barra de ações:
        bt_mass = _btn("Carregar em massa", accent=True)
        actions.addStretch(); actions.addWidget(bt_mass)
        bt_mass.clicked.connect(lambda: MassImportDialog("Pacote de Tarifas", FIELDS_PACOTE, self).exec())
        actions.addWidget(self.bt_clear); actions.addWidget(self.bt_cancel); actions.addWidget(self.bt_save)
        root.addLayout(actions)

        # sinais
        self.bt_clear.clicked.connect(self._clear)
        self.bt_cancel.clicked.connect(self._cancel)
        self.bt_save.clicked.connect(self._save)

    # ---------- helpers ----------
    def _has_any_text(self)->bool:
        eds = [self.ed_cliente,self.ed_cnpj,self.ed_pacote,self.ed_ag,self.ed_cc,self.ed_prazo,self.ed_motivo]
        return any(e.text().strip() for e in eds)

    def _clear(self):
        for w in [self.ed_cliente,self.ed_cnpj,self.ed_pacote,self.ed_ag,self.ed_cc,self.ed_prazo,self.ed_motivo]:
            w.clear()
        self.cb_segmento.setCurrentIndex(0); self.cb_tipo.setCurrentIndex(0)

    def _cancel(self):
        if self._has_any_text():
            m = QMessageBox(self); m.setWindowTitle("Cancelar")
            m.setText("Deseja cancelar o cadastro?\nOs dados preenchidos serão descartados.")
            m.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            m.setDefaultButton(QMessageBox.No)
            if m.exec()==QMessageBox.Yes:
                self.cancelled.emit()
        else:
            # sem nada preenchido → agir como 'voltar'
            self.cancelled.emit()

    @Slot()
    def _save(self):
        # validações mínimas (frontend)
        falta = []
        if not self.ed_cliente.text().strip(): falta.append("Cliente")
        if not self.ed_cnpj.text().strip():    falta.append("CNPJ")
        if not self.ed_pacote.text().strip():  falta.append("Pacote")
        if not self.ed_ag.text().strip():      falta.append("AG")
        if not self.ed_cc.text().strip():      falta.append("CC")
        if falta:
            QMessageBox.warning(self, "Campos obrigatórios",
                "Preencha: " + ", ".join(falta))
            return

        data: Dict[str,str] = {
            "Data_Neg": self.ed_data_neg.date().toString("dd/MM/yyyy"),
            "Segmento": self.cb_segmento.currentText(),
            "Cliente":  self.ed_cliente.text().strip(),
            "CNPJ":     self.ed_cnpj.text().strip(),
            "Pacote":   self.ed_pacote.text().strip(),
            "AG":       self.ed_ag.text().strip(),
            "CC":       self.ed_cc.text().strip(),
            "Prazo":    self.ed_prazo.text().strip(),
            "Data_Rev": self.ed_data_rev.date().toString("dd/MM/yyyy"),
            "Motivo":   self.ed_motivo.text().strip(),
            "Tipo":     self.cb_tipo.currentText(),
        }

        # Popup de sucesso com opções
        m = QMessageBox(self); m.setWindowTitle("Sucesso")
        m.setText("Cadastro realizado com sucesso.")
        viz = m.addButton("Visualizar", QMessageBox.AcceptRole)
        fechar = m.addButton("Fechar", QMessageBox.RejectRole)
        m.exec()
        # Em ambos os casos emitimos 'saved', e quem ouvir decide navegar
        self.saved.emit(data)
        # Se quiser diferenciar:
        # if m.clickedButton()==viz: ...

    def _open_mass_import(self):
        cols = ["Data_Neg","Segmento","Cliente","CNPJ","Pacote",
                "AG","CC","Prazo","Data_Rev","Motivo","Tipo"]
        dlg = MassImportDialog("Pacote de Tarifas", cols, self)
        if dlg.exec():
            pass

