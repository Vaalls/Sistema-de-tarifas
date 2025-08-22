from PySide6.QtWidgets import QApplication

class ThemeManager:
    DARK = "dark"
    LIGHT = "light"

    def __init__(self, app: QApplication | None = None):
        # aceita ThemeManager(app) ou ThemeManager() (usa QApplication.instance())
        self.app = app or QApplication.instance()
        self.current = ThemeManager.DARK
        self.tokens_dark = {
                "bg": "#0D1117",
                "surface": "#161B22",
                "primary": "#0B2A4A",
                "accent": "#D4AF37",
                "text": "#E6EAF2",
                "muted": "#8B98A5",
                "success": "#1FA97A",
                "warning": "#E0A800",
                "error": "#D64545",
                "sidebar_btn": "#B38B4D",
                "sidebar_btn_hover": "#A07A43",
                "sidebar_btn_text": "#0D1117",
        }
        self.tokens_light = {
                "bg": "#F5F7FA",
                "surface": "#FFFFFF",
                "primary": "#0B2A4A",
                "accent": "#C49A2E",
                "text": "#0B1220",
                "muted": "#6B7280",
                "success": "#0F9D58",
                "warning": "#B88700",
                "error": "#C0392B",
                "sidebar_btn": "#B38B4D",
                "sidebar_btn_hover": "#A07A43",
                "sidebar_btn_text": "#0B1220",
        }


    def apply(self, mode: str | None = None):
        if mode:
            self.current = mode
        tokens = self.tokens_dark if self.current == ThemeManager.DARK else self.tokens_light
        # Usar % formatting para evitar conflito com chaves dos QSS
        qss = """
            QWidget {
                background-color: %(bg)s;
                color: %(text)s;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            
            QLabel { background: transparent; }  /* evita a “faixa” escura atrás dos títulos */
            
            /* Qt StyleSheets não suportam filter/opacity */

            QFrame#Surface {
                background-color: %(surface)s;
                border-radius: 10px;
            }
            
            QLineEdit, QComboBox {
                background: %(surface)s;
                border: 1px solid %(muted)s;
                padding: 6px 8px; border-radius: 6px;
            }
            
            QPushButton {
                background: %(primary)s; color: %(text)s;
                border: none; padding: 8px 12px; border-radius: 8px;
            }
            
            QPushButton[role="sidebar"] {
                background: %(sidebar_btn)s;
                color: %(sidebar_btn_text)s;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }
            
            QPushButton[role="sidebar"]:hover {background: %(sidebar_btn_hover)s;}
 
            QPushButton:hover {
                background: %(primary)s;
            }
            
            QPushButton:disabled {
            background: %(muted)s; color: %(bg)s;
            }
            
            QPushButton[accent="true"] { background: %(accent)s; color: %(bg)s; }
            
            QPushButton[accent="true"]:hover { background: %(accent)s; }
            
            QToolButton { border: none; padding: 6px; border-radius: 8px; }
            
            QToolButton:hover { background: %(surface)s; }
            
            QHeaderView::section {
                background: %(surface)s; color: %(text)s;
                padding: 6px; border: none; border-bottom: 1px solid %(muted)s;
            }
            
            QTableWidget { background: %(surface)s; border-radius: 8px; }
            
            QTableWidget::item:selected { background: %(primary)s; color: %(text)s; } 
        """ % tokens
        self.app.setStyleSheet(qss)


    def toggle(self):
        self.current = ThemeManager.LIGHT if self.current == ThemeManager.DARK else ThemeManager.DARK
        self.apply()
