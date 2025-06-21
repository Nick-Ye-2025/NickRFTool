class ThemeManager:
    def __init__(self):
        self.current_theme = "dark"
        
    def apply_theme(self, widget):
        if self.current_theme == "dark":
            widget.setStyleSheet("""
                QWidget { background: #2D2D2D; color: #FFFFFF; }
                QTreeWidget { border-right: 1px solid #404040; }
                QPushButton { min-width: 40px; border-radius: 4px; }
            """)