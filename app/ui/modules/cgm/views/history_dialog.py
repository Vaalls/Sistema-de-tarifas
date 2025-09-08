from typing import List, Tuple
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox

class HistoryDialog(QDialog):
    def __init__(self, parent=None, title="Histórico", rows: List[Tuple[str,str,str]] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        rows = rows or []  # [(usuario, acao, datetime)]
        lay = QVBoxLayout(self); lay.setContentsMargins(12,12,12,12); lay.setSpacing(8)
        info = QLabel("Últimas ações registradas"); lay.addWidget(info)
        table = QTableWidget(0, 3); table.setHorizontalHeaderLabels(["Usuário","Ação","Data/Hora"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for u, a, d in rows:
            r = table.rowCount(); table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(u))
            table.setItem(r, 1, QTableWidgetItem(a))
            table.setItem(r, 2, QTableWidgetItem(d))
        lay.addWidget(table)
        btns = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        btns.rejected.connect(self.close); btns.accepted.connect(self.close)
        lay.addWidget(btns)
