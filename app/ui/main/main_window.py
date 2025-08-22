# ==============================================
# ui/main/main_window.py — Shell principal (MVVM)
# ==============================================
from app.core.i18n.i18n import I18n
from app.core.theme.theme import ThemeManager
from app.ui.components.toasts import Toast
from app.ui.main.sidebar import Sidebar
from app.ui.main.topbar import Topbar
from app.ui.modules.analise_repique.views.repique_view import RepiqueView
from app.ui.modules.home.views.home_view import HomeView
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
 QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
 QStackedWidget
)
from app.ui.modules.cgm.views.cgm_view import CgmView
from app.core.data.repique_repository import RepiqueRepository
from app.core.data.sqlserver import get_engine
import os

class MainWindow(QMainWindow):

    def __init__(self, theme: ThemeManager, i18n: I18n):
        super().__init__()
        self.theme = theme
        self.i18n = i18n
        self.setWindowTitle(self.i18n.tr("app.title"))
        self.resize(1200, 800)
        self.engine = get_engine()
        self.repique_repo = RepiqueRepository(self.engine)

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
        

        # Conteúdo (Topbar + Stack)
        content = QVBoxLayout(); content.setSpacing(8)
        self.topbar = Topbar(i18n)
        content.addWidget(self.topbar)
        self.stack = QStackedWidget()
        content.addWidget(self.stack)
        self.topbar.set_menu_enabled(False)  # Desabilita menu até sidebar carregar
        self.topbar.sidebar_toggle_requested.connect(self._toggle_sidebar)
        self.topbar.set_view_title(self.i18n.tr("menu.home"), show_menu=False)
        user = os.getenv("USERNAME") or os.getenv("USER") or ""
        self.topbar.set_user(user)
        root.addLayout(content)

        self.engine = get_engine()
        self.repique_repo = RepiqueRepository(self.engine)

        # Views
        self.home_view = HomeView(i18n)
        self.repique_view = RepiqueView(i18n, repo=self.repique_repo)  # Placeholder for future views
        self.cgm_view = CgmView()
        self.stack.addWidget(self.home_view)
        self.stack.addWidget(self.repique_view)
        self.stack.addWidget(self.cgm_view)
        self.stack.setCurrentWidget(self.home_view)

        # Conexões
        self.topbar.toggle_theme.connect(self.theme.toggle)
        self.sidebar.navigate.connect(self.on_navigate)
        self.home_view.new_repique.connect(self._go_repique)
        self.cgm_view.open_cadastro.connect(self._open_cgm_form)

        # Atalhos globais
        self._setup_shortcuts()

    @Slot()
    def goto_home(self):
        self.stack.setCurrentWidget(self.home_view)

    @Slot()
    def toggle_language(self):
        self.i18n.toggle()
        # Recriar views com novo idioma (simples para v0)
        cur = self.stack.currentWidget()
        self.stack.removeWidget(self.home_view)
        self.home_view.deleteLater()
        self.home_view = HomeView(self.i18n)
        self.stack.addWidget(self.home_view)

        # recria Topbar/Sidebar para aplicar idioma
        self.topbar.deleteLater(); self.topbar = Topbar(self.i18n)
        self.centralWidget().layout().itemAt(1).layout().insertWidget(0, self.topbar)
        self.topbar.toggle_theme.connect(self.theme.toggle)
        self.stack.setCurrentWidget(self.home_view)

        self.sidebar.deleteLater(); self.sidebar = Sidebar(self.i18n)
        self.centralWidget().layout().insertWidget(0, self.sidebar)
        self.sidebar.navigate.connect(self.on_navigate)

        self.setWindowTitle(self.i18n.tr("app.title"))

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
        self.stack.setCurrentWidget(self.repique_view)
        self._set_sidebar(False, False)
        self.topbar.set_view_title(self.i18n.tr("menu.repique"), show_menu=True)    
        
    @Slot(str)
    def on_navigate(self, key: str):
        if key == "home":
            self.stack.setCurrentWidget(self.home_view)
            self._set_sidebar(True, True)
            self.topbar.set_view_title(self.i18n.tr("menu.home"), show_menu=False)   
        elif key == "repique":
            self.stack.setCurrentWidget(self.repique_view)
            self._set_sidebar(False, False)
            self.topbar.set_view_title(self.i18n.tr("menu.repique"), show_menu=True)
        elif key == "cgm":
            self.stack.setCurrentWidget(self.cgm_view)
            self._set_sidebar(False, False)
            self.topbar.set_view_title("Cadastro no CGM", show_menu=True)
        else:
            Toast(self, f"{key} — em breve").show_at(self.width() - 260, 80)
            self._set_sidebar(False, False)
            self.topbar.set_view_title(key.capitalize(), show_menu=True)

    def _setup_shortcuts(self):
        # Ctrl+Shift+L = tema
        act_theme = QAction(self); act_theme.setShortcut(QKeySequence("Ctrl+Shift+L"))
        act_theme.triggered.connect(self.theme.toggle)
        self.addAction(act_theme)
        # F1 = ajuda
        act_help = QAction(self); act_help.setShortcut(QKeySequence("F1"))
        act_help.triggered.connect(lambda: Toast(self, self.i18n.tr("help")).show_at(self.width()-220, 120))
        self.addAction(act_help)

    def _open_cgm_form(self, cadastro_id: str):
        # TODO: decidir para qual formulário ir baseado no prefixo/registro
        Toast(self, f"Abrindo formulário do cadastro {cadastro_id}").show_at(self.width()-260, 80)
        # Ex.: if cadastro_id.startswith("CGM-"):
        #          self.stack.setCurrentWidget(self.cgm_estorno_view) ...

    