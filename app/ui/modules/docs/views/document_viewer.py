# app/ui/modules/docs/views/document_viewer.py
from __future__ import annotations
import os, shutil
from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QPlainTextEdit, QTableWidget, QTableWidgetItem
)

# PDF (QtPdf)
try:
    from PySide6.QtPdfWidgets import QPdfView
    from PySide6.QtPdf import QPdfDocument
    _PDF_OK = True
except Exception:
    _PDF_OK = False

class DocumentViewer(QWidget):
    go_back = Signal()

    def __init__(self):
        super().__init__()
        self._meta: Dict | None = None
        self._pdf_doc = None
        self._build()

    def _gold(self, t, w=120, h=32):
        b = QPushButton(t); b.setProperty("accent","true")
        b.setFixedSize(w,h); b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet("QPushButton:hover{background:#C49A2E;}")
        return b

    def _build(self):
        root = QVBoxLayout(self); root.setSpacing(10); root.setContentsMargins(12,12,12,12)
        top = QHBoxLayout()
        self.bt_back = self._gold("Voltar", 100, 30)
        self.bt_export = self._gold("Exportar", 110, 30)
        self.lbl = QLabel(""); self.lbl.setStyleSheet("color:#8B98A5;")
        top.addWidget(self.bt_back); top.addWidget(self.bt_export); top.addStretch(); top.addWidget(self.lbl)
        root.addLayout(top)

        self._stack = QWidget(); self._stack_lay = QVBoxLayout(self._stack); self._stack_lay.setContentsMargins(0,0,0,0)
        root.addWidget(self._stack, stretch=1)

        # Widgets possíveis
        self._pdf = QPdfView() if _PDF_OK else None
        self._text = QPlainTextEdit(); self._text.setReadOnly(True)
        self._table = QTableWidget(0,0)

        self.bt_back.clicked.connect(self.go_back.emit)
        self.bt_export.clicked.connect(self._export_copy)

    # ---------- API ----------
    def open_document(self, meta: Dict):
        """meta = {'title','path'}"""
        self._meta = meta
        path = meta.get("path","")
        self.lbl.setText(os.path.basename(path))

        # limpa stack
        while self._stack_lay.count():
            it = self._stack_lay.takeAt(0)
            if it.widget(): it.widget().setParent(None)

        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf" and _PDF_OK:
            self._open_pdf(path)
        elif ext in (".csv", ".txt"):
            self._open_text_or_csv(path, ext)
        elif ext in (".xlsx", ".xls"):
            # tentativa simples: abrir no aplicativo padrão
            os.startfile(path)  # Windows only
            # mostra um texto informativo
            self._text.setPlainText("Arquivo XLS(X) aberto no aplicativo padrão.\nFeche-o para retornar.")
            self._stack_lay.addWidget(self._text)
        else:
            # fallback: abrir no app padrão
            try:
                os.startfile(path)
            except Exception as e:
                self._text.setPlainText(f"Não foi possível abrir o arquivo.\n{e}")
                self._stack_lay.addWidget(self._text)

    # ---------- viewers ----------
    def _open_pdf(self, path:str):
        self._pdf_doc = QPdfDocument(self)
        self._pdf_doc.load(path)
        self._pdf.setDocument(self._pdf_doc)
        self._stack_lay.addWidget(self._pdf)

    def _open_text_or_csv(self, path:str, ext:str):
        if ext == ".csv":
            import csv
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            if rows:
                self._table.setRowCount(len(rows)-1)
                self._table.setColumnCount(len(rows[0]))
                self._table.setHorizontalHeaderLabels(rows[0])
                for r,row in enumerate(rows[1:]):
                    for c,val in enumerate(row):
                        self._table.setItem(r,c,QTableWidgetItem(val))
                self._stack_lay.addWidget(self._table)
                return
        # txt (ou csv vazio)
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._text.setPlainText(f.read())
        except Exception as e:
            self._text.setPlainText(f"Erro ao ler arquivo: {e}")
        self._stack_lay.addWidget(self._text)

    def _export_copy(self):
        if not self._meta: return
        src = self._meta.get("path","")
        base = os.path.basename(src)
        tgt, _ = QFileDialog.getSaveFileName(self, "Exportar", base)
        if not tgt: return
        shutil.copyfile(src, tgt)
