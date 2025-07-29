import os
import sys
import threading
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QToolBar,
    QLineEdit,
    QDialog,
)
from PyQt6.QtCore import QEventLoop, QCoreApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtNetwork import QNetworkProxy
from cookies import Cookies
from login import LoginDialog
from events import Events
from globals import config
from update_manager import UpdateManager
from system_tray import SystemTrayManager
from session_manager import SessionManager
from web_engine_manager import WebEngineManager
from ui_components import UIComponents


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.username = None
        self.force_quit = False
        
        # Initialize managers
        self.update_manager = UpdateManager(self)
        self.system_tray_manager = SystemTrayManager(self)
        
        # Check for updates first
        latest_version = self.update_manager.check_for_updates()
        if latest_version:
            print(f"Mandatory update required! Updating to version {latest_version}...")
            self.update_manager.download_and_install_update()
            # Wait for update to finish before proceeding
            loop = QEventLoop()
            self.update_manager.update_thread.download_complete.connect(loop.quit)
            loop.exec()
            QCoreApplication.exit()

        # Handle login
        self.login_dialog = LoginDialog()
        if self.login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.username = self.login_dialog.username
            self.cookies = Cookies(self.username, self.update_manager._s3_client)
            self.cookies._ensure_directories()
            self.set_proxy()
            print(f"Proxy set to {config.PROXY_URL}:{config.PROXY_PORT}")
            
            # Initialize session manager
            self.session_manager = SessionManager(self, self.login_dialog)
            self.session_manager.set_session_expiration(self.login_dialog.disabled_after)
            self.session_manager.start_session_timer()
            
            # Download data if sync is enabled
            if config.SYNC_DATA:
                download_thread = threading.Thread(target=self.cookies.download_data_from_cloud, daemon=True)
                download_thread.start()
                download_thread.join()
        else:
            print("Login failed. Exiting...")
            sys.exit(0)

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        # Set window properties
        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')
            
        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        self.setWindowTitle("Espot Browser")
        self.resize(1280, 800)
        
        # Initialize browser profile
        self.cookies._getProfile()
        
        # Setup tabs
        self._setup_tabs()
        
        # Setup navigation bar
        self._setup_navigation()
        
        # Apply styling
        self.setStyleSheet(UIComponents.get_main_window_stylesheet())
        
        # Initialize components
        self.events.new_tab()
        WebEngineManager.set_default_user_agent()
        self.system_tray_manager.init_system_tray()

    def _setup_tabs(self):
        """Setup the tab widget."""
        self.events = Events()
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.events.close_tab)
        self.tabs.setMovable(True)
        self.setCentralWidget(self.tabs)
        self.events.tabs = self.tabs

    def _setup_navigation(self):
        """Setup the navigation toolbar."""
        navbar = QToolBar("Navigation")
        self.addToolBar(navbar)

        # Navigation buttons
        buttons = [
            ("Back", self.events.back_icon_svg(), self.events.go_back),
            ("Forward", self.events.forward_icon_svg(), self.events.go_forward),
            ("Reload", self.events.reload_icon_svg(), self.events.reload_page),
            ("New Tab", self.events.new_tab_icon_svg(), self.events.new_tab),
            ("Clean Now", self.events.clean_icon_svg(), 
             lambda: self.cookies.clean_data(self.tabs, self.events.new_tab, config.PROFILE))
        ]

        for name, icon_svg, callback in buttons:
            button = QAction(UIComponents.get_svg_icon(icon_svg), name, self)
            button.triggered.connect(callback)
            navbar.addAction(button)

        # Search bar
        search_bar = QLineEdit(self)
        search_bar.setPlaceholderText("Enter URL or Web Address")
        search_bar.returnPressed.connect(self.events.open_url)
        navbar.addWidget(search_bar)
        self.events.search_bar = search_bar

    def set_proxy(self):
        """Set up proxy configuration."""
        if config.PROXY_URL and config.PROXY_PORT:
            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
            proxy.setHostName(config.PROXY_URL)
            proxy.setPort(int(config.PROXY_PORT))
            if config.PROXY_USER and config.PROXY_PASSWORD:
                proxy.setUser(config.PROXY_USER)
                proxy.setPassword(config.PROXY_PASSWORD)
            QNetworkProxy.setApplicationProxy(proxy)

    def closeEvent(self, event):
        """Handle close event - minimize to tray instead of closing"""
        if not self.force_quit and hasattr(self.system_tray_manager, 'tray_icon') and self.system_tray_manager.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.system_tray_manager.show_message(
                "Espot Browser",
                "Application was minimized to tray"
            )
        else:
            # Handle cleanup and data upload
            self.session_manager.cleanup_on_close()
            WebEngineManager.cleanup_web_engine_pages(self.tabs)
            
            if self.session_manager.handle_data_upload_on_close(self.cookies, config):
                event.ignore()
            else:
                event.accept()
