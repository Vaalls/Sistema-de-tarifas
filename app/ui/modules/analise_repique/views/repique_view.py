# app/ui/modules/analise_repique/views/repique_view.py
from __future__ import annotations
import os, json, csv
from pathlib import Path
from typing import List, Tuple, Dict, Set
from urllib.parse import quote
from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QMenu, QWidgetAction,
    QDialog, QVBoxLayout as QVBox, QTableWidget as QTable, QDialogButtonBox, QLabel
)

from app.core.i18n.i18n import I18n
from app.ui.components.toasts import Toast
from app.core.data.repique_repository import RepiqueRepository
from app.ui.modules.analise_repique.viewmodels.repique_vm import RepiqueViewModel, RepiqueRow


# ---------------- Histórico em JSON + CSV ----------------
class HistoryStore:
    """Persistência simples do histórico de análises."""
    def __init__(self, filename: str = None):
        base = Path(os.path.expanduser("~")) / ".safra_app"
        base.mkdir(parents=True, exist_ok=True)
        self.path = Path(filename) if filename else base / "repique_history.json"

    def load(self) -> List[Dict]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_all(self, data: List[Dict]) -> None:
        try:
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def add_entry(
        self, user: str, when: datetime, count: int, filters: Dict[int, List[str]],
        total_value: float, count_ge50k: int, started_at: datetime | None
    ):
        data = self.load()
        data.insert(0, {
            "user": user or "operador",
            "when": when.strftime("%d/%m/%Y %H:%M"),
            "count": int(count),
            "count_ge50k": int(count_ge50k),
            "total_value": float(total_value),
            "filters": {str(k): v for k, v in filters.items() if v},
            "started_at": started_at.strftime("%d/%m/%Y %H:%M:%S") if started_at else None,
            "ended_at": None,
            "duration_secs": None
        })
        self.save_all(data)

    def complete_last(self, ended_when: datetime, duration_secs: int):
        data = self.load()
        if not data:
            return
        # atualiza o item mais recente
        data[0]["ended_at"] = ended_when.strftime("%d/%m/%Y %H:%M:%S")
        data[0]["duration_secs"] = int(duration_secs)
        self.save_all(data)

    def export_csv(self, csv_path: str):
        rows = self.load()
        cols = ["user","when","started_at","ended_at","duration_secs",
                "count","count_ge50k","total_value","filters"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({
                    "user": r.get("user",""),
                    "when": r.get("when",""),
                    "started_at": r.get("started_at",""),
                    "ended_at": r.get("ended_at",""),
                    "duration_secs": r.get("duration_secs",""),
                    "count": r.get("count",""),
                    "count_ge50k": r.get("count_ge50k",""),
                    "total_value": f'{float(r.get("total_value",0)):,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."),
                    "filters": json.dumps(r.get("filters",{}), ensure_ascii=False)
                })


class RepiqueView(QWidget):
    # Índices de coluna
    COL_CHECK   = 0
    COL_CNPJ    = 1
    COL_CLIENTE = 2
    COL_GRUPO   = 3
    COL_TARIFA  = 4
    COL_AGENCIA = 5
    COL_CONTA   = 6
    COL_DATA    = 7
    COL_MESREF  = 8
    COL_VALOR   = 9
    COL_ESTAB   = 10
    COL_HIST    = 11
    COL_LOTE    = 12
    COL_STATUS  = 13
    COL_MODAL   = 14
    COL_DEBC    = 15
    COL_RAT     = 16
    COL_WORK    = 17
    COL_RESTR   = 18
    COL_SEG     = 19
    COL_OBS     = 20

    HEADERS = [
        " ", "CNPJ/CPF", "Cliente", "Grupo Econ", "Tarifa",
        "Agência", "Conta", "Data", "MesRef", "Valor (R$)",
        "Estab_CNPJ", "Histórico", "Lote", "Status",
        "Modal", "Debc", "RAT", "Workout", "Restr_Int", "Segmento", "OBS"
    ]

    NUMERIC_INT_COLS   = {COL_TARIFA, COL_AGENCIA, COL_CONTA, COL_LOTE}
    NUMERIC_FLOAT_COLS = {COL_VALOR}

    def __init__(self, i18n: I18n, repo: RepiqueRepository):
        super().__init__()
        self.i18n = i18n
        self.repo = repo
        self.vm = RepiqueViewModel()

        self._active_filters: Dict[int, Set[str]] = {}
        self._obs_by_index: Dict[int, str] = {}

        self._email_to: List[str] = ["gestora@safra.com.br"]
        self._email_cc: List[str] = ["coordenacao@safra.com.br"]

        self._history = HistoryStore()
        self._current_user = os.getenv("USERNAME") or os.getenv("USER") or "operador"
        self._last_selection_count = 0
        self._last_selection_total = 0.0
        self._last_selection_ge50k = 0
        self._analysis_start: datetime | None = None

        self._build()

    # ========== UI ==========
    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(10)

        # Barra de ações
        actions = QHBoxLayout(); actions.setSpacing(8)

        self.btn_carregar = QPushButton("Carregar linhas")
        self.btn_enviar   = QPushButton("Enviar e-mail")
        self.btn_analise  = QPushButton("Análise")
        self.btn_historico= QPushButton("Histórico")

        for b in (self.btn_carregar, self.btn_enviar, self.btn_analise, self.btn_historico):
            b.setProperty("accent", "true")
            b.setMinimumHeight(32)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")

        actions.addStretch()
        actions.addWidget(self.btn_carregar)
        actions.addWidget(self.btn_enviar)
        actions.addWidget(self.btn_analise)
        actions.addStretch()
        actions.addWidget(self.btn_historico)
        root.addLayout(actions, 0)

        # Tabela
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setStretchLastSection(True)
        hh.setSectionsClickable(True)
        hh.sectionClicked.connect(self._on_header_left_click)
        hh.setContextMenuPolicy(Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self._on_header_context_menu)

        self.table.setColumnWidth(self.COL_CHECK, 36)
        self.table.setColumnWidth(self.COL_CLIENTE, 220)
        self.table.setColumnWidth(self.COL_HIST, 220)
        self.table.setColumnWidth(self.COL_OBS, 240)

        root.addWidget(self.table, 1)

        # Conexões
        self.btn_carregar.clicked.connect(self._on_carregar_sql)
        self.btn_analise.clicked.connect(self._on_analise)
        self.btn_enviar.clicked.connect(self._on_enviar)
        self.btn_historico.clicked.connect(self._on_historico)

    # ========= Helpers =========
    def _checkbox_center_widget(self, checked: bool) -> QWidget:
        wrap = QWidget()
        lay = QHBoxLayout(wrap); lay.setContentsMargins(0,0,0,0); lay.setAlignment(Qt.AlignCenter)
        cb = QCheckBox(); cb.setChecked(checked); lay.addWidget(cb)
        return wrap

    def _fmt_moeda(self, v) -> str:
        try:   return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except: return "0,00"

    def _fmt_data(self, d) -> str:
        if not d: return ""
        try: return d.strftime("%d/%m/%Y")
        except:
            s = str(d)
            return f"{s[6:8]}/{s[4:6]}/{s[0:4]}" if len(s) >= 8 else s[:10]

    def _fmt_mesref(self, d) -> tuple[str, int]:
        if not d: return "", 0
        try:
            mm = f"{d.month:02d}"; yy = f"{d.year:04d}"
            return f"{mm}/{yy}", int(yy) * 100 + int(mm)
        except:
            s = str(d)
            if len(s) >= 8:
                yy, mm = s[0:4], s[4:6]
                return f"{mm}/{yy}", int(yy) * 100 + int(mm)
            return s, 0

    # ========= preencher =========
    def _fill_table(self):
        rows = self.vm.rows
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            # sem marcação automática
            self.table.setCellWidget(r, self.COL_CHECK, self._checkbox_center_widget(False))

            mesref_txt, mesref_key = self._fmt_mesref(row.dt)

            data_map = [
                row.cnpj_cpf or "", row.cliente or "", row.grupo_econ or "", row.tarifa or "",
                row.agencia or "", row.conta or "", self._fmt_data(row.dt), mesref_txt, self._fmt_moeda(row.valor),
                row.estab_cnpj or "", row.historico or "", row.lote or "", row.desc_status or "",
                row.modal or "", row.debc or "", row.rat or "", row.workout or "",
                row.restr_int or "", row.segmento or "", self._obs_by_index.get(r, "")
            ]

            for c, txt in enumerate(data_map, start=1):
                it = QTableWidgetItem(txt)

                if c in self.NUMERIC_INT_COLS:
                    try: it.setData(Qt.EditRole, int(str(txt).replace(".", "").replace(",", "")))
                    except: it.setData(Qt.EditRole, 0)
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                elif c in self.NUMERIC_FLOAT_COLS:
                    try: it.setData(Qt.EditRole, float(str(txt).replace(".", "").replace(",", ".").replace("R$ ", "")))
                    except: it.setData(Qt.EditRole, 0.0)
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                elif c == self.COL_DATA:
                    try:
                        dd, mm, yy = str(txt).split("/")
                        it.setData(Qt.EditRole, int(yy) * 10000 + int(mm) * 100 + int(dd))
                    except: it.setData(Qt.EditRole, 0)
                    it.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

                elif c == self.COL_MESREF:
                    it.setData(Qt.EditRole, mesref_key)
                    it.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

                else:
                    it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

                self.table.setItem(r, c, it)

            idx_item = self.table.item(r, self.COL_CNPJ)
            if idx_item: idx_item.setData(Qt.UserRole, r)

        self._apply_menu_filters()

    # ========= filtros/ordenação =========
    def _distinct_values(self, col: int) -> List[str]:
        vals: Set[str] = set()
        for r in range(self.table.rowCount()):
            it = self.table.item(r, col)
            if it: vals.add(it.text())
        return sorted(vals)

    def _apply_menu_filters(self):
        for r in range(self.table.rowCount()):
            hide = False
            for col, allowed in self._active_filters.items():
                if not allowed: continue
                it = self.table.item(r, col)
                if it and it.text() not in allowed:
                    hide = True; break
            self.table.setRowHidden(r, hide)

    def _on_header_context_menu(self, pos):
        col = self.table.horizontalHeader().logicalIndexAt(pos)
        if col >= 0: self._show_header_menu(col)

    def _on_header_left_click(self, col: int):
        # clique normal também abre o menu (estilo Excel)
        self._show_header_menu(col)

    def _show_header_menu(self, col: int):
        if col == self.COL_CHECK: return
        is_date    = (col in (self.COL_DATA, self.COL_MESREF))
        is_numeric = (col in self.NUMERIC_INT_COLS) or (col in self.NUMERIC_FLOAT_COLS)

        menu = QMenu(self)
        container = QWidget(menu); v = QVBox(container)
        v.setContentsMargins(8,8,8,8); v.setSpacing(6)

        from PySide6.QtWidgets import QCheckBox, QPushButton, QHBoxLayout
        chk_all = QCheckBox("Selecionar tudo"); v.addWidget(chk_all)

        values = self._distinct_values(col)
        checks: List[QCheckBox] = []
        current = self._active_filters.get(col, set())
        for val in values:
            ck = QCheckBox(val)
            ck.setChecked(False if current else True)
            if current and val in current: ck.setChecked(True)
            v.addWidget(ck); checks.append(ck)

        def set_all(state: bool):
            for ck in checks: ck.setChecked(state)
        chk_all.toggled.connect(set_all)
        v.addSpacing(6)

        row_sort = QHBoxLayout()
        def add_btn(txt, fn):
            b = QPushButton(txt); b.setMinimumHeight(26); b.setProperty("accent", "true")
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
            b.clicked.connect(lambda: (fn(), menu.close())); row_sort.addWidget(b)

        if is_numeric:
            add_btn("0 → 9", lambda: self.table.sortItems(col, Qt.AscendingOrder))
            add_btn("9 → 0", lambda: self.table.sortItems(col, Qt.DescendingOrder))
        elif is_date:
            add_btn("Mais recente → mais antiga", lambda: self.table.sortItems(col, Qt.DescendingOrder))
            add_btn("Mais antiga → mais recente", lambda: self.table.sortItems(col, Qt.AscendingOrder))
        else:
            add_btn("A → Z", lambda: self.table.sortItems(col, Qt.AscendingOrder))
            add_btn("Z → A", lambda: self.table.sortItems(col, Qt.DescendingOrder))
        v.addLayout(row_sort)

        row_btn = QHBoxLayout()
        btn_apply = QPushButton("Aplicar"); btn_clear = QPushButton("Limpar")
        for b in (btn_apply, btn_clear):
            b.setMinimumHeight(26); b.setProperty("accent", "true")
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
        row_btn.addWidget(btn_apply); row_btn.addWidget(btn_clear); v.addLayout(row_btn)

        def apply_filters():
            selected = {ck.text() for ck in checks if ck.isChecked()}
            self._active_filters[col] = set() if (not values or len(selected)==len(values)) else selected
            self._apply_menu_filters()

        def clear_filters():
            self._active_filters[col] = set(); self._apply_menu_filters()

        btn_apply.clicked.connect(lambda: (apply_filters(), menu.close()))
        btn_clear.clicked.connect(lambda: (clear_filters(), menu.close()))

        act = QWidgetAction(menu); act.setDefaultWidget(container); menu.addAction(act)
        menu.exec(QCursor.pos())

    # ========= seleção =========
    def _selected_rows(self) -> List[Tuple[int, RepiqueRow]]:
        out: List[Tuple[int, RepiqueRow]] = []

        def vm_row_from_visual(vr: int) -> Tuple[int, RepiqueRow]:
            idx_item = self.table.item(vr, self.COL_CNPJ)
            vm_idx = idx_item.data(Qt.UserRole) if idx_item else None
            vm_idx = vr if vm_idx is None else int(vm_idx)
            return vm_idx, self.vm.rows[vm_idx]

        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r):  # respeita filtro
                continue
            wrap = self.table.cellWidget(r, self.COL_CHECK)
            chk = wrap.findChild(QCheckBox) if wrap else None
            if chk and chk.isChecked(): out.append(vm_row_from_visual(r))

        if not out and self.table.selectionModel():
            for idx in self.table.selectionModel().selectedRows():
                if not self.table.isRowHidden(idx.row()):
                    out.append(vm_row_from_visual(idx.row()))
        return out

    # ========= ações =========
    def _on_carregar_sql(self):
        Toast(self, "Carregando…").show_centered_in(self, 1200)
        self.vm.carregar_db(self.repo)      # apenas carrega (sem marcações)
        self._fill_table()
        self._analysis_start = datetime.now()   # inicia cronômetro total
        Toast(self, f"{len(self.vm.rows)} linha(s) carregadas.").show_centered_in(self, 2200)

    def _on_analise(self):
        # marca SOMENTE o que está visível e ≥ 50k
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r):
                continue
            it_val = self.table.item(r, self.COL_VALOR)
            if not it_val: continue
            try:
                v = float(it_val.text().replace(".", "").replace(",", "."))
            except: v = 0.0
            wrap = self.table.cellWidget(r, self.COL_CHECK)
            chk = wrap.findChild(QCheckBox) if wrap else None
            if chk:
                chk.setChecked(v >= self.vm.LIMITE)

        sel = self._selected_rows()
        if not sel:
            Toast(self, "Nada para analisar (nenhuma linha marcada).").show_centered_in(self, 2000)
            return

        # calculamos os agregados
        total = 0.0
        ge50k = 0
        for _, it in sel:
            total += float(it.valor or 0.0)
            if (it.valor or 0.0) >= self.vm.LIMITE:
                ge50k += 1
        self._last_selection_count = len(sel)
        self._last_selection_total = total
        self._last_selection_ge50k = ge50k

        # popup de revisão
        dlg = QDialog(self); dlg.setWindowTitle("Revisão das linhas selecionadas")
        layout = QVBox(dlg); layout.setContentsMargins(12,12,12,12); layout.setSpacing(8)

        tbl = QTable(0, 7, dlg)
        tbl.setHorizontalHeaderLabels(["Cliente", "CNPJ/CPF", "Tarifa", "Valor (R$)", "Data", "Segmento", "OBS"])
        tbl.verticalHeader().setVisible(False)
        tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        tbl.setEditTriggers(QAbstractItemView.AllEditTriggers)
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        for c in (1,2,3,4,5): hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)

        tbl.setRowCount(len(sel))
        for r, (vm_idx, it) in enumerate(sel):
            items = [
                QTableWidgetItem(it.cliente or ""),
                QTableWidgetItem(it.cnpj_cpf or ""),
                QTableWidgetItem(it.tarifa or ""),
                QTableWidgetItem(self._fmt_moeda(it.valor)),
                QTableWidgetItem(self._fmt_data(it.dt)),
                QTableWidgetItem(it.segmento or ""),
                QTableWidgetItem(self._obs_by_index.get(vm_idx, "")),
            ]
            for c in range(6): items[c].setFlags(items[c].flags() ^ Qt.ItemIsEditable)
            items[6].setData(Qt.UserRole, vm_idx)
            for c, w in enumerate(items): tbl.setItem(r, c, w)

        # Resumo analítico
        resumo = QLabel(
            f"<b>Selecionadas:</b> {self._last_selection_count} &nbsp; "
            f"<b>≥ R$ 50.000:</b> {self._last_selection_ge50k} &nbsp; "
            f"<b>Total:</b> R$ {self._fmt_moeda(self._last_selection_total)}"
        )
        layout.addWidget(resumo)

        layout.addWidget(tbl)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close, parent=dlg)
        layout.addWidget(btns)

        def save_obs():
            for r in range(tbl.rowCount()):
                obs_item = tbl.item(r, 6)
                vm_idx = int(obs_item.data(Qt.UserRole))
                self._obs_by_index[vm_idx] = obs_item.text()
                # reflete na grade principal
                for vr in range(self.table.rowCount()):
                    idx_item = self.table.item(vr, self.COL_CNPJ)
                    if idx_item and idx_item.data(Qt.UserRole) == vm_idx:
                        self.table.setItem(vr, self.COL_OBS, QTableWidgetItem(obs_item.text()))
                        break
            # registra histórico (parcial; duração será finalizada no envio do e-mail)
            filters = {col: sorted(list(vals)) for col, vals in self._active_filters.items() if vals}
            self._history.add_entry(
                self._current_user, datetime.now(), self._last_selection_count,
                filters, self._last_selection_total, self._last_selection_ge50k, self._analysis_start
            )
            Toast(self, "Observações salvas e histórico registrado.").show_centered_in(self, 1800)

        btns.accepted.connect(save_obs)
        btns.rejected.connect(dlg.close)
        dlg.resize(1200, 680); dlg.exec()

    def _on_historico(self):
        data = self._history.load()

        dlg = QDialog(self); dlg.setWindowTitle("Histórico de análises")
        lay = QVBox(dlg); lay.setContentsMargins(12,12,12,12); lay.setSpacing(8)

        info = QLabel(
            "Itens registrados ao clicar em <b>Salvar</b> no review. "
            "A duração total é finalizada ao <b>Enviar e-mail</b>."
        )
        info.setStyleSheet("color:#8B98A5;")
        lay.addWidget(info)

        tbl = QTable(0, 8, dlg)
        tbl.setHorizontalHeaderLabels([
            "Usuário","Início","Fim","Duração (s)","Qtde","≥ 50k","Total (R$)","Filtros"
        ])
        tbl.verticalHeader().setVisible(False)
        hdr = tbl.horizontalHeader()
        for c in range(7): hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.Stretch)

        tbl.setRowCount(len(data))
        for r, row in enumerate(data):
            total_fmt = f'{float(row.get("total_value",0)):,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            filt = row.get("filters", {})
            if filt:
                parts = []
                for k, vals in filt.items():
                    try: col_name = self.HEADERS[int(k)]
                    except: col_name = f"Col{k}"
                    parts.append(f"{col_name}: {', '.join(vals)}")
                filt_txt = " | ".join(parts)
            else:
                filt_txt = "-"

            tbl.setItem(r, 0, QTableWidgetItem(row.get("user","")))
            tbl.setItem(r, 1, QTableWidgetItem(row.get("started_at","") or row.get("when","")))
            tbl.setItem(r, 2, QTableWidgetItem(row.get("ended_at","") or "-"))
            tbl.setItem(r, 3, QTableWidgetItem(str(row.get("duration_secs","") or "-")))
            tbl.setItem(r, 4, QTableWidgetItem(str(row.get("count",0))))
            tbl.setItem(r, 5, QTableWidgetItem(str(row.get("count_ge50k",0))))
            tbl.setItem(r, 6, QTableWidgetItem(total_fmt))
            tbl.setItem(r, 7, QTableWidgetItem(filt_txt))

        lay.addWidget(tbl)

        # Ações: Reaplicar filtros e Exportar CSV
        btn_row = QHBoxLayout()
        btn_reapply = QPushButton("Reaplicar filtros do selecionado")
        btn_export  = QPushButton("Exportar CSV")
        for b in (btn_reapply, btn_export):
            b.setProperty("accent","true"); b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
        btn_row.addWidget(btn_reapply); btn_row.addStretch(); btn_row.addWidget(btn_export)
        lay.addLayout(btn_row)

        def reapply():
            r = tbl.currentRow()
            if r < 0: 
                Toast(dlg, "Selecione uma linha do histórico.").show_centered_in(dlg, 1600); 
                return
            data_item = self._history.load()[r]
            filt_map = {int(k): set(v) for k, v in data_item.get("filters",{}).items()}
            self._active_filters = filt_map
            self._apply_menu_filters()
            Toast(self, "Filtros reaplicados.").show_centered_in(self, 1600)

        def export_csv():
            path = str((Path(os.path.expanduser("~")) / "repique_history.csv").resolve())
            self._history.export_csv(path)
            Toast(self, f"CSV exportado em\n{path}").show_centered_in(self, 2200)

        btn_reapply.clicked.connect(reapply)
        btn_export.clicked.connect(export_csv)

        close = QDialogButtonBox(QDialogButtonBox.Close, parent=dlg)
        close.rejected.connect(dlg.close); close.accepted.connect(dlg.close)
        lay.addWidget(close)

        dlg.resize(980, 560); dlg.exec()

    def _on_enviar(self):
        selecionados = self._selected_rows()
        if not selecionados:
            Toast(self, "Nenhuma linha selecionada para envio.").show_centered_in(self, 2200)
            return

        subject = "Análise de Repique – Linhas acima de R$ 50.000,00"
        body_lines = ["Prezada gestora,", "", "Segue a relação de lançamentos para análise:"]
        for vm_idx, r in selecionados:
            obs = self._obs_by_index.get(vm_idx, "")
            body_lines.append(
                f"- Cliente: {r.cliente} | CNPJ/CPF: {r.cnpj_cpf} | Agência: {r.agencia} | Conta: {r.conta} | "
                f"Tarifa: {r.tarifa} | Data: {self._fmt_data(r.dt)} | Valor: R$ {self._fmt_moeda(r.valor)} | "
                f"Status: {r.desc_status or ''} | Segmento: {r.segmento or ''}" + (f" | OBS: {obs}" if obs else "")
            )
        body_lines.extend(("", "Atenciosamente,"))

        plain = "\r\n".join(body_lines)
        html  = "<br>".join(line if line else "&nbsp;" for line in body_lines)

        # Finaliza duração total da análise (desde Carregar até Enviar e-mail)
        if self._analysis_start:
            end = datetime.now()
            self._history.complete_last(end, int((end - self._analysis_start).total_seconds()))
            self._analysis_start = None

        try:
            import win32com.client as win32
            ol = win32.Dispatch("Outlook.Application")
            mail = ol.CreateItem(0)
            mail.To = ";".join(self._email_to)
            if self._email_cc: mail.CC = ";".join(self._email_cc)
            mail.Subject = subject
            mail.HTMLBody = f"<html><body>{html}</body></html>"
            mail.Display(True)
            Toast(self, "Abrindo e-mail…").show_centered_in(self, 2000)
            return
        except Exception:
            pass

        url = QUrl.fromUserInput(
            "mailto:" + quote(";".join(self._email_to))
            + "?subject=" + quote(subject, safe="")
            + ("&cc=" + quote(";".join(self._email_cc), safe="") if self._email_cc else "")
            + "&body=" + quote(plain, safe="", encoding="utf-8")
        )
        QDesktopServices.openUrl(url)
        Toast(self, "Abrindo e-mail…").show_centered_in(self, 2000)
