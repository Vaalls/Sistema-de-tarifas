from __future__ import annotations
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog, QLineEdit, QMessageBox
)

GOLD_HOVER = "QPushButton:hover{background:#C49A2E;}"

def _btn(text: str, accent: bool = True) -> QPushButton:
    b = QPushButton(text)
    if accent:
        b.setProperty("accent", "true")
    b.setMinimumHeight(36)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(GOLD_HOVER)
    return b


class MassImportDialog(QDialog):
    """
    Popup simples para importação em massa.
    - Mostra somente a ORDEM DAS COLUNAS (destacada)
    - Aceita .csv, .xlsx, .xls
    - Sem preview nem 'ver/salvar modelo'
    - Dicas no rodapé
    Após 'Importar', se houver arquivo selecionado, o diálogo retorna Accepted
    e o caminho fica em `self.file_path`.
    """
    def __init__(self, titulo: str, columns_in_order: List[str], parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"Carregar em massa — {titulo}")
        self.file_path: Optional[str] = None
        self.columns = columns_in_order
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(14, 14, 14, 14)

        # Cabeçalho
        h = QHBoxLayout()
        t = QLabel("Importação em massa"); 
        t.setStyleSheet("font-size:16px; font-weight:600; background:transparent;")
        h.addWidget(t, 1, Qt.AlignLeft)
        root.addLayout(h)

        # Bloco: Ordem das colunas (destacado)
        card = QFrame(objectName="Surface")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        lbl = QLabel("Ordem das colunas (da esquerda para a direita)")
        lbl.setStyleSheet("color:#8B98A5; background:transparent;")

        col_label = QLabel("  - " + "\n  • ".join(self.columns))
        col_label.setWordWrap(True)
        col_label.setStyleSheet("font-family: 'Cascadia Mono', 'Consolas', monospace; background:transparent;")

        lay.addWidget(lbl)
        lay.addWidget(col_label)
        root.addWidget(card)

        # Seletor de arquivo
        pick = QHBoxLayout()
        self.ed_file = QLineEdit()
        self.ed_file.setPlaceholderText("Selecione um arquivo .csv, .xlsx ou .xls")
        self.ed_file.setReadOnly(True)
        bt_browse = _btn("Selecionar arquivo", accent=True)
        bt_browse.clicked.connect(self._choose_file)
        pick.addWidget(self.ed_file, 1)
        pick.addWidget(bt_browse, 0)
        root.addLayout(pick)

        # Dicas no rodapé
        tips = QLabel(
            "Dicas:\n"
            "• Aceita CSV (separado por vírgula ou ponto-e-vírgula) e Excel (.xlsx/.xls).\n"
            "• Utilize a ordem acima. Cabeçalhos são opcionais — a ordem prevalece.\n"
            "• Datas no formato dd/MM/yyyy. Valores numéricos no padrão decimal.\n"
            "• A validação/carga efetiva acontecerá no backend."
        )
        tips.setStyleSheet("color:#8B98A5; background:transparent;")
        tips.setWordWrap(True)
        root.addWidget(tips)

        # Ações
        actions = QHBoxLayout()
        actions.addStretch()
        bt_cancel = _btn("Cancelar", accent=False)
        bt_import = _btn("Importar", accent=True)
        actions.addWidget(bt_cancel)
        actions.addWidget(bt_import)
        root.addLayout(actions)

        bt_cancel.clicked.connect(self.reject)
        bt_import.clicked.connect(self._try_accept)

        # Tamanho padrão
        self.resize(720, 420)

    def _choose_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o arquivo",
            "",
            "Planilhas (*.xlsx *.xls);;Arquivos CSV (*.csv);;Todos (*.*)"
        )
        if file:
            self.file_path = file
            self.ed_file.setText(file)

    def _try_accept(self):
        if not self.file_path:
            QMessageBox.warning(self, "Arquivo não selecionado", "Escolha um arquivo para importar.")
            return
        self.accept()
