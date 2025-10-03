from __future__ import annotations
from typing import Dict, List, Any
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtWidgets import *
from PySide6.QtGui import QCursor

GOLD = "QPushButton:hover{background:#C49A2E;}"
def _btn(t: str, a: bool=True, w: int=160, h: int=36) -> QPushButton:
    b = QPushButton(t)
    if a: b.setProperty("accent","true")
    b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD)
    return b

# Cabeçalhos exibidos (labels da UI)
DISPLAY_COLS = (
    "DATA_NEG","SEGMENTO","CLIENTE","CNPJ","AGENCIA","TARIFA",
    "VALOR_TARIFA","VALOR_AUTORIZADO","AUTORIZAÇÃO","QTDE",
    "PRAZO","VENCIMENTO","OBSERVAÇÃO"
)

DISPLAY_TO_KEY = {
    "DATA_NEG": "DATA_NEG",
    "SEGMENTO": "SEGMENTO",
    "CLIENTE":  "CLIENTE",
    "CNPJ":     "CNPJ",
    "AGENCIA":  "AGENCIA",
    "TARIFA":   "TARIFA",
    "VALOR_TARIFA":     "VALOR_MAJORADO",
    "VALOR_AUTORIZADO":  "VALOR_REQUERIDO",
    "AUTORIZAÇÃO":     "AUTORIZACAO",
    "QTDE":"QTDE",
    "PRAZO":     "PRAZO",
    "VENCIMENTO":"VENCIMENTO",
    "OBSERVAÇÃO":"OBSERVACAO",
}

DEFAULT_FILTERABLE_COLS = ("DATA_NEG", "TARIFA")

class AlcadaConsultaView(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        self.repo = None

        # estado de filtros e mapeamentos do cabeçalho
        self._active_filters: dict[int, dict] = {}      # col_idx -> {"type": "...", ...}
        self._idx_by_header: dict[str, int] = {}
        self._header_by_idx: dict[int, str] = {}
        self.FILTERABLE_COLS = tuple(DEFAULT_FILTERABLE_COLS)
        self._clear_on_next_show = False
        self._force_run = False

        self._build()

    def attach_repo(self, repo): 
        self.repo = repo

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setContentsMargins(12,12,12,12)

        # filtros
        f = QHBoxLayout(); f.setSpacing(8)

        self.ed_seg = QLineEdit(placeholderText="Segmento"); self.ed_seg.setFixedWidth(160)
        self.ed_cli = QLineEdit(placeholderText="Cliente");  self.ed_cli.setFixedWidth(240)
        self.ed_cnpj= QLineEdit(placeholderText="CNPJ");     self.ed_cnpj.setFixedWidth(200)
        self.ed_ag  = QLineEdit(placeholderText="Agência");  self.ed_ag.setFixedWidth(120)
        self.ed_tar = QLineEdit(placeholderText="Tarifa"); self.ed_tar.setFixedWidth(100)
        bt_buscar   = _btn("Buscar", True, 120, 36); bt_back=_btn("Voltar", False, 120, 36)
        for w in (self.ed_seg,self.ed_cli,self.ed_cnpj,self.ed_ag,self.ed_tar,bt_buscar): f.addWidget(w)
        f.addStretch()
        top = QHBoxLayout(); top.addLayout(f,1); top.addWidget(bt_back, 0, Qt.AlignRight); root.addLayout(top)

        # tabela
        self.table = QTableWidget(0, len(DISPLAY_COLS))
        self.table.setHorizontalHeaderLabels(DISPLAY_COLS)
        self.table.verticalHeader().setVisible(False)

        # >>> AJUSTES DE LEGIBILIDADE <<<
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)  
        self.table.verticalHeader().setDefaultSectionSize(28)
                     
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)  # operador pode redimensionar manualmente
        hh.setStretchLastSection(False)
        hh.setSectionsClickable(True)
        hh.sectionClicked.connect(self._on_header_left_click)
        hh.setContextMenuPolicy(Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self._on_header_context_menu)

        # mapas de cabeçalho
        self._idx_by_header = {name: i for i, name in enumerate(DISPLAY_COLS)}
        self._header_by_idx = {i: name for i, name in enumerate(DISPLAY_COLS)}

        # larguras padrão generosas para CLIENTE e OBSERVAÇÃO
        self._col_idx = {name: i for i, name in enumerate(DISPLAY_COLS)}
        def _setw(name: str, w: int):
            if name in self._col_idx: self.table.setColumnWidth(self._col_idx[name], w)
        _setw("CLIENTE", 320); _setw("VALOR_TARIFA", 160)
        _setw("OBSERVAÇÃO", 380); _setw("VALOR_AUTORIZADO", 160)
        _setw("AUTORIZAÇÃO", 180)

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
    def prefill(self, f: Dict[str,str], autorun: bool=False):

        def get_ci(*keys):
            # pega valor por qualquer chave (case-insensitive)
            for k in keys:
                if k in f:
                    return f[k]
            lk = {str(k).lower(): v for k, v in f.items()}
            for k in keys:
                v = lk.get(str(k).lower())
                if v is not None:
                    return v
            return ""

        seg = get_ci("SEGMENTO", "segmento", "Segmento")
        cli = get_ci("CLIENTE", "cliente", "Cliente")
        cnpj_raw = str(get_ci("CNPJ", "cnpj", "Cnpj") or "")
        ag = get_ci("AG", "AGENCIA", "Agência")
        tar = get_ci("TAR", "TARIFA", "Tarifa")

        self.ed_seg.setText(seg or "")
        self.ed_cli.setText(cli or "")
        self.ed_cnpj.setText(cnpj_raw or "")
        self.ed_ag.setText(ag or "")
        self.ed_tar.setText(tar or "")

        self._clear_on_next_show = False
                
        if autorun: 
            self._force_run = True
            self._do(force=True)

    def clear_filters(self):
        for w in (self.ed_seg,self.ed_cli,self.ed_cnpj,self.ed_ag, self.ed_tar): 
            w.clear()
        self.table.clearContents() 
        self.table.setRowCount(0) 
        self.table.setVisible(False)
        self._bt_upd.setVisible(False) 
        self._bt_del.setVisible(False)
        self._active_filters = {}

    def hideEvent(self,e):
        try:
                # se a janela principal está minimizada, NÃO limpa ao voltar
            win = self.window()
            if win and (win.windowState() & Qt.WindowMinimized):
                self._clear_on_next_show = False
            else:
                # escondeu por navegação/troca de tela → limpar ao voltar
                self._clear_on_next_show = True
        finally:
            super().hideEvent(e)

    def showEvent(self, e):
        super().showEvent(e)
        if getattr(self, "_clear_on_next_show", False):
            self.clear_filters()
            self._clear_on_next_show = False

    # chamada ao repo
    def _repo_search(self, seg: str, cli: str, cnpj: str, ag: str, tar: str) -> List[dict]:
        if not self.repo: return []
        if not hasattr(self.repo, "search_consulta"):
            raise AttributeError("Implante AlcadaRepository.search_consulta(...)")
        return self.repo.search_consulta(segmento=seg, cliente=cli, cnpj=cnpj, ag=ag, tarifa=tar )

    # core
    def _do(self, force = None):
        seg=self.ed_seg.text().strip() 
        cli=self.ed_cli.text().strip()
        cnpj=self.ed_cnpj.text().strip() 
        ag=self.ed_ag.text().strip()
        tar=self.ed_tar.text().strip()

        if not any([seg,cli,cnpj,ag, tar]) and not force:
            QMessageBox.information(self,"Consulta","Informe ao menos um filtro.")
            return
        if not self.repo:
            QMessageBox.warning(self,"Consulta","Repositório não conectado.")
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            rows = self._repo_search(seg, cli, cnpj, ag, tar)
        except Exception as e:
            QMessageBox.critical(self, "Erro na consulta", f"{e}")
            rows = []
        finally:
            QApplication.restoreOverrideCursor()
        self._fill(rows)

    def _fill(self, rows: List[Dict[str,Any]]):
        self.table.setRowCount(len(rows))
        for r, it in enumerate(rows):
            rid = it.get("id") or it.get("Id") or it.get("ID")
            for c, label in enumerate(DISPLAY_COLS):
                key = DISPLAY_TO_KEY.get(label, label)
                v = (
                    it.get(key) or
                    it.get(label) or
                    it.get(str(key).lower()) or
                    it.get(str(label).lower()) or
                    ""
                )
                item = QTableWidgetItem("" if v is None else str(v))
                if c == 0 and rid is not None:
                    item.setData(Qt.UserRole, int(rid))
                self.table.setItem(r, c, item)

        self.table.setVisible(True)
        self.table.resizeRowsToContents()
        self._apply_menu_filters()
        any_rows = len(rows) > 0
        self._bt_upd.setVisible(any_rows); self._bt_del.setVisible(any_rows)
        if not any_rows: QMessageBox.information(self, "Consulta", "Nenhum registro encontrado.")
        self._on_sel()
        
    # ---------- helpers de filtro/orden. ----------
    def _parse_qdate(self, s: str) -> QDate | None:
        if not s: return None
        txt = s.strip()[:10]
        # dd/MM/yyyy
        if "/" in txt:
            try:
                d, m, y = txt.split("/")
                return QDate(int(y), int(m), int(d))
            except: pass
        # yyyy-MM-dd
        if "-" in txt:
            try:
                y, m, d = txt.split("-")
                return QDate(int(y), int(m), int(d))
            except: pass
        return None

    def _distinct_values(self, col: int) -> list[str]:
        vals = set()
        for r in range(self.table.rowCount()):
            it = self.table.item(r, col)
            vals.add("" if it is None else it.text())
        return sorted(vals, key=lambda x: (x is None, x))

    def _apply_menu_filters(self):
        for r in range(self.table.rowCount()):
            hide = False
            for col, f in self._active_filters.items():
                if not f:  # sem filtro nessa coluna
                    continue
                typ = f.get("type")
                it = self.table.item(r, col)
                txt = "" if it is None else it.text()

                if typ == "set":
                    allowed = f.get("allowed", set())
                    if allowed and txt not in allowed: hide = True

                elif typ == "text":
                    pat = (f.get("pattern") or "").lower().strip()
                    if pat and pat not in (txt or "").lower(): hide = True

                elif typ == "date":
                    qd = self._parse_qdate(txt)
                    d0: QDate | None = f.get("start"); d1: QDate | None = f.get("end")
                    if qd is None and (d0 or d1):
                        hide = True
                    else:
                        if d0 and qd < d0: hide = True
                        if d1 and qd > d1: hide = True

                if hide: break
            self.table.setRowHidden(r, hide)

    def _on_header_left_click(self, col: int):
        self._show_header_menu(col)

    def _on_header_context_menu(self, pos):
        col = self.table.horizontalHeader().logicalIndexAt(pos)
        if col >= 0: self._show_header_menu(col)

    def _show_header_menu(self, col: int):
        col_name = self._header_by_idx.get(col, "")
        if col_name not in self.FILTERABLE_COLS:
            return

        menu = QMenu(self)
        container = QWidget(menu)
        v = QVBoxLayout(container); v.setContentsMargins(8, 8, 8, 8); v.setSpacing(6)

        # ----- DATA_NEG: filtro por intervalo de datas -----
        if col_name == "DATA_NEG":
            row_dates = QHBoxLayout()
            v.addWidget(QLabel("Intervalo de datas:"))

            de = QDateEdit(calendarPopup=True); de.setDisplayFormat("dd/MM/yyyy")
            ate = QDateEdit(calendarPopup=True); ate.setDisplayFormat("dd/MM/yyyy")

            # pré-preenche com min/max da coluna
            qs = []
            for r in range(self.table.rowCount()):
                it = self.table.item(r, col)
                qd = self._parse_qdate("" if it is None else it.text())
                if qd: qs.append(qd)
            if qs:
                de.setDate(min(qs)); ate.setDate(max(qs))
            else:
                de.setDate(QDate.currentDate()); ate.setDate(QDate.currentDate())

            # se já havia filtro ativo, restaura
            cur = self._active_filters.get(col, {})
            if cur.get("type") == "date":
                if cur.get("start"): de.setDate(cur["start"])
                if cur.get("end"):   ate.setDate(cur["end"])

            row_dates.addWidget(QLabel("De:")); row_dates.addWidget(de)
            row_dates.addSpacing(8)
            row_dates.addWidget(QLabel("Até:")); row_dates.addWidget(ate)
            v.addLayout(row_dates)

            # ordenar por data
            row_sort = QHBoxLayout()
            for txt, order in (("Mais recente → mais antiga", Qt.DescendingOrder),
                               ("Mais antiga → mais recente", Qt.AscendingOrder)):
                b = QPushButton(txt); b.setMinimumHeight(26); b.setProperty("accent","true")
                b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD)
                b.clicked.connect(lambda _=None, o=order: (self.table.sortItems(col, o), menu.close()))
                row_sort.addWidget(b)
            v.addLayout(row_sort)

            # aplicar/limpar
            row_btn = QHBoxLayout()
            btn_apply = QPushButton("Aplicar"); btn_clear = QPushButton("Limpar")
            for b in (btn_apply, btn_clear):
                b.setMinimumHeight(26); b.setProperty("accent","true")
                b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD)
            row_btn.addWidget(btn_apply); row_btn.addWidget(btn_clear); v.addLayout(row_btn)

            def apply_date():
                self._active_filters[col] = {"type": "date", "start": de.date(), "end": ate.date()}
                self._apply_menu_filters()

            def clear_date():
                self._active_filters[col] = {}
                self._apply_menu_filters()

            btn_apply.clicked.connect(lambda: (apply_date(), menu.close()))
            btn_clear.clicked.connect(lambda: (clear_date(), menu.close()))

        # ----- TARIFA: caixa de busca (contém) -----
        elif col_name == "TARIFA":
            v.addWidget(QLabel("Buscar (contém):"))
            ed = QLineEdit()
            cur = self._active_filters.get(col, {})
            if cur.get("type") == "text": ed.setText(cur.get("pattern", ""))

            v.addWidget(ed)

            row_sort = QHBoxLayout()
            for txt, order in (("A → Z", Qt.AscendingOrder), ("Z → A", Qt.DescendingOrder)):
                b = QPushButton(txt); b.setMinimumHeight(26); b.setProperty("accent","true")
                b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD)
                b.clicked.connect(lambda _=None, o=order: (self.table.sortItems(col, o), menu.close()))
                row_sort.addWidget(b)
            v.addLayout(row_sort)

            row_btn = QHBoxLayout()
            btn_apply = QPushButton("Aplicar"); btn_clear = QPushButton("Limpar")
            for b in (btn_apply, btn_clear):
                b.setMinimumHeight(26); b.setProperty("accent","true")
                b.setCursor(Qt.PointingHandCursor); b.setStyleSheet(GOLD)
            row_btn.addWidget(btn_apply); row_btn.addWidget(btn_clear); v.addLayout(row_btn)

            def apply_text():
                pattern = ed.text().strip()
                self._active_filters[col] = {"type": "text", "pattern": pattern}
                self._apply_menu_filters()

            def clear_text():
                self._active_filters[col] = {}
                self._apply_menu_filters()

            btn_apply.clicked.connect(lambda: (apply_text(), menu.close()))
            btn_clear.clicked.connect(lambda: (clear_text(), menu.close()))

        # (se futuramente quiser outras colunas com checkboxes, dá
        # para adicionar um terceiro ramo aqui com type "set")
        act = QWidgetAction(menu); act.setDefaultWidget(container); menu.addAction(act)
        menu.exec(QCursor.pos())

    def _on_sel(self,*_):
        n = len(self.table.selectionModel().selectedRows())
        self._bt_upd.setEnabled(n==1)
        self._bt_del.setEnabled(n>=1)

    def _selected_rows(self)->List[int]:
        return sorted({i.row() for i in self.table.selectionModel().selectedRows()})

    def _selected_ids(self)->List[int]:
        ids=[]
        for r in self._selected_rows():
            it0 = self.table.item(r,0)
            if it0:
                rid = it0.data(Qt.UserRole)
                if rid is not None: ids.append(int(rid))
        return ids

    # EXCLUSÃO
    def _confirm_delete(self):
        ids = self._selected_ids()
        if not ids:
            QMessageBox.information(self,"Excluir","Selecione ao menos um registro.")
            return

        dlg = QDialog(self); dlg.setWindowTitle("Confirmar exclusão")
        v = QVBoxLayout(dlg); v.addWidget(QLabel("Os seguintes registros serão excluídos:"))

        prev = QTableWidget(len(self._selected_rows()), len(DISPLAY_COLS))
        prev.setHorizontalHeaderLabels(DISPLAY_COLS)
        prev.verticalHeader().setVisible(False)
        prev.setEditTriggers(QAbstractItemView.NoEditTriggers)
        prev.setSelectionMode(QAbstractItemView.NoSelection)
        for i, r in enumerate(self._selected_rows()):
            for c, col in enumerate(DISPLAY_COLS):
                src = self.table.item(r,c)
                prev.setItem(i,c,QTableWidgetItem("" if src is None else src.text()))
        hh = prev.horizontalHeader()
        for i,col in enumerate(DISPLAY_COLS):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
        v.addWidget(prev)

        btns = QHBoxLayout(); bt_cancel=_btn("Cancelar",False,120,36); bt_del=_btn("Excluir",True,120,36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_del); v.addLayout(btns)

        def do_delete():
            try:
                deleted = self.repo.delete_many(ids) if self.repo else 0
                QMessageBox.information(self,"Excluir",f"{deleted} registro(s) excluído(s).")
                dlg.accept(); self._do()
            except Exception as e:
                QMessageBox.critical(self,"Erro",f"Falha ao excluir: {e}")

        bt_cancel.clicked.connect(dlg.reject); bt_del.clicked.connect(do_delete); dlg.exec()

    # ATUALIZAÇÃO
    def _open_update_dialog(self):
        ids = self._selected_ids()
        if len(ids) != 1:
            QMessageBox.information(self, "Atualizar", "Selecione exatamente um registro.")
            return
        rid = ids[0]
        if not self.repo or not hasattr(self.repo, "get_by_id"):
            QMessageBox.warning(self, "Atualizar", "Repositório sem get_by_id.")
            return
        data = self.repo.get_by_id(rid)
        if not data:
            QMessageBox.warning(self, "Atualizar", "Não foi possível carregar os dados.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Atualizar registro #{rid}")
        dlg.setSizeGripEnabled(True)
        scr = QApplication.primaryScreen().availableGeometry()
        dlg.resize(min(900, int(scr.width()*0.7)), min(650, int(scr.height()*0.75)))

        root = QVBoxLayout(dlg); root.setContentsMargins(12,12,12,12); root.setSpacing(10)
        scroll = QScrollArea(dlg); scroll.setWidgetResizable(True)
        wrap = QWidget(); form = QFormLayout(wrap); editors = {}

        DATE_FIELDS = {"DATA_NEG", "VENCIMENTO"}

        for label in DISPLAY_COLS:
            key = DISPLAY_TO_KEY.get(label, label)
            val = data.get(key, data.get(key.upper(), data.get(key.lower(), "")))

            if key in DATE_FIELDS:
                # editor de data
                ed = QDateEdit(calendarPopup=True)
                ed.setDisplayFormat("dd/MM/yyyy")
                # tenta carregar a data atual
                qd = self._parse_qdate(str(val or ""))
                ed.setDate(qd if qd else QDate.currentDate())
            elif key == "OBSERVACAO":
                ed = QPlainTextEdit("" if val is None else str(val))
                ed.setMinimumHeight(120)
            else:
                ed = QLineEdit("" if val is None else str(val))
                if key == "CLIENTE":
                    ed.setMinimumWidth(360)

            ed.setObjectName(key)
            editors[key] = ed
            form.addRow(QLabel(label), ed)

        scroll.setWidget(wrap)
        root.addWidget(scroll, 1)

        btns = QHBoxLayout()
        bt_cancel = _btn("Cancelar", False, 120, 36)
        bt_upd    = _btn("Atualizar", True, 120, 36)
        btns.addStretch(); btns.addWidget(bt_cancel); btns.addWidget(bt_upd)
        root.addLayout(btns)

        def do_update():
            payload_db = {}
            only_cols  = []

            for k, w in editors.items():
                if isinstance(w, QDateEdit):
                    new_val = w.date().toString("dd/MM/yyyy")
                elif isinstance(w, QPlainTextEdit):
                    new_val = w.toPlainText()
                else:
                    new_val = w.text()

                old_val = str(data.get(k) or data.get(k.upper()) or data.get(k.lower()) or "")

                # envia apenas o que realmente mudou e não está vazio
                if new_val.strip() and new_val.strip() != old_val.strip():
                    payload_db[k] = new_val
                    only_cols.append(k)

            if not payload_db:
                QMessageBox.information(self, "Atualizar", "Nada para atualizar.")
                return

            try:
                ok = self.repo.update_by_id(rid, payload_db, only=only_cols)
                if ok:
                    QMessageBox.information(self, "Atualizar", "Registro atualizado.")
                    dlg.accept()
                    self._do()
                else:
                    QMessageBox.warning(self, "Atualizar", "Nada para atualizar.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao atualizar: {e}")

        bt_cancel.clicked.connect(dlg.reject)
        bt_upd.clicked.connect(do_update)

        # >>> Faltava isto: exibe o diálogo <<<
        dlg.exec()