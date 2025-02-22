import os
import threading
import sys
import requests
import boto3
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QToolBar,
    QLineEdit,
    QMessageBox,
    QDialog,
    QLineEdit,
)
from PyQt6.QtCore import QTimer, QDateTime, QCoreApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtNetwork import QNetworkProxy
from cookies import Cookies
from login import LoginDialog
from events import Events
from globals import config

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.username = None
        self._s3_client = boto3.client(
            's3',
            aws_access_key_id=config.CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=config.CLOUDFLARE_SECRET_KEY,
            endpoint_url=config.CLOUDFLARE_ENDPOINT_URL
        )
        # self.check_for_updates()
        # Show login dialog
        self.login_dialog = LoginDialog()
        if self.login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.username = self.login_dialog.username
            self.cookies = Cookies(self.username, self._s3_client)
            self.cookies._ensure_directories()
            self.set_proxy()
            print(f"Proxy set to {config.PROXY_URL}:{config.PROXY_PORT}")
            self.disabled_after = self.login_dialog.disabled_after  # Store the disabled_after value
            self.start_session_timer()
            if config.SYNC_DATA:
                threading.Thread(target=self.cookies.download_data_from_cloud, daemon=True).start()
        else:
            sys.exit()

        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        events = Events()
        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Browser Window Setup
        self.setWindowTitle("Espot Browser")
        self.resize(1280, 800)
        self.cookies._getProfile()
        # Tab Widget to manage multiple tabs
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(events.close_tab)
        self.tabs.setMovable(True)  # Allow rearranging tabs
        self.setCentralWidget(self.tabs)
        events.tabs = self.tabs

        # Navigation bar (Back, Forward, Reload buttons)
        navbar = QToolBar("Navigation")
        self.addToolBar(navbar)

        # Back button (SVG icon)
        back_button = QAction(events.get_svg_icon(events.back_icon_svg()), "Back", self)
        back_button.triggered.connect(events.go_back)
        navbar.addAction(back_button)

        # Forward button (SVG icon)
        forward_button = QAction(events.get_svg_icon(events.forward_icon_svg()), "Forward", self)
        forward_button.triggered.connect(events.go_forward)
        navbar.addAction(forward_button)

        # Reload button (SVG icon)
        reload_button = QAction(events.get_svg_icon(events.reload_icon_svg()), "Reload", self)
        reload_button.triggered.connect(events.reload_page)
        navbar.addAction(reload_button)

        # New Tab button (SVG icon)
        new_tab_button = QAction(events.get_svg_icon(events.new_tab_icon_svg()), "New Tab", self)
        new_tab_button.triggered.connect(events.new_tab)
        navbar.addAction(new_tab_button)

        # Clean Data button (SVG icon)
        clean_button = QAction(events.get_svg_icon(events.clean_icon_svg()), "Clean Now", self)
        clean_button.triggered.connect(lambda: self.cookies.clean_data(self.tabs, events.new_tab, config.PROFILE))
        navbar.addAction(clean_button)

        # Search bar
        search_bar = QLineEdit(self)
        search_bar.setPlaceholderText("Enter URL or Web Address")
        search_bar.returnPressed.connect(events.open_url)
        navbar.addWidget(search_bar)
        events.search_bar = search_bar

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
        """)

        # Open a new tab when the browser starts
        events.new_tab()

    def closeEvent(self, event):
        """Handle application close event with uploading in the background."""
        self.login_dialog.stop_heartbeat()
        self.cleanup_webengine_pages()
        if(config.SYNC_DATA):
        # Show a dialog box indicating that data is being uploaded
            self.msg_box = QMessageBox(self)
            self.msg_box.setWindowTitle("Info")
            self.msg_box.setText(config.CLOSING_DIALOG if config.CLOSING_DIALOG else "Uploading your data to the cloud. The program will exit automatically.")
            self.msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton)
            self.msg_box.show()

            # Start the upload in a separate thread
            self.upload_thread = threading.Thread(target=self.cookies.upload_data_to_cloud)
            self.upload_thread.start()

            # Use a QTimer to check if the upload is complete and close the application
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.check_upload_complete)
            self.timer.start(1000)

            # Ignore the close event for now
            event.ignore()
        else:
            event.accept()

    def check_upload_complete(self):
        """Check if the upload thread is complete."""
        if not self.upload_thread.is_alive():
            self.timer.stop()  # Stop the timer
            self.msg_box.close()  # Close the message box
            QCoreApplication.exit()  # Exit the application

    def cleanup_webengine_pages(self):
        """Ensure all QWebEnginePage instances are properly deleted."""
        for i in range(self.tabs.count()):
            browser_view = self.tabs.widget(i)
            if browser_view:
                browser_view.setPage(None)
                browser_view.deleteLater()

    def start_session_timer(self):
        """Start a timer to check session expiration every minute."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_session_expiration)
        self.timer.start(10000)  # Check every 10 seconds

    def check_session_expiration(self):
        """Check if the session has expired or is about to expire."""
        current_time = QDateTime.currentDateTime()
        expiration_time = QDateTime.fromString(self.disabled_after, "ddd, dd MMM yyyy HH:mm:ss 'GMT'")

        if self.disabled_after:
            time_left = current_time.secsTo(expiration_time)

            if time_left <= 0:
                self.timer.stop()
                QMessageBox.warning(self, "Session Expired", "Your session has expired.")
                self.close()
                self.show_login_dialog()
            elif time_left <= 300:
                QMessageBox.warning(self, "Session Expiring Soon",
                                    "Your session will expire in 5 minutes. Please save your work.")

    def show_login_dialog(self):
        """Show the login dialog."""
        login_dialog = LoginDialog()
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.set_proxy()
            print(f"Proxy set to {config.PROXY_URL}:{config.PROXY_PORT}")
            self.disabled_after = login_dialog.disabled_after
            login_dialog.start_heartbeat()
        else:
            sys.exit()

    def set_proxy(self):
        """Set up the proxy for the browser."""
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
        proxy.setHostName(config.PROXY_URL)
        proxy.setPort(int(config.PROXY_PORT))
        proxy.setUser(config.PROXY_USER)
        proxy.setPassword(config.PROXY_PASSWORD)
        QNetworkProxy.setApplicationProxy(proxy)

    def check_proxy(self):
        """Check if the proxy is active by making a test request."""
        proxy_address = f"{config.PROXY_URL}:{config.PROXY_PORT}"
        proxies = {
            "http": f"http://{config.PROXY_USER}:{config.PROXY_PASSWORD}@{proxy_address}",
            "https": f"https://{config.PROXY_USER}:{config.PROXY_PASSWORD}@{proxy_address}",
        }
        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
            if response.status_code == 200:
                print("Proxy is active. IP:", response.json()["origin"])
            else:
                print("Failed to connect through proxy.")
        except requests.RequestException as e:
            print("Error connecting through proxy:", e)