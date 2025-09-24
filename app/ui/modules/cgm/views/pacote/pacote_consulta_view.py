# app/ui/modules/cgm/views/pacote/pacote_consulta_view.py
from __future__ import annotations
from typing import Dict, List, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLabel, QAbstractItemView, QApplication,
    QPlainTextEdit
)

GOLD="QPushButton:hover{background:#C49A2E;}"
def _btn(t,a=True,w=160,h=36):
    b=QPushButton(t)
    if a: b.setProperty("accent","true")
    b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD); 
    return b

DISPLAY_COLS=("DATA_NEG","SEGMENTO","CLIENTE","CNPJ"
              ,"PACOTE","AGENCIA","CONTA","MOTIVO", "OBS")

# label -> chave do dict que vem do repo
DISPLAY_TO_KEY = {
    "DATA_NEG": "DATA_NEG",
    "SEGMENTO": "SEGMENTO",
    "CLIENTE": "CLIENTE",
    "CNPJ": "CNPJ",
    "PACOTE": "PACOTE",
    "AGENCIA": "AGENCIA",
    "CONTA": "CONTA",
    "MOTIVO": "MOTIVO",
    "OBS": "OBS",               
}

class PacoteConsultaView(QWidget):
    go_back=Signal()
    def __init__(self):
        super().__init__()
        self.repo=None
        self._build()

    def attach_repo(self, repo): self.repo=repo

    def _build(self):
        root=QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)
        
        f=QHBoxLayout(); f.setSpacing(8)
        self.ed_seg=QLineEdit(placeholderText="Segmento"); self.ed_seg.setFixedWidth(160)
        self.ed_cli=QLineEdit(placeholderText="Cliente");  self.ed_cli.setFixedWidth(240)
        self.ed_cnpj=QLineEdit(placeholderText="CNPJ");    self.ed_cnpj.setFixedWidth(200)
        self.ed_ag  =QLineEdit(placeholderText="Agência"); self.ed_ag.setFixedWidth(120)
        bt_buscar=_btn("Buscar",True,120,36); bt_back=_btn("Voltar",False,120,36)
        for w in (self.ed_seg,self.ed_cli,self.ed_cnpj,self.ed_ag,bt_buscar): f.addWidget(w)
        f.addStretch()
        top=QHBoxLayout(); top.addLayout(f,1); top.addWidget(bt_back,0,Qt.AlignRight); 
        root.addLayout(top)

        self.table=QTableWidget(0,len(DISPLAY_COLS))
        self.table.setHorizontalHeaderLabels(DISPLAY_COLS)
        self.table.verticalHeader().setVisible(False)

                # >>> AJUSTES DE LEGIBILIDADE <<<
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)  # não coloca "..."
        vh = self.table.verticalHeader()
        vh.setDefaultSectionSize(28)               # altura base (cresce com resizeRowsToContents)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)  # operador pode redimensionar manualmente
        hh.setStretchLastSection(False)

        # larguras padrão generosas para CLIENTE e OBSERVAÇÃO
        self._col_idx = {name: i for i, name in enumerate(DISPLAY_COLS)}
        def _setw(name: str, w: int):
            if name in self._col_idx: self.table.setColumnWidth(self._col_idx[name], w)
        _setw("MOTIVO", 320)
        _setw("CLIENTE", 380)
        _setw("OBS", 400)

        self.table.setVisible(False)
        root.addWidget(self.table, stretch=1)

        # ações
        actions = QHBoxLayout(); actions.setSpacing(12); actions.setAlignment(Qt.AlignRight)
        self._bt_upd = _btn("Atualizar selecionado", False)
        self._bt_del = _btn("Excluir selecionados", True)
        self._bt_upd.setVisible(False); self._bt_del.setVisible(False)
        actions.addStretch(); actions.addWidget(self._bt_upd); actions.addWidget(self._bt_del)
        root.addLayout(actions)

        # conexões
        bt_buscar.clicked.connect(self._do)
        bt_back.clicked.connect(self.go_back.emit)
        self._bt_del.clicked.connect(self._confirm_delete)
        self._bt_upd.clicked.connect(self._open_update_dialog)
        self.table.selectionModel().selectionChanged.connect(self._on_sel)

    # API
    def prefill(self, filtros: Dict[str,str], autorun: bool=False):
        self.ed_seg.setText(filtros.get("Segmento","") or filtros.get("SEGMENTO",""))
        self.ed_cli.setText(filtros.get("Cliente","") or filtros.get("CLIENTE",""))
        self.ed_cnpj.setText(filtros.get("CNPJ",""))
        self.ed_ag.setText(filtros.get("AG","") or filtros.get("Agencia","") or filtros.get("AGENCIA",""))
        if autorun: self._do()

    def clear_filters(self):
        self.ed_seg.clear(); self.ed_cli.clear(); self.ed_cnpj.clear(); self.ed_ag.clear()
        self.table.clearContents(); self.table.setRowCount(0); self.table.setVisible(False)
        self._bt_upd.setVisible(False); self._bt_del.setVisible(False)

    def hideEvent(self,e):
        try: self.clear_filters()
        finally: super().hideEvent(e)

    # Preferir search_consulta (com os aliases certos); cair para search se necessário
    def _repo_search(self, seg:str, cli:str, cnpj:str, ag:str)->List[dict]:
        if not self.repo: return []
        if not hasattr(self.repo,"search_consulta"):
            raise AttributeError("search_consulta not implemented in repo")
        return self.repo.search_consulta(segmento=seg, cliente=cli, cnpj=cnpj, ag=ag)

    # core
    def _do(self):
        seg=self.ed_seg.text().strip(); cli=self.ed_cli.text().strip()
        cnpj=self.ed_cnpj.text().strip(); ag=self.ed_ag.text().strip()
        if not any([seg,cli,cnpj,ag]):
            QMessageBox.information(self,"Consulta","Informe ao menos um filtro.")
            return
        if not self.repo:
            QMessageBox.warning(self,"Consulta","Repositório não injetado. Chame attach_repo(AlcadaRepository).")
            return

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            rows = self._repo_search(seg, cli, cnpj, ag)
        except Exception as e:
            QMessageBox.critical(self, "Erro na consulta", f"{e}")
            rows = []
        finally:
            QApplication.restoreOverrideCursor()

        self._fill(rows)

    def _fill(self, rows:List[Dict[str,Any]]):
        self.table.setRowCount(len(rows)); any_rows=len(rows)>0
        for r,it in enumerate(rows):
            rid=it.get("id") or it.get("Id") or it.get("ID")
            for c,label in enumerate(DISPLAY_COLS):
                key = DISPLAY_TO_KEY.get(label, label)
                v=it.get(key, it.get(key.lower(),""))
                item=QTableWidgetItem("" if v is None else str(v))
                if c==0 and rid is not None: item.setData(Qt.UserRole,int(rid))
                self.table.setItem(r,c,item)

        self.table.setVisible(True)
        self.table.resizeRowsToContents()
        
        any_rows=len(rows)>0
        self._bt_upd.setVisible(any_rows); 
        self._bt_del.setVisible(any_rows)
        if not any_rows: QMessageBox.information(self,"Consulta","Nenhum registro encontrado.")
        self._on_sel()

    def _on_sel(self,*_):
        n=len(self.table.selectionModel().selectedRows())
        self._bt_upd.setEnabled(n==1); 
        self._bt_del.setEnabled(n>=1)

    def _selected_rows(self)->List[int]: 
        return sorted({i.row() for i in self.table.selectionModel().selectedRows()})
   
    def selected_ids(self)->List[int]:
        out=[]; 
        for r in self._selected_rows():
            it0=self.table.item(r,0)
            if it0:
                rid=it0.data(Qt.UserRole)
                if rid is not None: out.append(int(rid))
        return out

    def _confirm_delete(self):
        ids=self.selected_ids()
        if not ids: 
            QMessageBox.information(self,"Excluir","Selecione ao menos um registro."); 
            return
        
        dlg = QDialog(self); dlg.setWindowTitle("Confirmar exclusão")
        v = QVBoxLayout(dlg); v.addWidget(QLabel("Os seguintes registros serão excluídos:"))
        
        prev=QTableWidget(len(self._selected_rows()), len(DISPLAY_COLS))
        prev.setHorizontalHeaderLabels(DISPLAY_COLS); 
        prev.verticalHeader().setVisible(False)
        prev.setEditTriggers(QAbstractItemView.NoEditTriggers); 
        prev.setSelectionMode(QAbstractItemView.NoSelection)
        for i,r in enumerate(self._selected_rows()):
            for c,col in enumerate(DISPLAY_COLS):
                src=self.table.item(r,c); 
                prev.setItem(i,c,QTableWidgetItem("" if src is None else src.text()))
        prev.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        v.addWidget(prev)
        btns=QHBoxLayout(); bt_cancel=_btn("Cancelar",False,120,36); bt_del=_btn("Excluir",True,120,36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_del); v.addLayout(btns)
        def do_del():
            try:
                deleted=self.repo.delete_many(ids) if self.repo else 0
                QMessageBox.information(self,"Excluir",f"{deleted} registro(s) excluído(s).")
                dlg.accept(); self._do()
            except Exception as e:
                QMessageBox.critical(self,"Erro",f"Falha ao excluir: {e}")

        bt_cancel.clicked.connect(dlg.reject); bt_del.clicked.connect(do_del); 
        dlg.exec()

    def _open_update_dialog(self):
        ids=self.selected_ids()
        if len(ids)!=1: QMessageBox.information(self,"Atualizar","Selecione exatamente um registro."); return
        rid=ids[0]
        if not self.repo or not hasattr(self.repo,"get_by_id"): QMessageBox.warning(self,"Atualizar","Repositório sem get_by_id."); return
        data=self.repo.get_by_id(rid)
        if not data: QMessageBox.warning(self,"Atualizar","Não foi possível carregar os dados."); return
        dlg=QDialog(self); dlg.setWindowTitle(f"Atualizar registro #{rid}")
        v=QVBoxLayout(dlg); form=QFormLayout(); editors={}

        # editores (OBS em multiline)
        for label in DISPLAY_COLS:
            key = DISPLAY_TO_KEY.get(label,label)
            val = data.get(key, data.get(key.upper(), data.get(key.lower(), "")))
            if label=="OBS":
                ed=QPlainTextEdit("" if val is None else str(val)); ed.setFixedHeight(100)
            else:
                ed=QLineEdit("" if val is None else str(val))
                if label=="Cliente": ed.setMinimumWidth(360)
            ed.setObjectName(key); editors[key]=ed; form.addRow(QLabel(label), ed)
        v.addLayout(form)

        btns=QHBoxLayout(); bt_cancel=_btn("Cancelar",False,120,36); bt_upd=_btn("Atualizar",True,120,36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_upd); v.addLayout(btns)

        def do_upd():
            # monta payload e filtra apenas chaves reconhecidas pelo repo (evita erro se 'OBS' não existir no DB)
            payload={}
            for k, w in editors.items():
                payload[k] = w.toPlainText() if isinstance(w, QPlainTextEdit) else w.text()
            if hasattr(self.repo,"MAP"):
                allowed = set(self.repo.MAP.keys()) | set(self.repo.MAP.values())
                payload = {k:v for k,v in payload.items() if k in allowed}
            try:
                ok=self.repo.update_by_id(rid,payload) if self.repo else False
                if ok: QMessageBox.information(self,"Atualizar","Registro atualizado."); dlg.accept(); self._do()
                else: QMessageBox.warning(self,"Atualizar","Nada para atualizar.")
            except Exception as e:
                QMessageBox.critical(self,"Erro",f"Falha ao atualizar: {e}")

        bt_cancel.clicked.connect(dlg.reject); bt_upd.clicked.connect(do_upd); dlg.exec()
