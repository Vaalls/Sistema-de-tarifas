from __future__ import annotations
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget, QVBoxLayout

class DashboardWebView(QWidget):
    def __init__(self):
        super().__init__()

        # Mantém a sessão (cookies) para o login do Power BI
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)

        self.web = QWebEngineView(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.web)

    def load_secure_url(self, url: str):
        self.web.load(QUrl(url))

    def print_to_pdf(self, file_path: str):
        # Qt 6 – assíncrono; salva direto no caminho
        self.web.page().printToPdf(file_path)
