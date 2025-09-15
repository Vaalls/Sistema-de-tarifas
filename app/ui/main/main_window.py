# ==============================================
# ui/main/main_window.py — Shell principal (MVVM)
# ==============================================
from __future__ import annotations
from typing import Optional
import os

from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QMessageBox

from app.core.i18n.i18n import I18n
from app.core.theme.theme import ThemeManager
from app.ui.components.toasts import Toast
from app.ui.main.sidebar import Sidebar
from app.ui.main.topbar import Topbar

# Home / Repique
from app.ui.modules.home.views.home_view import HomeView
from app.ui.modules.analise_repique.views.repique_view import RepiqueView
from app.core.data.repique_repository import RepiqueRepository
from app.core.data.sqlserver import get_engine

# Dashs
from app.ui.modules.dashboard.views.dashboard_menu_view import DashboardMenuView
from app.ui.modules.dashboard.views.dashboard_view import DashboardView

# Docs
from app.ui.modules.docs.views.docs_menu_view import DocsMenuView
from app.ui.modules.docs.views.document_viewer import DocumentViewer

# CGM (tela principal)
from app.ui.modules.cgm.views.cgm_view import CgmView

# Menus (primeiras telas de cada submenu)
from app.ui.modules.cgm.views.estorno.estorno_view import EstornoView
from app.ui.modules.cgm.views.pacote.pacote_view import PacoteView
from app.ui.modules.cgm.views.multas.multas_view import MultasView
from app.ui.modules.cgm.views.alcada.alcada_view import AlcadaView
from app.ui.modules.cgm.views.lar.lar_view import LarView

# Cadastros
from app.ui.modules.cgm.views.estorno.estorno_cadastro_view import EstornoCadastroView
from app.ui.modules.cgm.views.pacote.pacote_cadastro_view import PacoteCadastroView
from app.ui.modules.cgm.views.multas.multas_view_cadastro import MultasCadastroView
from app.ui.modules.cgm.views.alcada.alcada_cadastro_view import AlcadaCadastroView
from app.ui.modules.cgm.views.lar.lar_cadastro_view import LarCadastroView

# Consultas
from app.ui.modules.cgm.views.estorno.estorno_consulta_view import EstornoConsultaView
from app.ui.modules.cgm.views.pacote.pacote_consulta_view import PacoteConsultaView
from app.ui.modules.cgm.views.multas.multas_consulta_view import MultasConsultaView
from app.ui.modules.cgm.views.alcada.alcada_consulta_view import AlcadaConsultaView
from app.ui.modules.cgm.views.lar.lar_consulta_view import LarConsultaView


class MainWindow(QMainWindow):
    def __init__(self, theme: ThemeManager, i18n: I18n, repique_repo: Optional[RepiqueRepository] = None):
        super().__init__()
        self.theme = theme
        self.i18n = i18n
        self.setWindowTitle(self.i18n.tr("app.title"))
        self.resize(1200, 800)

                # --- Dashboards ---
        self.dashboard_menu_view = DashboardMenuView()
        self.dashboard_view = DashboardView()

                # ---- Dashboard module ----
        self._dash_meta = [
            {
                "key": "cgm_ops",
                "title": "CGM — Operações",
                "secure_url": "https://app.powerbi.com/reportEmbed?reportId=ef3dbca8-07d1-4029-9c6e-5767511babc1&autoAuth=true&ctid=11dbbfe2-89b8-4549-be10-cec364e59551",
                "restricted": False,
                "desc": "Visão 360 de volumes, pendências e SLAs no CGM."
            },
            {
                "key": "comercial",
                "title": "Performance Comercial",
                "secure_url": "https://app.powerbi.com/reportEmbed?reportId=GUID2&groupId=GUID_WORKSPACE&autoAuth=true&ctid=TENANT_GUID",
                "restricted": True,  # ⬅ “somente gestora”
                "desc": "Receita, evolução mensal, ranking de agências."
            },
            {
                "key": "cockpit",
                "title": "Operações Cockpit",
                "secure_url": "https://app.powerbi.com/reportEmbed?reportId=91423210-36e4-4d71-ae9b-f262e2799156&autoAuth=true&ctid=940a1fd6-e859-4fe8-974b-ec76448a2f39",
                "restricted": False,
                "desc": "Acompanhamento de operações feitas."
            },
        ]

        self.dashboard_menu_view.set_dashboards([
            {"key":"cockpit", "title":"Operações de Cockpit", "desc":"Acompanhamento de operações feitas."},
            {"key":"cgm_ops", "title":"CGM — Operações", "desc":"Visão 360 de volumes, pendências e SLAs no CGM."},
            {"key":"perf", "title":"Performance Comercial", "desc":"Receita, evolução mensal, ranking de agências.", "restricted": True},
            # ...adicione mais metadados aqui
        ])
        self.dashboard_menu_view.open_dashboard.connect(self._open_dashboard)  # seu handler existente

        self.docs_menu_view = DocsMenuView()
        self.document_viewer = DocumentViewer()

        # catálogo de documentos (exemplos)
        self.docs_menu_view.set_docs([
            {"key": "man_cgm", "title": "Manual do CGM", "path": r"C:\Users\Gabri\Downloads\dashboard.pdf"},
            {"key": "repique_dic", "title": "Dicionário de dados — Repique", "path": r"C:\docs\repique_dic.csv"},
            {"key": "tarifas_tabela", "title": "Tabela de Tarifas 2025", "path": r"C:\Users\Gabri\OneDrive\Área de Trabalho\Planilha_Financeira_2025.xlsx"}
        ])

        # conexões
        self.docs_menu_view.open_doc.connect(lambda meta: (self.document_viewer.open_document(meta),
                                                        self._goto(self.document_viewer, meta.get("title","Documento"))))
        self.document_viewer.go_back.connect(lambda: self._goto(self.docs_menu_view, "Documentação"))


        # Repo do Repique
        self.engine = get_engine()
        self.repique_repo = repique_repo or RepiqueRepository(self.engine)

        # ---------- layout principal ----------
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        self.setCentralWidget(central)

        # Sidebar
        self.sidebar = Sidebar(i18n)
        self.sidebar.setFixedWidth(220)
        root.addWidget(self.sidebar)
        self.sidebar_visible = True
        self.sidebar_locked = True
        self.dashboard_menu_view.open_dashboard.connect(self._open_dashboard)
        self.dashboard_view.go_back.connect(lambda: self._goto(self.dashboard_menu_view, "Dashboards"))

        # Conteúdo (Topbar + Stack)
        content = QVBoxLayout(); content.setSpacing(8)

        self.topbar = Topbar(i18n)
        content.addWidget(self.topbar)

        self.stack = QStackedWidget()
        content.addWidget(self.stack)

        self.topbar.set_menu_enabled(False)
        self.topbar.sidebar_toggle_requested.connect(self._toggle_sidebar)
        self.topbar.set_view_title(self.i18n.tr("menu.home"), show_menu=False)

        user = os.getenv("USERNAME") or os.getenv("USER") or ""
        self.topbar.set_user(user)

        self.stack.addWidget(self.dashboard_menu_view)
        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.docs_menu_view)
        self.stack.addWidget(self.document_viewer)

        root.addLayout(content)

        # ---------- Views ----------
        self.home_view = HomeView(i18n)
        self.repique_view = RepiqueView(i18n, repo=self.repique_repo)
        self.cgm_view = CgmView()

        # Menus
        self.estorno_view = EstornoView()
        self.pacote_view = PacoteView()
        self.multas_view = MultasView()
        self.alcada_view = AlcadaView()
        self.lar_view = LarView()

        # Cadastros
        self.estorno_cadastro_view = EstornoCadastroView()
        self.pacote_cadastro_view = PacoteCadastroView()
        self.multas_cadastro_view = MultasCadastroView()
        self.alcada_cadastro_view = AlcadaCadastroView()
        self.lar_cadastro_view = LarCadastroView()

        # Consultas
        self.estorno_consulta_view = EstornoConsultaView()
        self.pacote_consulta_view = PacoteConsultaView()
        self.multas_consulta_view = MultasConsultaView()
        self.alcada_consulta_view = AlcadaConsultaView()
        self.lar_consulta_view = LarConsultaView()

        # Empilha
        for w in [
            self.home_view, self.repique_view, self.cgm_view,
            self.estorno_view, self.pacote_view, self.multas_view, self.alcada_view, self.lar_view,
            self.estorno_cadastro_view, self.pacote_cadastro_view, self.multas_cadastro_view,
            self.alcada_cadastro_view, self.lar_cadastro_view,
            self.estorno_consulta_view, self.pacote_consulta_view, self.multas_consulta_view,
            self.alcada_consulta_view, self.lar_consulta_view
        ]:
            self.stack.addWidget(w)

        self.stack.setCurrentWidget(self.home_view)

        # ---------- Conexões ----------
        self.topbar.toggle_theme.connect(self.theme.toggle)
        self.sidebar.navigate.connect(self.on_navigate)
        self.home_view.new_repique.connect(self._go_repique)

        # CGM principal → submenus
        self.cgm_view.open_estorno.connect(lambda: self._goto(self.estorno_view, "Estorno"))
        self.cgm_view.open_pacote.connect(lambda: self._goto(self.pacote_view, "Pacote de Tarifas"))
        self.cgm_view.open_multas.connect(lambda: self._goto(self.multas_view, "Multas e Comissões"))
        self.cgm_view.open_alcada.connect(lambda: self._goto(self.alcada_view, "Negociação com Alçada"))
        self.cgm_view.open_lar.connect(lambda: self._goto(self.lar_view, "LAR"))

        # Menus → voltar ao CGM
        self.estorno_view.go_back.connect(self._go_cgm)
        self.pacote_view.go_back.connect(self._go_cgm)
        self.multas_view.go_back.connect(self._go_cgm)
        self.alcada_view.go_back.connect(self._go_cgm)
        self.lar_view.go_back.connect(self._go_cgm)

        # Menus → abrir cadastro/consulta
        self.estorno_view.open_cadastro.connect(lambda: self._goto(self.estorno_cadastro_view, "Estorno — Cadastro"))
        self.estorno_view.open_consulta.connect(lambda: self._goto(self.estorno_consulta_view, "Estorno — Consulta"))
        self.pacote_view.open_cadastro.connect(lambda: self._goto(self.pacote_cadastro_view, "Pacote de Tarifas — Cadastro"))
        self.pacote_view.open_consulta.connect(lambda: self._goto(self.pacote_consulta_view, "Pacote de Tarifas — Consulta"))
        self.multas_view.open_cadastro.connect(lambda: self._goto(self.multas_cadastro_view, "Multas e Comissões — Cadastro"))
        self.multas_view.open_consulta.connect(lambda: self._goto(self.multas_consulta_view, "Multas e Comissões — Consulta"))
        self.alcada_view.open_cadastro.connect(lambda: self._goto(self.alcada_cadastro_view, "Negociação com Alçada — Cadastro"))
        self.alcada_view.open_consulta.connect(lambda: self._goto(self.alcada_consulta_view, "Negociação com Alçada — Consulta"))
        self.lar_view.open_cadastro.connect(lambda: self._goto(self.lar_cadastro_view, "LAR — Cadastro"))
        self.lar_view.open_consulta.connect(lambda: self._goto(self.lar_consulta_view, "LAR — Consulta"))

        # “Visualizar” a partir da lista de últimos cadastros (prefill + navega)
        self.estorno_view.open_registro.connect(lambda f: self._prefill_and_go(self.estorno_consulta_view, "Estorno — Consulta", f))
        self.pacote_view.open_registro.connect(lambda f: self._prefill_and_go(self.pacote_consulta_view, "Pacote de Tarifas — Consulta", f))
        self.multas_view.open_registro.connect(lambda f: self._prefill_and_go(self.multas_consulta_view, "Multas e Comissões — Consulta", f))
        self.alcada_view.open_registro.connect(lambda f: self._prefill_and_go(self.alcada_consulta_view, "Negociação com Alçada — Consulta", f))
        self.lar_view.open_registro.connect(   lambda f: self._prefill_and_go(self.lar_consulta_view,    "LAR — Consulta", f))

        # Cadastros → sucesso/cancelar
        # ESTORNO
        self.estorno_cadastro_view.saved_view.connect(lambda d: self._after_estorno_saved(d, go_visual=True))
        self.estorno_cadastro_view.saved_close.connect(lambda d: self._after_estorno_saved(d, go_visual=False))
        self.estorno_cadastro_view.cancelled.connect(lambda: self._goto(self.estorno_view, "Estorno"))
        # PACOTE
        self.pacote_cadastro_view.saved_view.connect(lambda d: self._after_pacote_saved(d, go_visual=True))
        self.pacote_cadastro_view.saved_close.connect(lambda d: self._after_pacote_saved(d, go_visual=False))
        self.pacote_cadastro_view.cancelled.connect(lambda: self._goto(self.pacote_view, "Pacote de Tarifas"))
        # MULTAS
        self.multas_cadastro_view.saved_view.connect(lambda d: self._after_multas_saved(d, go_visual=True))
        self.multas_cadastro_view.saved_close.connect(lambda d: self._after_multas_saved(d, go_visual=False))
        self.multas_cadastro_view.cancelled.connect(lambda: self._goto(self.multas_view, "Multas e Comissões"))
        # ALCADA
        self.alcada_cadastro_view.saved_view.connect(lambda d: self._after_alcada_saved(d, go_visual=True))
        self.alcada_cadastro_view.saved_close.connect(lambda d: self._after_alcada_saved(d, go_visual=False))
        self.alcada_cadastro_view.cancelled.connect(lambda: self._goto(self.alcada_view, "Negociação com Alçada"))
        # LAR
        self.lar_cadastro_view.saved_view.connect(lambda d: self._after_lar_saved(d, go_visual=True))
        self.lar_cadastro_view.saved_close.connect(lambda d: self._after_lar_saved(d, go_visual=False))
        self.lar_cadastro_view.cancelled.connect(lambda: self._goto(self.lar_view, "LAR"))

        # Consultas → voltar
        self.estorno_consulta_view.go_back.connect(lambda: self._goto(self.estorno_view, "Estorno"))
        self.pacote_consulta_view.go_back.connect(lambda: self._goto(self.pacote_view, "Pacote de Tarifas"))
        self.multas_consulta_view.go_back.connect(lambda: self._goto(self.multas_view, "Multas e Comissões"))
        self.alcada_consulta_view.go_back.connect(lambda: self._goto(self.alcada_view, "Negociação com Alçada"))
        self.lar_consulta_view.go_back.connect(lambda: self._goto(self.lar_view, "LAR"))

        # atalhos
        self._setup_shortcuts()

    # -------- Navegação básica --------
    @Slot()
    def goto_home(self):
        self.stack.setCurrentWidget(self.home_view)

    def _goto(self, widget: QWidget, title: str):
        self.stack.setCurrentWidget(widget)
        self._set_sidebar(False, False)
        self.topbar.set_view_title(title, show_menu=True)

    def _go_cgm(self):
        self._goto(self.cgm_view, "Cadastro no CGM")

    def _toggle_sidebar(self):
        if self.sidebar_locked:
            return
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.setVisible(self.sidebar_visible)

    def _set_sidebar(self, visible: bool, locked: bool):
        self.sidebar_locked = locked
        self.sidebar_visible = visible
        self.sidebar.setVisible(visible)
        self.topbar.set_menu_enabled(not locked)

    def _go_repique(self):
        self._goto(self.repique_view, self.i18n.tr("menu.repique"))

    @Slot(str)
    def on_navigate(self, key: str):
        if key == "home":
            self.stack.setCurrentWidget(self.home_view)
            self._set_sidebar(True, True)
            self.topbar.set_view_title(self.i18n.tr("menu.home"), show_menu=False)
        elif key == "repique":
            self._go_repique()
        elif key == "cgm":
            self._go_cgm()
        elif key == "dashboard":
           self.dashboard_menu_view.reset_search()
           self._goto(self.dashboard_menu_view, "Dashboards")
        elif key == "docs":
            self.docs_menu_view.reset_search()
            self._goto(self.docs_menu_view, "Documentação")
        else:
            Toast(self, f"{key} — em breve").show_at(self.width() - 260, 80)
            self._set_sidebar(False, False)
            self.topbar.set_view_title(key.capitalize(), show_menu=True)

    def _setup_shortcuts(self):
        act_theme = QAction(self); act_theme.setShortcut(QKeySequence("Ctrl+Shift+L"))
        act_theme.triggered.connect(self.theme.toggle); self.addAction(act_theme)
        act_help = QAction(self); act_help.setShortcut(QKeySequence("F1"))
        act_help.triggered.connect(lambda: Toast(self, self.i18n.tr("help")).show_at(self.width()-220, 120))
        self.addAction(act_help)

    # ---------- helpers ----------
    def _prefill_and_go(self, consulta_view: QWidget, title: str, filtros: dict):
        try:
            # todas as consultas implementam prefill(**dict)
            consulta_view.prefill(filtros, autorun=True)
        except Exception:
            pass
        self._goto(consulta_view, title)

    # -------- Pós-cadastro → ir para consulta com filtros preenchidos --------
    def _after_estorno_saved(self, d: dict, go_visual: bool):
        if go_visual:
            try:
                self.estorno_consulta_view.prefill({
                    "Agência": d.get("Agencia","") or d.get("Agência",""),
                    "Conta":   d.get("Conta",""),
                    "Cliente": d.get("Nome_Cli",""),
                }, autorun=True)
            except Exception:
                pass
            self._goto(self.estorno_consulta_view, "Estorno — Consulta")
        else:
            self._goto(self.estorno_view, "Estorno")

    def _after_pacote_saved(self, d: dict, go_visual: bool):
        if go_visual:
            try:
                self.pacote_consulta_view.prefill({
                    "Segmento": d.get("Segmento",""),
                    "Cliente":  d.get("Cliente",""),
                    "CNPJ":     d.get("CNPJ",""),
                    "AG":       d.get("AG",""),
                }, autorun=True)
            except Exception:
                pass
            self._goto(self.pacote_consulta_view, "Pacote de Tarifas — Consulta")
        else:
            self._goto(self.pacote_view, "Pacote de Tarifas")

    def _after_multas_saved(self, d: dict, go_visual: bool):
        if go_visual:
            try:
                self.multas_consulta_view.prefill({
                    "Segmento": d.get("Segmento",""),
                    "Cliente":  d.get("Cliente",""),
                    "CNPJ":     d.get("CNPJ",""),
                }, autorun=True)
            except Exception:
                pass
            self._goto(self.multas_consulta_view, "Multas e Comissões — Consulta")
        else:
            self._goto(self.multas_view, "Multas e Comissões")

    def _after_alcada_saved(self, d: dict, go_visual: bool):
        if go_visual:
            try:
                self.alcada_consulta_view.prefill({
                    "Segmento": d.get("Segmento",""),
                    "CNPJ":     d.get("CNPJ",""),
                    "AG":       d.get("AG",""),
                    "Tarifa":   d.get("Tarifa",""),
                }, autorun=True)
            except Exception:
                pass
            self._goto(self.alcada_consulta_view, "Negociação com Alçada — Consulta")
        else:
            self._goto(self.alcada_view, "Negociação com Alçada")

    def _after_lar_saved(self, d: dict, go_visual: bool):
        if go_visual:
            try:
                self.lar_consulta_view.prefill({
                    "Segmento": d.get("Segmento",""),
                    "Cliente":  d.get("Cliente",""),
                    "CNPJ":     d.get("CNPJ",""),
                }, autorun=True)
            except Exception:
                pass
            self._goto(self.lar_consulta_view, "LAR — Consulta")
        else:
            self._goto(self.lar_view, "LAR")

        # --- Permissão: somente gestora ---

    def _is_gestora_user(self) -> bool:
        user = (os.getenv("USERNAME") or os.getenv("USER") or "").lower()
        allowed = {"gestora", "admin"}  # ou ler de .env/config
        return user in allowed

    def _open_dashboard(self, key: str):
        meta = next((m for m in self._dash_meta if m["key"] == key), None)
        if not meta: 
            Toast(self, "Dashboard indisponível").show_at(self.width()-260, 80)
            return
        if meta.get("restricted") and not self._is_gestora_user():
            QMessageBox.warning(self, "Acesso restrito", "Este dashboard é exclusivo para usuários da gestora.")
            return
        self.dashboard_view.show_secure(meta["secure_url"])
        self._goto(self.dashboard_view, meta["title"])
