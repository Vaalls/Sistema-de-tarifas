from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
from app.ui.modules.dashboard.views.dashboard_webview import DashboardWebView

class DashboardView(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        self.web = DashboardWebView()
        self._build()

    def _gold(self, text, w=160, h=40):
        b = QPushButton(text)
        b.setProperty("accent", "true")
        b.setFixedSize(w, h)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
        return b

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setAlignment(Qt.AlignTop)

        top = QHBoxLayout()
        top.addStretch()
        bt_pdf = self._gold("Exportar PDF", 160, 40)
        bt_back = self._gold("Voltar ao menu", 160, 40)
        bt_back.clicked.connect(self.go_back.emit)
        bt_pdf.clicked.connect(self._export_pdf)
        top.addWidget(bt_pdf)
        top.addWidget(bt_back)
        root.addLayout(top)

        root.addWidget(self.web, stretch=1)

    def show_secure(self, url: str):
        self.web.load_secure_url(url)

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar dashboard em PDF", "dashboard.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            self.web.print_to_pdf(path)
            # A impressão é assíncrona; um toast/simples diálogo ajuda a indicar que foi enviado
            QMessageBox.information(self, "Exportar PDF", "Exportação enviada. Aguarde a geração do arquivo.")
        except Exception as e:
            QMessageBox.warning(self, "Exportar PDF", f"Falha ao exportar: {e}")
