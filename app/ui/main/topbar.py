# ===============================
# ui/main/topbar.py — Topbar
# ===============================
from PySide6.QtCore import Signal
from app.core.i18n.i18n import I18n
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QToolButton, QStyle
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtWidgets import QSizePolicy

class Topbar(QFrame):
    toggle_theme = Signal()
    help_requested = Signal()
    sidebar_toggle_requested = Signal() 

    def __init__(self, i18n: I18n):
        super().__init__(objectName="Surface")
        self.i18n = i18n
        lay = QHBoxLayout(self); lay.setContentsMargins(12,8,12,8); lay.setSpacing(8)
        
        #Esquerda
        self.btn_menu = QToolButton(); self.btn_menu.setText("☰")
        lay.addWidget(self.btn_menu)
        title = QLabel(self.i18n.tr("app.title"))
        title.setStyleSheet("font-size:16px; font-weight:600; background:transparent;")
        lay.addWidget(title)

        #Centro
        lay.addStretch()
        self.view_title = QLabel("")
        self.view_title.setAlignment(Qt.AlignCenter)
        self.view_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.view_title.setStyleSheet("font-size:16px; font-weight:600; background:transparent;")
        lay.addWidget(self.view_title)
        lay.addStretch()

        # Right actions
        btn_help = QToolButton(); btn_help.setText("?")
        btn_notif = QToolButton(); btn_notif.setText("🔔")
        btn_theme = QToolButton(); btn_theme.setText("🌗")
        btn_lang = QToolButton(); btn_lang.setText("PT/EN")
        btn_user = QToolButton(); btn_user.setText("👤")
        for b in (btn_help, btn_notif, btn_theme, btn_user):
            lay.addWidget(b)

        self.info = QLabel("") #Bom dia, usuario - 20/08/2025 14:32
        self.info.setStyleSheet("color: #8B98A5; background: transparent;")
        lay.addWidget(self.info)

        self.username = ""
        self._clock = QTimer(self); 
        self._clock.timeout.connect(self._update_clock)
        self._update_clock()
        self._clock.start(60_000)  # Atualiza a cada minuto

        for b in (btn_help, btn_notif, btn_theme, btn_lang, btn_user):
            b.setCursor(Qt.PointingHandCursor)
        

        # Connect
        btn_theme.clicked.connect(self.toggle_theme.emit)
        btn_help.clicked.connect(self.help_requested.emit)
        self.btn_menu.clicked.connect(self.sidebar_toggle_requested.emit)

    def set_menu_enabled(self, enabled: bool):
        self.btn_menu.setEnabled(enabled)

    def set_view_title(self, text: str, show_menu: bool = True):
        self.view_title.setText(text or "")
        self.view_title.setVisible(show_menu)
    
    def set_user(self, username: str):
        self._username = username or ""
        self._update_clock()
    
    def _update_clock(self):
        now = QDateTime.currentDateTime()
        h = now.time().hour()
        greet = "Bom dia" if 5 <= 12 else ("Boa tarde" if 12 <= h < 18 else "Boa noite")
        user = getattr(self, '_username', "")
        self.info.setText(f"{greet}, {user} - {now.toString('dd/MM/yyyy HH:mm')}")