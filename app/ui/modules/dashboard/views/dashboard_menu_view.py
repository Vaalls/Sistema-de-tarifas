# app/ui/modules/dashboard/views/dashboard_menu_view.py
from __future__ import annotations
from typing import List, Dict
import unicodedata

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)

CARD_W = 280

def _norm(s: str) -> str:
    s = (s or "").lower()
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")

class DashboardMenuView(QWidget):
    open_dashboard = Signal(str)

    def __init__(self):
        super().__init__()
        self._meta: List[Dict] = []
        self._cards: List[QFrame] = []
        self._grid_cols = 3
        self.grid = None
        self.search = None
        self._placeholder = QLabel("Nenhum dashboard configurado.")
        self._build()

    def _gold(self, text, w=96, h=28):
        b = QPushButton(text); b.setProperty("accent","true")
        b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
        return b

    def _card(self, meta: Dict) -> QFrame:
        card = QFrame(objectName="Surface", parent=self)
        card.setMaximumWidth(CARD_W)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        lay = QVBoxLayout(card); lay.setContentsMargins(12,12,12,12); lay.setSpacing(6)
        title = QLabel(meta.get("title","")); title.setStyleSheet("font-weight:700; font-size:14px; background:transparent;")
        desc  = QLabel(meta.get("desc",""));  desc.setWordWrap(True)
        desc.setStyleSheet("color:#8B98A5; background:transparent; font-size:12px;"); desc.setMaximumHeight(36)

        bottom = QHBoxLayout()
        if meta.get("restricted"):
            badge = QLabel("Somente gestora")
            badge.setStyleSheet("background:#1e2630; color:#ffcc66; padding:2px 8px; border-radius:6px; font-size:12px;")
            bottom.addWidget(badge)
        bottom.addStretch()
        bt = self._gold("Abrir")
        bt.clicked.connect(lambda _=None, k=meta["key"]: self.open_dashboard.emit(k))
        bottom.addWidget(bt)

        lay.addWidget(title); lay.addWidget(desc); lay.addLayout(bottom)
        return card

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setAlignment(Qt.AlignTop)

        top = QHBoxLayout()
        self.search = QLineEdit(placeholderText="Pesquisar dashboards…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self._refilter)
        top.addWidget(self.search, 0, Qt.AlignLeft); top.addStretch()
        root.addLayout(top)

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        inner = QWidget(); self.grid = QGridLayout(inner)
        self.grid.setHorizontalSpacing(12); self.grid.setVerticalSpacing(12)
        self._scroll.setWidget(inner)
        root.addWidget(self._scroll, stretch=1)

        self._placeholder.setStyleSheet("color:#8B98A5;"); self._placeholder.setAlignment(Qt.AlignHCenter)
        root.addWidget(self._placeholder); self._placeholder.hide()

    # -------- API --------
    def set_dashboards(self, meta: List[Dict]):
        self._meta = [{**m, "_title_n": _norm(m.get("title","")), "_desc_n": _norm(m.get("desc",""))} for m in (meta or [])]

        for c in self._cards: c.setParent(None)
        self._cards = [self._card(m) for m in self._meta]
        self._placeholder.setVisible(len(self._cards)==0)

        self._relayout()
        # Defer para o próximo ciclo do event loop → garante 1º paint OK
        QTimer.singleShot(0, self._refilter)

    def reset_search(self):
        if self.search and self.search.text():
            self.search.clear()

    # -------- filtro & layout --------
    def _refilter(self):
        q_raw = (self.search.text() if self.search else "") or ""
        q = _norm(q_raw)

        self.setUpdatesEnabled(False)
        for i, m in enumerate(self._meta):
            if not q:
                show = True
            elif len(q) == 1:
                show = m["_title_n"].startswith(q)
            else:
                show = (q in m["_title_n"]) or (q in m["_desc_n"])
            self._cards[i].setVisible(show)
        self._relayout()
        self.setUpdatesEnabled(True)

    def showEvent(self, ev):
        super().showEvent(ev)
        # quando entra na tela pela 1ª vez, força refilter após layout
        QTimer.singleShot(0, self._refilter)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        w = self.width()
        cols = 5 if w >= 1500 else 4 if w >= 1200 else 3 if w >= 980 else 2 if w >= 680 else 1
        if cols != self._grid_cols:
            self._grid_cols = cols
            self._relayout()

    def _relayout(self):
        if not self.grid: return
        while self.grid.count(): self.grid.takeAt(0)
        for c in range(max(1, self._grid_cols)): self.grid.setColumnStretch(c, 1)

        j = 0
        for w in self._cards:
            if not w.isVisible(): continue
            r, col = divmod(j, self._grid_cols)
            self.grid.addWidget(w, r, col, Qt.AlignTop)
            j += 1
