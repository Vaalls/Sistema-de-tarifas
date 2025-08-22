from PySide6.QtWidgets import QDialog, QVBoxLayout
from app.core.i18n.i18n import I18n
from app.core.theme.theme import ThemeManager
from app.ui.modules.auth.views.login_view import LoginView

class LoginWindow(QDialog):
    def __init__(self, theme: ThemeManager, i18n: I18n):
        super().__init__()
        self.theme = theme
        self.i18n = i18n
        self.setWindowTitle(self.i18n.tr("app.title") + " — Login")
        self.setModal(True)
        self.setMinimumWidth(560)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        self.view = LoginView(self.i18n)
        lay.addWidget(self.view)
        self.view.login_success.connect(self.accept)
        self.view.btn_login.setDefault(True)
        self.view.btn_login.setAutoDefault(True)

