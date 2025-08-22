from PySide6.QtCore import  QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
     QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QAbstractItemView,
     QDialog, QVBoxLayout as QVBox, QListWidget, QDialogButtonBox
)
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QProgressDialog   
from urllib.parse import quote
from app.core.data.repique_repository import RepiqueRepository
from app.core.i18n.i18n import I18n
from app.ui.components.toasts import Toast
from PySide6.QtCore import Qt
from app.ui.modules.analise_repique.viewmodels.repique_vm import RepiqueViewModel, RepiqueRow

class RepiqueView(QWidget):
    def __init__(self, i18n: I18n, repo: RepiqueRepository):
        super().__init__()
        self.i18n = i18n
        self.vm = RepiqueViewModel()
        self.repo = repo
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(10)

        self.setStyleSheet("background-color: #0B2A4A;")

        # Ações
        actions = QHBoxLayout(); actions.setSpacing(8)
        self.btn_carregar = QPushButton("Carregar linhas")
        self.btn_enviar = QPushButton("Enviar e-mail")
        self.btn_analise = QPushButton("Análise")
        self.btn_analise.setProperty("accent", True)
        self.btn_analise.style().unpolish(self.btn_analise); self.btn_analise.style().polish(self.btn_analise)

        actions.addWidget(self.btn_carregar)
        actions.addWidget(self.btn_enviar)
        actions.addWidget(self.btn_analise)
        actions.addStretch()

        # Tabela
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Enviar", "Cliente", "Conta", "Valor (R$)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)


        root.addLayout(actions)
        root.addWidget(self.table)

        # Conexões
        self.btn_carregar.clicked.connect(self._on_carregar_sql)
        self.btn_analise.clicked.connect(self._on_analise)
        self.btn_enviar.clicked.connect(self._on_enviar)

    def _on_carregar_sql(self):
        dlg = QProgressDialog("Carregando do SQL...", None, 0, 0, self)
        dlg.setWindowModality(Qt.WindowModal); dlg.setCancelButton(None); dlg.setMinimumDuration(0)
        dlg.show(); QApplication.processEvents()
        try:
            self.vm.carregar_db(self.repo)
            self._fill_table()
        finally:
            dlg.close()
        self._show_loaded_popup()


    def _show_loaded_popup(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Linhas carregadas com sucesso")
        layout = QVBox(dlg); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(8)
        info = QLabel(f"{len(self.vm.rows)} linha(s) carregadas.")
        layout.addWidget(info)
        lista = QListWidget()
        # lista cada linha carregada: Cliente | Conta | Valor
        for r in self.vm.rows:
            lista.addItem(f"{r.cliente} | {r.conta} | R$ {r.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        layout.addWidget(lista)
        btns = QDialogButtonBox(QDialogButtonBox.Ok, parent=dlg)
        btns.accepted.connect(dlg.accept)
        layout.addWidget(btns)
        dlg.resize(560, 420)
        dlg.exec()

    def _fill_table(self):
        self.table.setRowCount(len(self.vm.rows))
        for r, row in enumerate(self.vm.rows):
                # checkbox "Enviar"
                chk = QTableWidgetItem()
                chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Checked if row.valor >= self.vm.LIMITE else Qt.Unchecked)
                self.table.setItem(r, 0, chk)
                # dados
                self.table.setItem(r, 1, QTableWidgetItem(row.cliente))
                self.table.setItem(r, 2, QTableWidgetItem(row.conta))
                self.table.setItem(r, 3, QTableWidgetItem(
                    f"{row.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                ))

    def _on_enviar(self):
        selecionados: list[RepiqueRow] = []
        for r in range(self.table.rowCount()):
            chk = self.table.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                try:
                    valor_txt = self.table.item(r, 3).text().replace(".", "").replace(",", ".")
                    valor = float(valor_txt)
                except:
                    valor = 0.0
                selecionados.append(RepiqueRow(
                    self.table.item(r, 1).text(),
                    self.table.item(r, 2).text(),
                    valor
                ))
        # 2) se nenhuma marcada, usa seleção visual (fallback)
        if not selecionados:
            for idx in self.table.selectionModel().selectedRows():
                r = idx.row()
                try:
                    valor_txt = self.table.item(r, 3).text().replace(".", "").replace(",", ".")
                    valor = float(valor_txt)
                except:
                    valor = 0.0
                selecionados.append(RepiqueRow(
                    self.table.item(r, 1).text(),
                    self.table.item(r, 2).text(),
                    valor
                ))
        # 3) se ainda vazio, usa ≥ limite
        if not selecionados:
            selecionados = self.vm.selecionar_acima_limite()
        
        dlg = QProgressDialog("Preparando e-mail...", None, 0, 0, self)
        dlg.setWindowModality(Qt.WindowModal); dlg.setCancelButton(None); dlg.setMinimumDuration(0)
        dlg.show(); QApplication.processEvents()

        linhas = []
        for r in selecionados:
            linhas.append(f"Cliente: {r.cliente} | Conta: {r.conta} | Valor: R$ {r.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        subject = "Análise de Repique - Linhas acima de R$ 50.000,00"
        body = "Prezada gestora,%0D%0A%0D%0A" + "%0D%0A".join(quote(l) for l in linhas) + "%0D%0A%0D%0AAtenciosamente,"
        url = QUrl(f"mailto:?subject={quote(subject)}&body={body}")
        QDesktopServices.openUrl(url)
        Toast(self, "Abrindo e-mail...").show_centered_in(self, duration_ms=2500)
    
    def _on_analise(self):
        dlg = QProgressDialog("Analisando linhas...", None, 0, 0, self)
        dlg.setWindowModality(Qt.WindowModal); dlg.setCancelButton(None); dlg.setMinimumDuration(0)
        dlg.show(); QApplication.processEvents()
        self.table.clearSelection()
        hits = 0
        for r in range(self.table.rowCount()):
            try:
                valor_txt = self.table.item(r, 3).text().replace(".", "").replace(",", ".")
                valor = float(valor_txt)
            except Exception:
                valor = 0.0
            if valor >= self.vm.LIMITE:
                self.table.item(r, 0).setCheckState(Qt.Checked)
                self.table.selectRow(r)
                hits += 1
            else:
                self.table.item(r, 0).setCheckState(Qt.Unchecked)
        dlg.close()
        msg = f"Análise concluída: {hits} linha(s) ≥ R$ 50.000,00"
        Toast(self, msg).show_centered_in(self, duration_ms=2500)

