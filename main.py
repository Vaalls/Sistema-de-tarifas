# ==============
# main.py — run
# ==============
import sys

from PySide6.QtWidgets import QApplication, QDialog

from app.core.i18n.i18n import I18n
from app.core.theme.theme import ThemeManager
from app.core.data.repique_repository import RepiqueRepository
from app.ui.modules.auth.windows.login_window import LoginWindow
from app.ui.main.main_window import MainWindow
from PySide6.QtCore import Qt, QCoreApplication


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Tema e i18n
    theme = ThemeManager(app)
    theme.apply(ThemeManager.DARK)
    i18n = I18n()
    QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)

    # Tela de login (modal)
    login = LoginWindow(theme, i18n)
    if login.exec() == QDialog.Accepted:
        # Repositório MOCK (sem SQL) para a tela de Análise de Repique
        repique_repo = RepiqueRepository(engine=None, use_mock=True)

        # Tente passar o repo pela assinatura (se a MainWindow aceitar)
        try:
            win = MainWindow(theme, i18n, repique_repo=repique_repo)
        except TypeError:
            # Fallback: versões antigas da MainWindow sem parâmetro repique_repo
            win = MainWindow(theme, i18n)
            # Se existir um setter/atributo, injeta o repo
            if hasattr(win, "set_repique_repo"):
                win.set_repique_repo(repique_repo)
            elif hasattr(win, "repique_repo"):
                setattr(win, "repique_repo", repique_repo)

        win.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
