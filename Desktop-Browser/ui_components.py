from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt


class UIComponents:
    """Manages UI components and styling."""
    
    @staticmethod
    def get_svg_icon(svg_content, size=QSize(32, 32)):
        """Convert SVG content to a QIcon."""
        try:
            renderer = QSvgRenderer()
            renderer.load(svg_content.encode('utf-8'))
            
            pixmap = QPixmap(size)
            pixmap.fill(Qt.GlobalColor.transparent)  # Fill with transparent background
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            return QIcon(pixmap)
        except Exception as e:
            print(f"Error creating SVG icon: {e}")
            return QIcon()  # Return empty icon on error
    
    @staticmethod
    def get_main_window_stylesheet():
        """Get the main window stylesheet."""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border-top: 2px solid #C2C2C2;
                background-color: #f5f5f5;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #C4C4C3;
                border-bottom-color: #C2C2C2;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 5px;
                margin: 2px;
                color: black;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #f0f0f0;
                border-color: #A0A0A0;
            }
            QTabBar::tab:selected {
                font-weight: bold;
            }
            QToolBar {
                background: #ffffff;
                border: none;
                padding: 5px;
            }
            QToolBar QToolButton {
                background: #e0e0e0;
                border: none;
                border-radius: 16px;
                padding: 5px;
                margin: 2px;
            }
            QToolBar QToolButton:hover {
                background: #d0d0d0;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #C4C4C3;
                border-radius: 5px;
                padding: 5px;
                margin-left: 10px;
                margin-right: 10px;
                font-size: 14px;
                color: black;
            }
        """
    
    @staticmethod
    def get_login_dialog_stylesheet():
        """Get the login dialog stylesheet."""
        return """
            QDialog {
                background-color: #f0f0f0;
                border-radius: 10px;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
                background: white;
                color: black;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
             QLabel#contactLabel {
                margin-top: 50px;
                margin-bottom: 10px;
            }
        """


class IconProvider:
    """Provides SVG icons for the application."""
    
    @staticmethod
    def back_icon_svg():
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H19v-2z"/></svg>"""

    @staticmethod
    def forward_icon_svg():
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M5 13h11.17l-5.59 5.59L13 20l8-8-8-8-1.41 1.41L16.17 11H5v2z"/></svg>"""

    @staticmethod
    def reload_icon_svg():
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.86 0 7 3.14 7 7 0 .78-.13 1.52-.36 2.22l1.46 1.46C20.68 15.31 21 14.19 21 13c0-5-4-9-9-9zm-7.64.78L2.93 3.36C2.32 4.52 2 5.73 2 7c0 5 4 9 9 9v3l4-4-4-4v3c-3.86 0-7-3.14-7-7 0-1.11.24-2.16.64-3.22z"/></svg>"""

    @staticmethod
    def new_tab_icon_svg():
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4v8H4v2h8v8h2v-8h8v-2h-8V4h-2z"/></svg>"""

    @staticmethod
    def clean_icon_svg():
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4v2H6v12h12V6h-6V4h-2v2h-4V4h-2zm6 14H6v-2h12v2z"/></svg>"""
