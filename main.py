# ==============
# main.py — run
# ==============
import sys
from app.core.i18n.i18n import I18n
from app.core.theme.theme import ThemeManager
from app.ui.main.main_window import MainWindow
import sys
from PySide6.QtWidgets import (
QApplication
)
from PySide6.QtWidgets import QDialog
from app.ui.modules.auth.windows.login_window import LoginWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    theme = ThemeManager(app); theme.apply(ThemeManager.DARK)
    i18n = I18n()
    login = LoginWindow(theme, i18n)
    if login.exec() == QDialog.Accepted:

        win = MainWindow(theme, i18n)
        win.show()
        sys.exit(app.exec())
    else:
        sys.exit(0) 