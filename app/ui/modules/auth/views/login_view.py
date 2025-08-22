# ===============================================
# ui/modules/auth/views/login_view.py — Login UI
# ===============================================
from app.core.i18n.i18n import I18n
from app.ui.components.toasts import Toast
from app.ui.modules.auth.viewmodels.login_vm import LoginViewModel
from PySide6.QtCore import Qt, Signal, Slot, QEvent
from PySide6.QtWidgets import (
 QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,  QFrame,
)

class LoginView(QWidget):
    login_success = Signal()

    def __init__(self, i18n: I18n):
        super().__init__()
        self.i18n = i18n
        self.vm = LoginViewModel()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)

        card = QFrame(objectName="Surface")
        card.setMinimumWidth(420)
        lay = QVBoxLayout(card)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        title = QLabel(self.i18n.tr("app.title"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:600; background: transparent;")
        subtitle = QLabel(self.i18n.tr("login.title"))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:#8B98A5; background: transparent;")

        self.input_user = QLineEdit(placeholderText=self.i18n.tr("login.user"))
        self.input_pass = QLineEdit(placeholderText=self.i18n.tr("login.pass"))
        self.input_pass.setEchoMode(QLineEdit.Password)

        self.input_user.setFixedHeight(32)
        self.input_user.setFixedSize(300, 32)
        self.input_user.setAlignment(Qt.AlignCenter)
        self.input_pass.setFixedHeight(32)
        self.input_pass.setFixedSize(300, 32)
        self.input_pass.setAlignment(Qt.AlignCenter)
        
        self.btn_login = QPushButton(self.i18n.tr("login.button"))
        self.btn_login.clicked.connect(self.on_login)
        self.input_user.returnPressed.connect(self.on_login)
        self.input_pass.returnPressed.connect(self.on_login)
        self.btn_login.setFixedHeight(36)
        self.btn_login.setFixedSize(300, 36)
        self.btn_login.setStyleSheet("font-weight: 600;")
        self.btn_login.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
        self.btn_login.setCursor(Qt.PointingHandCursor)

        lay.addWidget(title, alignment=Qt.AlignCenter)
        lay.addWidget(subtitle, alignment=Qt.AlignCenter)
        lay.addSpacing(6)
        lay.addWidget(self.input_user, alignment=Qt.AlignCenter)
        lay.addWidget(self.input_pass, alignment=Qt.AlignCenter)
        lay.addWidget(self.btn_login, alignment=Qt.AlignCenter)


        root.addWidget(card)
        # Acessibilidade / atalhos
        self.input_user.setFocus()
        self.input_user.installEventFilter(self)


    def eventFilter(self, obj, ev):
        if obj is self.input_user and ev.type() == QEvent.KeyPress:
            if ev.key() == Qt.Key_L and ev.modifiers() & Qt.ControlModifier:
                self.input_user.setFocus(); return True
        return super().eventFilter(obj, ev)


    @Slot()
    def on_login(self):
        self.vm.user = self.input_user.text()
        self.vm.password = self.input_pass.text()
        if self.vm.validate():
            self.login_success.emit()
        else:
            Toast(self, self.i18n.tr("toast.error.credentials")).show_centered_in(self, duration_ms=2500)