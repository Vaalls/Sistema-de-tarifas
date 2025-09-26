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
    if accent: 
        b.setProperty("accent","true")
    b.setMinimumHeight(36); 
    b.setCursor(Qt.PointingHandCursor); 
    b.setStyleSheet(GOLD_HOVER)
    return b

def _date_ddmmyyyy(default_today: bool = True) -> QDateEdit:
    d = QDateEdit()
    d.setCalendarPopup(True)
    d.setDisplayFormat("dd/MM/yyyy")
    d.setButtonSymbols(QAbstractSpinBox.NoButtons)
    if default_today: d.setDate(QDate.currentDate())
    if d.lineEdit(): d.lineEdit().setInputMask("99/99/9999")
    return d

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
        root = QVBoxLayout(self); 
        root.setSpacing(12); 
        root.setContentsMargins(12,12,12,12)

        g = QGridLayout(); g.setHorizontalSpacing(12); g.setVerticalSpacing(10)

        def add(label: str, w: QWidget, row: int, col: int, span: int = 1, minw: int = 120):
            lab = QLabel(label); lab.setStyleSheet("background:transparent;")
            w.setMinimumWidth(minw)
            self.inputs[label] = w
            g.addWidget(lab, row, col)
            g.addWidget(w,   row, col+1, 1, span)

        # Linha 0 
        self.ed_data = _date_ddmmyyyy()
        add("DATA_NEG", self.ed_data, 0, 0)
        cb_seg = QComboBox(); cb_seg.addItems(["","EMPRESA","MIDDLE","CORPORATE", "LARGE", "CAPTAÇÃO", "OUTROS"])
        add("SEGMENTO", cb_seg, 0, 2)
        add("CNPJ", QLineEdit(), 0, 4, 1)

        # Linha 0
        add("CLIENTE", QLineEdit(), 1, 0, 1, 240)
        add("AGENCIA", QLineEdit(), 1, 2, 1, 90)
        add("CONTA", QLineEdit(), 1, 4, 1, 140)

        # Linha 1
        add("TARIFA",     QLineEdit(),     2, 0, 1, 100)
        v_tar = QDoubleSpinBox(); v_tar.setMaximum(1e9); v_tar.setDecimals(2)
        add("VALOR_TARIFA", v_tar,           2, 2, 1, 120)

        # Linha 2
        v_aut = QDoubleSpinBox(); v_aut.setMaximum(1e9); v_aut.setDecimals(2)
        add("VALOR_AUTORIZADO", v_aut, 2, 4, 1, 120)
        add("AUTORIZAÇÃO", QLineEdit(), 3, 0, 1, 200)

        # Linha 3
        sp_qtde = QSpinBox(); sp_qtde.setRange(0, 9999)
        add("QTDE", sp_qtde, 3, 2, 1, 100)

        self.sp_prazo = QSpinBox(); self.sp_prazo.setRange(0, 3650)  # dias
        add("PRAZO", self.sp_prazo, 3, 4, 1, 120)

        # Linha 6
        cb_neg_esp = QComboBox(); cb_neg_esp.addItems(["","N","S"])
        add("NEG_ESP", cb_neg_esp, 5, 0, 1, 100)
        add("PRAZO_SGN", QLineEdit(), 5, 2, 1, 140)

        # Linha 7 — Vencimento calculado
        self.ed_venc = _date_ddmmyyyy()
        self.ed_venc.setReadOnly(True)
        add("VENCIMENTO", self.ed_venc, 5, 4, 1, 140)

        cb_atuado = QComboBox(); cb_atuado.addItems(["","S","N"])
        add("ATUADO_SCT", cb_atuado, 6, 0, 1, 100)

        cb_motivo = QComboBox(); cb_motivo.addItems([
            "","ERRO OPERACIONAL","ERRO DE SISTEMA","COMERCIAL","ARQUIVADO","PENDENTE DE DOM","RECEPCIONADO",
            "RECUSADO","CLIENTE APLICADOR","ENCERRAMENTO DE CONTA","PACOTE ATIVO","TARIFA DEVIDA","CREDITADO",
            "DEVOLVIDO","ENCAMINHADO","FRANQUIA"
        ])
        add("MOTIVO", cb_motivo, 6, 2, 1, 200)
        add("USUÁRIO", QLineEdit(), 6, 4, 1, 140)

        add("OBSERVAÇÃO", QLineEdit(), 7, 0, 7, 420)

        root.addLayout(g)

       # Ações
        actions = QHBoxLayout(); actions.addStretch()
        btn_clear   = _btn("Limpar", accent=False)
        btn_cancel  = _btn("Voltar", accent=False)
        btn_save    = _btn("Cadastrar", accent=True)
        btn_mass    = _btn("Carregar em massa", accent=True)
        actions.addWidget(btn_clear); actions.addWidget(btn_cancel)
        actions.addWidget(btn_save);  actions.addSpacing(12); actions.addWidget(btn_mass)
        root.addLayout(actions)

        # Conexões
        btn_clear.clicked.connect(self._clear)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_save.clicked.connect(self._on_save)
        btn_mass.clicked.connect(self._open_mass_import)
       
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
            if isinstance(w, QLineEdit): 
                d[label] = w.text().strip()
            elif isinstance(w, QComboBox): 
                d[label] = w.currentText().strip()
            elif isinstance(w, QDateEdit): 
                d[label] = w.date().toString("dd/MM/yyyy")
            elif isinstance(w, QDoubleSpinBox): 
                d[label] = f"{w.value():.2f}".replace(".", ",")
            elif isinstance(w, QSpinBox): 
                d[label] = str(w.value())
        return d

    def _is_empty(self) -> bool:
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit) and w.text().strip(): 
                return False
            if isinstance(w, (QDoubleSpinBox, QSpinBox)) and w.value() > 0: 
                return False
            if isinstance(w, QComboBox) and w.currentIndex() > 0: 
                return False
        return True

    def _clear(self):
        from PySide6.QtWidgets import QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox
        for w in self.inputs.values():
            if isinstance(w, QLineEdit): 
                w.clear()
            elif isinstance(w, (QDoubleSpinBox, QSpinBox)): 
                w.setValue(0)
            elif isinstance(w, QComboBox): 
                w.setCurrentIndex(0)
            elif isinstance(w, QDateEdit): 
                w.setDate(QDate.currentDate())

    # Fluxo
    @Slot()
    def _on_cancel(self):
        if self._is_empty():
            self.cancelled.emit()
            return
        m = QMessageBox(self)
        m.setWindowTitle("Cancelar")
        m.setText("Deseja cancelar? Os dados preenchidos serão descartados.")
        m.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        m.setDefaultButton(QMessageBox.No)
        if m.exec() == QMessageBox.Yes:
            self.cancelled.emit()

    @Slot()
    def _on_save(self):
        d = self._collect()
        #Valor minimo para multas
        obrig = ["CLIENTE","CNPJ","AGENCIA","CONTA","TARIFA", "VALOR_TARIFA", "VALOR_AUTORIZADO", "AUTORIZAÇÃO", "QTDE", "PRAZO", "USUÁRIO"]
        faltam = [f for f in obrig if not d.get(f)]
        if faltam:
            QMessageBox.warning(self,"Campos obrigatórios","Preencha: "+", ".join(faltam)); 
            return

        m = QMessageBox(self); 
        m.setWindowTitle("Cadastro realizado"); 
        m.setText("Cadastro realizado com sucesso.")
        bt_vis = m.addButton("Visualizar", QMessageBox.AcceptRole)
        bt_close = m.addButton("Fechar", QMessageBox.RejectRole)
        m.exec()

        self._clear()
        self.saved.emit(d)

        if m.clickedButton() is bt_vis: 
            self.saved_view.emit(d)
        else:                         
            self.saved_close.emit(d)

    def _open_mass_import(self):
        cols = ["DATA_NEG","SEGMENTO","CNPJ","AGENCIA","CONTA","TARIFA",
                "VALOR_TARIFA","VALOR_AUTORIZADO","AUTORIZAÇÃO","QTDE",
                "PRAZO","NEG_ESP","PRAZO_SGN","VENCIMENTO", "OBSERVAÇÃO", "ATUADO_SCT", "MOTIVO", "USUÁRIO"]
        dlg = MassImportDialog("Negociação com Alçada", cols, self)
        if dlg.exec():
            pass
