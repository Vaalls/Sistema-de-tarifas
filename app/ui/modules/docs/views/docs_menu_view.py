# app/ui/modules/docs/views/docs_menu_view.py
from __future__ import annotations
from typing import List, Dict
import unicodedata, os

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)

def _norm(s:str)->str:
    s=(s or "").lower()
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch)!="Mn")

class DocsMenuView(QWidget):
    open_doc = Signal(dict)  # emite o metadado completo: {"key","title","path",...}

    def __init__(self):
        super().__init__()
        self._meta: List[Dict] = []
        self._cards: List[QFrame] = []
        self._grid_cols = 3
        self.grid = None
        self.search = None
        self._build()

    def _gold(self, text, w=96, h=28):
        b = QPushButton(text); b.setProperty("accent","true")
        b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
        return b

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(12); root.setAlignment(Qt.AlignTop)

        top = QHBoxLayout()
        self.search = QLineEdit(placeholderText="Pesquisar documentos…")
        self.search.setClearButtonEnabled(True); self.search.setFixedWidth(300)
        self.search.textChanged.connect(self._refilter)
        top.addWidget(self.search, 0, Qt.AlignLeft); top.addStretch()
        root.addLayout(top)

        sa = QScrollArea(); sa.setWidgetResizable(True)
        inner = QWidget(); self.grid = QGridLayout(inner)
        self.grid.setHorizontalSpacing(12); self.grid.setVerticalSpacing(12)
        sa.setWidget(inner)
        root.addWidget(sa, stretch=1)

    # API
    def set_docs(self, meta: List[Dict]):
        self._meta = [{**m, "_n": _norm(m.get("title","")+" "+m.get("path",""))} for m in (meta or [])]
        for c in self._cards: c.setParent(None)
        self._cards = [self._card(m) for m in self._meta]
        self._relayout()
        QTimer.singleShot(0, self._refilter)

    def reset_search(self):
        if self.search and self.search.text():
            self.search.clear()

    # filtro & layout
    def _refilter(self):
        q = _norm(self.search.text() or "")
        self.setUpdatesEnabled(False)
        for i,m in enumerate(self._meta):
            show = True if not q else q in m["_n"]
            self._cards[i].setVisible(show)
        self._relayout()
        self.setUpdatesEnabled(True)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        w = self.width()
        cols = 5 if w>=1500 else 4 if w>=1200 else 3 if w>=980 else 2 if w>=680 else 1
        if cols != self._grid_cols:
            self._grid_cols = cols
            self._relayout()

    def _relayout(self):
        while self.grid.count(): self.grid.takeAt(0)
        for c in range(max(1,self._grid_cols)): self.grid.setColumnStretch(c,1)
        j=0
        for w in self._cards:
            if not w.isVisible(): continue
            r,c = divmod(j, self._grid_cols)
            self.grid.addWidget(w, r, c, Qt.AlignTop)
            j+=1

    #Cards
    def _apply_card_theme(self, card: QFrame, ext: str, title: QLabel, subtitle: QLabel):
        ext = (ext or "").lower().lstrip(".")
        # bg, border, title_color, subtitle_color
        theming = {
            "pdf":  ("#3b1d1d", "#e74c3c", "#ffe9e9", "#f6c8c8"),
            "doc":  ("#152538", "#3498db", "#d7eaff", "#a2c9ef"),
            "docx": ("#152538", "#3498db", "#d7eaff", "#a2c9ef"),
            "xls":  ("#14281d", "#27ae60", "#d6ffe6", "#b6f5d0"),
            "xlsx": ("#14281d", "#27ae60", "#d6ffe6", "#b6f5d0"),
            "csv":  ("#14281d", "#27ae60", "#d6ffe6", "#b6f5d0"),
            "txt":  ("#1f2328", "#7f8c8d", "#f0f0f0", "#c8d0d3"),
        }.get(ext, ("", "", "", ""))

        bg, border, title_c, sub_c = theming
        card.setObjectName("DocCard")
        if bg:
            card.setStyleSheet(
                f"""
                QFrame#DocCard {{
                    background:{bg};
                    border:1px solid {border};
                    border-radius:10px;
                }}
                QFrame#DocCard QLabel[role="title"] {{ color:{title_c}; }}
                QFrame#DocCard QLabel[role="subtitle"] {{ color:{sub_c}; }}
                """
            )
        else:
            # fallback: mantém seu "Surface"
            card.setObjectName("Surface")
            card.setStyleSheet("")

        # aplica roles para o QSS acima
        title.setProperty("role", "title")
        subtitle.setProperty("role", "subtitle")
        title.style().unpolish(title); title.style().polish(title)
        subtitle.style().unpolish(subtitle); subtitle.style().polish(subtitle)

    def _card(self, m: Dict) -> QFrame:
        from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
        import os

        card = QFrame(parent=self)
        card.setMaximumWidth(280)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        lay = QVBoxLayout(card); lay.setContentsMargins(12,12,12,12); lay.setSpacing(6)
        title = QLabel(m.get("title","")); title.setStyleSheet("font-weight:700; font-size:14px;")
        subtitle = QLabel(os.path.basename(m.get("path",""))); subtitle.setStyleSheet("font-size:12px;")
        subtitle.setWordWrap(True)

        # pinta o card pelo tipo
        ext = os.path.splitext(m.get("path",""))[1]
        self._apply_card_theme(card, ext, title, subtitle)

        row = QHBoxLayout(); row.addStretch()
        bt = self._gold("Abrir", 96, 28)
        bt.clicked.connect(lambda _=None, meta=m: self.open_doc.emit(meta))
        row.addWidget(bt)

        lay.addWidget(title); lay.addWidget(subtitle); lay.addStretch(); lay.addLayout(row)
        return card
