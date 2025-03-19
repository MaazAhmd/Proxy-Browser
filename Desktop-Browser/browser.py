import os
import sys

from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QToolBar
)

from cookies import Cookies
from events import Events

profile = None
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.cookies = Cookies(profile)

        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        events = Events(profile)
        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Browser Window Setup
        self.setWindowTitle("Browser")
        self.resize(1280, 800)
        # Tab Widget to manage multiple tabs
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(False)
        self.setCentralWidget(self.tabs)
        events.tabs = self.tabs

        # Navigation bar (Reload button)
        navbar = QToolBar("Navigation")
        self.addToolBar(navbar)

        # Reload button (SVG icon)
        reload_button = QAction(events.get_svg_icon(events.reload_icon_svg()), "Reload", self)
        reload_button.triggered.connect(events.reload_page)
        navbar.addAction(reload_button)

        # New Tab button (SVG icon)

        # Apply CSS styling
        self.setStyleSheet("""
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
        """)

        # Open a new tab when the browser starts
        events.new_tab()

    def closeEvent(self, event):
        """Handle application close event with uploading in the background."""
        event.accept()
