from __future__ import annotations
from typing import Dict, List, Optional, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLabel, QAbstractItemView
)

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

# Colunas exibidas na grid (ordem fixa)
DISPLAY_COLS = [
    "Data_Ent","AREA","AG","CC","Vlr_EST","TAR","Vlr_CRED","Status","RESP","SEGMENTO","NOME"
]

def _btn(text: str, accent: bool = True, w: int = 120, h: int = 32) -> QPushButton:
    b = QPushButton(text)
    if accent: b.setProperty("accent","true")
    b.setFixedSize(w, h); b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b


class EstornoConsultaView(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        self.repo = None
        self._build()

    def attach_repo(self, repo):
        self.repo = repo

    # ---------------------- UI ----------------------
    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        # Filtros
        filters = QHBoxLayout(); filters.setSpacing(8)
        self.ed_ag = QLineEdit(placeholderText="Agência"); self.ed_ag.setFixedWidth(120)
        self.ed_cc = QLineEdit(placeholderText="Conta");   self.ed_cc.setFixedWidth(160)
        self.ed_cli= QLineEdit(placeholderText="Nome/Cliente"); self.ed_cli.setFixedWidth(240)
        self.ed_tar= QLineEdit(placeholderText="Tarifa");  self.ed_tar.setFixedWidth(120)
        bt_buscar = _btn("Buscar", True); bt_back = _btn("Voltar", False)

        filters.addWidget(self.ed_ag); filters.addWidget(self.ed_cc)
        filters.addWidget(self.ed_cli); filters.addWidget(self.ed_tar)
        filters.addWidget(bt_buscar); filters.addStretch()

        top = QHBoxLayout(); top.addLayout(filters, 1); top.addWidget(bt_back, 0, Qt.AlignRight)
        root.addLayout(top)

        # Tabela somente leitura + seleção por linha
        self.table = QTableWidget(0, len(DISPLAY_COLS))
        self.table.setHorizontalHeaderLabels(DISPLAY_COLS)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        for i, col in enumerate(DISPLAY_COLS):
            if col == "NOME":
                hh.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.table.setVisible(False)
        root.addWidget(self.table, stretch=1)

        # Ações
        actions = QHBoxLayout(); actions.setSpacing(12); actions.setAlignment(Qt.AlignRight)
        self._btn_atualizar = _btn("Atualizar selecionado", False, 180, 36); self._btn_atualizar.setVisible(False)
        self._btn_excluir   = _btn("Excluir selecionados",  True, 180, 36); self._btn_excluir.setVisible(False)
        actions.addStretch(); actions.addWidget(self._btn_atualizar); actions.addWidget(self._btn_excluir)
        root.addLayout(actions)

        # Conexões
        bt_buscar.clicked.connect(self._do_query)
        bt_back.clicked.connect(self.go_back.emit)
        self._btn_excluir.clicked.connect(self._confirm_delete)
        self._btn_atualizar.clicked.connect(self._open_update_dialog)

        # Habilita/desabilita botões conforme seleção
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    # ---------------------- API ----------------------
    def prefill(self, filtros: Dict[str, str], autorun: bool = False):
        self.ed_ag.setText(filtros.get("Agência","") or filtros.get("AG",""))
        self.ed_cc.setText(filtros.get("Conta","") or filtros.get("CC",""))
        self.ed_cli.setText(filtros.get("Cliente","") or filtros.get("NOME",""))
        self.ed_tar.setText(filtros.get("Tarifa","") or filtros.get("TAR",""))
        if autorun: self._do_query()

    def clear_filters(self):
        self.ed_ag.clear(); self.ed_cc.clear(); self.ed_cli.clear(); self.ed_tar.clear()
        self.table.clearContents(); self.table.setRowCount(0); self.table.setVisible(False)
        self._btn_excluir.setVisible(False); self._btn_atualizar.setVisible(False)

    def hideEvent(self, e):
        try: self.clear_filters()
        finally: super().hideEvent(e)

    # ---------------------- Core ----------------------
    def _do_query(self):
        ag = self.ed_ag.text().strip()
        cc = self.ed_cc.text().strip()
        nome = self.ed_cli.text().strip()
        tar = self.ed_tar.text().strip()
        if not any([ag, cc, nome, tar]):
            QMessageBox.information(self, "Consulta", "Informe pelo menos um filtro.")
            return

        rows: List[Dict[str, Any]] = []
        if self.repo:
            if hasattr(self.repo, "search_cadastro"):
                rows = self.repo.search_cadastro(ag=ag, cc=cc, nome=nome, tarifa=tar)
            else:
                rows = self.repo.search(ag=ag, cc=cc, cliente=nome, tarifa=tar)

        self._fill_table(rows)

    def _fill_table(self, rows: List[Dict[str, Any]]):
        self.table.setRowCount(len(rows))
        any_rows = len(rows) > 0

        for r, it in enumerate(rows):
            row_id = it.get("id") or it.get("Id") or it.get("ID")
            for c, col_name in enumerate(DISPLAY_COLS):
                val = self._get_val(it, col_name)
                item = QTableWidgetItem("" if val is None else str(val))
                if c == 0 and row_id is not None:
                    item.setData(Qt.UserRole, int(row_id))
                self.table.setItem(r, c, item)

        self.table.setVisible(any_rows)
        self._btn_excluir.setVisible(any_rows)
        self._btn_atualizar.setVisible(any_rows)
        self._on_selection_changed()

    def _get_val(self, row: Dict[str, Any], key: str) -> Any:
        if key in row: return row[key]
        low = {k.lower(): v for k, v in row.items()}
        kl = key.lower()
        if kl in low: return low[kl]
        aliases = {
            "nome": ["nome_cliente","cliente"],
            "tar":  ["tarifa","tar"],
            "data_Ent".lower(): ["data_ent","dt_ent","dataentrada","data","dt_est","dt_estorno"],
            "vlr_est": ["vlr_est","vlr_estornado","valor_estorno","valor_estornado"],
            "vlr_cred": ["vlr_cred","valor_credito","vlr_credito","credito"],
            "status": ["status","situacao","situação"],
            "resp": ["resp","responsavel","responsável"],
            "segmento": ["segmento"],
        }
        if kl in aliases:
            for a in aliases[kl]:
                if a in low: return low[a]
        return None

    # ---------------------- Seleção ----------------------
    def _on_selection_changed(self, *args):
        selected_rows = self._selected_row_indexes()
        self._btn_atualizar.setEnabled(len(selected_rows) == 1)
        self._btn_excluir.setEnabled(len(selected_rows) >= 1)

    def _selected_row_indexes(self) -> List[int]:
        sel = self.table.selectionModel().selectedRows()
        return sorted({i.row() for i in sel})

    def _selected_ids(self) -> List[int]:
        ids: List[int] = []
        for r in self._selected_row_indexes():
            item0 = self.table.item(r, 0)
            if not item0: continue
            row_id = item0.data(Qt.UserRole)
            if row_id is not None:
                ids.append(int(row_id))
        return ids

    # ---------------------- Exclusão ----------------------
    def _confirm_delete(self):
        ids = self._selected_ids()
        if not ids:
            QMessageBox.information(self, "Excluir", "Selecione ao menos um registro.")
            return

        # Popup de confirmação em TABELA (todas as colunas)
        dlg = QDialog(self); dlg.setWindowTitle("Confirmar exclusão")
        v = QVBoxLayout(dlg)

        header = QLabel("Os seguintes registros serão excluídos:")
        v.addWidget(header)

        preview = QTableWidget(len(self._selected_row_indexes()), len(DISPLAY_COLS))
        preview.setHorizontalHeaderLabels(DISPLAY_COLS)
        preview.verticalHeader().setVisible(False)
        preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        preview.setSelectionMode(QAbstractItemView.NoSelection)

        for i, r in enumerate(self._selected_row_indexes()):
            for c, col in enumerate(DISPLAY_COLS):
                orig = self.table.item(r, c)
                preview.setItem(i, c, QTableWidgetItem("" if orig is None else orig.text()))

        pv_h = preview.horizontalHeader()
        for c, col in enumerate(DISPLAY_COLS):
            if col == "NOME":
                pv_h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                pv_h.setSectionResizeMode(c, QHeaderView.ResizeToContents)

        v.addWidget(preview)

        btns = QHBoxLayout()
        bt_cancel = _btn("Cancelar", False, 120, 36)
        bt_del    = _btn("Excluir", True, 120, 36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_del)
        v.addLayout(btns)

        def do_delete():
            try:
                deleted = self.repo.delete_many(ids) if self.repo else 0
                QMessageBox.information(self, "Excluir", f"{deleted} registro(s) excluído(s) com sucesso.")
                dlg.accept()
                self._do_query()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir: {e}")

        bt_cancel.clicked.connect(dlg.reject)
        bt_del.clicked.connect(do_delete)
        dlg.exec()

    # ---------------------- Atualização ----------------------
    def _open_update_dialog(self):
        ids = self._selected_ids()
        if len(ids) != 1:
            QMessageBox.information(self, "Atualizar", "Selecione exatamente um registro para atualizar.")
            return
        rid = ids[0]

        if not self.repo or not hasattr(self.repo, "get_by_id"):
            QMessageBox.warning(self, "Atualizar", "Repositório não possui 'get_by_id'.")
            return

        data = self.repo.get_by_id(rid)
        if not data:
            QMessageBox.warning(self, "Atualizar", "Não foi possível carregar os dados do registro.")
            return

        # Dialog com campos exibidos
        dlg = QDialog(self); dlg.setWindowTitle(f"Atualizar registro #{rid}")
        v = QVBoxLayout(dlg)
        form = QFormLayout(); editors: Dict[str, QLineEdit] = {}

        from PySide6.QtWidgets import QLineEdit
        editable_keys = DISPLAY_COLS[:]  # travar algum? remova aqui (ex.: editable_keys.remove("Data_Ent"))
        for k in editable_keys:
            val = self._get_val(data, k)
            ed = QLineEdit("" if val is None else str(val))
            ed.setObjectName(k)
            editors[k] = ed
            form.addRow(QLabel(k), ed)

        v.addLayout(form)

        btns = QHBoxLayout()
        bt_cancel = _btn("Cancelar", False, 120, 36)
        bt_update = _btn("Atualizar", True, 120, 36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_update)
        v.addLayout(btns)

        def _to_repo_payload(payload_db: Dict[str, Any]) -> Dict[str, Any]:
            """
            Converte do que a UI exibe (DISPLAY_COLS/nomes de DB) para as form keys esperadas pelo repo.update_by_id,
            usando o repo.MAP (form_key -> DB_COL) quando existir. Resolve casos como TAR (UI) -> Tar (DB/MAP).
            """
            disp_to_db = {
                "Data_Ent":"DATA_ENT",
                "AREA":"AREA",
                "AG":"AG",
                "CC":"CC",
                "Vlr_EST":"VLR_EST",
                "TAR":"Tar",                 # atenção: no DB costuma ser 'Tar' (não 'TAR')
                "Vlr_CRED":"VLR_CRED",
                "Status":"STATUS",
                "RESP":"RESP",
                "SEGMENTO":"SEGMENTO",
                "NOME":"NOME_CLIENTE",
                "ID": "Id"
            }
            # inverte MAP: DB_COL -> form_key
            inv_map = {}
            if self.repo and hasattr(self.repo, "MAP"):
                inv_map = {str(db).upper(): fk for fk, db in self.repo.MAP.items()}

            out: Dict[str, Any] = {}
            for disp_k, v in payload_db.items():
                db_col = disp_to_db.get(disp_k, disp_k)
                form_k = inv_map.get(str(db_col).upper())
                if form_k:
                    out[form_k] = v
                else:
                    # fallback: envia a própria coluna DB (caso update_by_id aceite DB_COL)
                    out[db_col] = v
            return out

        def do_update():
            payload_db: Dict[str, Any] = {k: editors[k].text() for k in editors.keys()}
            payload_repo = _to_repo_payload(payload_db)

            try:
                ok = self.repo.update_by_id(rid, payload_repo) if self.repo else False
                if ok:
                    QMessageBox.information(self, "Atualizar", "Registro atualizado com sucesso.")
                    dlg.accept()
                    self._do_query()
                else:
                    QMessageBox.warning(self, "Atualizar", "Nada para atualizar.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao atualizar: {e}")

        bt_cancel.clicked.connect(dlg.reject)
        bt_update.clicked.connect(do_update)
        dlg.exec()
