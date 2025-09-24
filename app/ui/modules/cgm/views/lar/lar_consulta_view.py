# app/ui/modules/cgm/views/lar/lar_consulta_view.py
from __future__ import annotations
from typing import Dict, List, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *
GOLD="QPushButton:hover{background:#C49A2E;}"
def _btn(t,a=True,w=160,h=36):
    b=QPushButton(t); 
    if a: b.setProperty("accent","true")
    b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD); 
    return b

DISPLAY_COLS=("Cliente","CNPJ","Segmento","AG","Vlr_Tar_Ref","Vlr_Auto","Vlr_Lar","Vencimento")

class LarConsultaView(QWidget):
    go_back=Signal()
    def __init__(self): super().__init__(); self.repo=None; self._build()
    def attach_repo(self, repo): self.repo=repo

    def _build(self):
        root=QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)
        f=QHBoxLayout(); f.setSpacing(8)
        self.ed_seg=QLineEdit(placeholderText="Segmento"); self.ed_seg.setFixedWidth(160)
        self.ed_cli=QLineEdit(placeholderText="Cliente");  self.ed_cli.setFixedWidth(240)
        self.ed_cnpj=QLineEdit(placeholderText="CNPJ");    self.ed_cnpj.setFixedWidth(200)
        bt_buscar=_btn("Buscar",True,120,36); bt_back=_btn("Voltar",False,120,36)
        for w in (self.ed_seg,self.ed_cli,self.ed_cnpj,bt_buscar): f.addWidget(w)
        f.addStretch(); top=QHBoxLayout(); top.addLayout(f,1); top.addWidget(bt_back,0,Qt.AlignRight); root.addLayout(top)

        self.table=QTableWidget(0,len(DISPLAY_COLS)); self.table.setHorizontalHeaderLabels(DISPLAY_COLS)
        self.table.verticalHeader().setVisible(False)
        hh=self.table.horizontalHeader()
        for i,c in enumerate(DISPLAY_COLS):
            hh.setSectionResizeMode(i, QHeaderView.Stretch if c=="Cliente" else QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setVisible(False); root.addWidget(self.table, stretch=1)

        acts=QHBoxLayout(); acts.setAlignment(Qt.AlignRight); acts.setSpacing(12)
        self._bt_upd=_btn("Atualizar selecionado",False); self._bt_del=_btn("Excluir selecionados",True)
        self._bt_upd.setVisible(False); self._bt_del.setVisible(False)
        acts.addStretch(); acts.addWidget(self._bt_upd); acts.addWidget(self._bt_del); root.addLayout(acts)

        bt_buscar.clicked.connect(self._do); bt_back.clicked.connect(self.go_back.emit)
        self._bt_del.clicked.connect(self._confirm_delete); self._bt_upd.clicked.connect(self._open_update_dialog)
        self.table.selectionModel().selectionChanged.connect(self._on_sel)

    def prefill(self,f:Dict[str,str], autorun:bool=False):
        self.ed_seg.setText(f.get("Segmento","")); self.ed_cli.setText(f.get("Cliente","")); self.ed_cnpj.setText(f.get("CNPJ",""))
        if autorun: self._do()

    def clear_filters(self):
        self.ed_seg.clear(); self.ed_cli.clear(); self.ed_cnpj.clear()
        self.table.clearContents(); self.table.setRowCount(0); self.table.setVisible(False)
        self._bt_upd.setVisible(False); self._bt_del.setVisible(False)

    def hideEvent(self,e):
        try: self.clear_filters()
        finally: super().hideEvent(e)

    def _do(self):
        seg=self.ed_seg.text().strip(); cli=self.ed_cli.text().strip(); cnpj=self.ed_cnpj.text().strip()
        if not any([seg,cli,cnpj]): QMessageBox.information(self,"Consulta","Informe ao menos um filtro."); return
        rows = self.repo.search(segmento=seg, cliente=cli, cnpj=cnpj) if self.repo else []
        self._fill(rows)

    def _fill(self, rows:List[Dict[str,Any]]):
        self.table.setRowCount(len(rows)); any_rows=len(rows)>0
        for r,it in enumerate(rows):
            rid = it.get("id") or it.get("Id") or it.get("ID")
            for c,k in enumerate(DISPLAY_COLS):
                v = it.get(k, it.get(k.lower(),""))
                item = QTableWidgetItem("" if v is None else str(v))
                if c==0 and rid is not None: item.setData(Qt.UserRole,int(rid))
                self.table.setItem(r,c,item)
        self.table.setVisible(any_rows); self._bt_upd.setVisible(any_rows); self._bt_del.setVisible(any_rows)
        self._on_sel()

    def _on_sel(self,*_):
        n=len(self.table.selectionModel().selectedRows())
        self._bt_upd.setEnabled(n==1); self._bt_del.setEnabled(n>=1)

    def _rows(self)->List[int]: return sorted({i.row() for i in self.table.selectionModel().selectedRows()})
    def _ids(self)->List[int]:
        out=[]; 
        for r in self._rows():
            it0=self.table.item(r,0)
            if it0:
                rid=it0.data(Qt.UserRole)
                if rid is not None: out.append(int(rid))
        return out

    def _confirm_delete(self):
        ids=self._ids()
        if not ids: QMessageBox.information(self,"Excluir","Selecione ao menos um registro."); return
        dlg=QDialog(self); dlg.setWindowTitle("Confirmar exclusão")
        v=QVBoxLayout(dlg); v.addWidget(QLabel("Os seguintes registros serão excluídos:"))
        prev=QTableWidget(len(self._rows()), len(DISPLAY_COLS))
        prev.setHorizontalHeaderLabels(DISPLAY_COLS); prev.verticalHeader().setVisible(False)
        prev.setEditTriggers(QAbstractItemView.NoEditTriggers); prev.setSelectionMode(QAbstractItemView.NoSelection)
        for i,r in enumerate(self._rows()):
            for c,col in enumerate(DISPLAY_COLS):
                src=self.table.item(r,c); prev.setItem(i,c,QTableWidgetItem("" if src is None else src.text()))
        hh=prev.horizontalHeader()
        for i,col in enumerate(DISPLAY_COLS):
            hh.setSectionResizeMode(i, QHeaderView.Stretch if col=="Cliente" else QHeaderView.ResizeToContents)
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
        bt_cancel.clicked.connect(dlg.reject); bt_del.clicked.connect(do_del); dlg.exec()

    def _open_update_dialog(self):
        ids=self._ids()
        if len(ids)!=1: QMessageBox.information(self,"Atualizar","Selecione exatamente um registro."); return
        rid=ids[0]
        if not self.repo or not hasattr(self.repo,"get_by_id"): QMessageBox.warning(self,"Atualizar","Repositório sem get_by_id."); return
        data=self.repo.get_by_id(rid)
        if not data: QMessageBox.warning(self,"Atualizar","Não foi possível carregar os dados."); return
        dlg=QDialog(self); dlg.setWindowTitle(f"Atualizar registro #{rid}")
        v=QVBoxLayout(dlg); form=QFormLayout(); editors={}
        from PySide6.QtWidgets import QLineEdit
        for k in DISPLAY_COLS:
            val=data.get(k, data.get(k.lower(),""))
            ed=QLineEdit("" if val is None else str(val)); ed.setObjectName(k)
            editors[k]=ed; form.addRow(QLabel(k),ed)
        v.addLayout(form)
        btns=QHBoxLayout(); bt_cancel=_btn("Cancelar",False,120,36); bt_upd=_btn("Atualizar",True,120,36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_upd); v.addLayout(btns)

        def to_payload(db:Dict[str,Any])->Dict[str,Any]:
            disp_to_db={
                "Cliente":"CLIENTE","CNPJ":"CNPJ","Segmento":"SEGMENTO","AG":"AGENCIA","Vlr_Tar_Ref":"VALOR_MAJORADO",
                "Vlr_Auto":"VALOR_REQUERIDO","Vlr_Lar":"VALOR_LAR","Vencimento":"VENCIMENTO"
            }
            inv_map={}
            if hasattr(self.repo,"MAP"): inv_map={str(db).upper(): fk for fk,db in self.repo.MAP.items()}
            out={}
            for disp,val in db.items():
                col=disp_to_db.get(disp,disp); fk=inv_map.get(str(col).upper())
                if fk: out[fk]=val
                else: out[col]=val
            return out

        def do_upd():
            payload_db={k: editors[k].text() for k in editors}
            payload=to_payload(payload_db)
            try:
                ok=self.repo.update_by_id(rid,payload) if self.repo else False
                if ok: QMessageBox.information(self,"Atualizar","Registro atualizado."); dlg.accept(); self._do()
                else: QMessageBox.warning(self,"Atualizar","Nada para atualizar.")
            except Exception as e:
                QMessageBox.critical(self,"Erro",f"Falha ao atualizar: {e}")

        bt_cancel.clicked.connect(dlg.reject); bt_upd.clicked.connect(do_upd); dlg.exec()
