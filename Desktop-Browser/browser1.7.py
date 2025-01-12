import re
import os
import sys
import requests
import jwt
import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QToolBar,
    QAction,
    QLineEdit,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtCore import QUrl, Qt, QTimer, QDateTime
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage, QWebEngineProfile
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtNetwork import QNetworkCookieJar, QNetworkProxy

# Global variables for proxy details
SECRET_KEY = 'QR2vZ7ocC7JkF0b02Kd7a5slN92MYgvd'
proxy_url = None
proxy_port = None
proxy_user = None
proxy_password = None

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.username = None
        self.password = None
        self.disabled_after = None
        self.setFixedSize(400, 400)
        layout = QVBoxLayout()
        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')

        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Add logo at the top
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap(os.path.join(assets_path, "logo.png"))
        self.logo_pixmap = self.logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        # Username input
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit("")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Password input
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit("")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.login_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.login_button)
        self.contact_label = QLabel("In case of issues, contact the administrator at: 03204342479")
        self.contact_label.setObjectName("contactLabel")
        self.contact_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.contact_label)
        self.setLayout(layout)

        # Apply CSS styling
        self.setStyleSheet("""
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
        """)

    def login(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        proxy_details = self.get_proxy_details(self.username, self.password)
        if proxy_details:
            global proxy_url, proxy_port, proxy_user, proxy_password
            proxy_url = proxy_details['proxy_url']
            proxy_port = proxy_details['proxy_port']
            proxy_user = proxy_details['proxy_user']
            proxy_password = proxy_details['proxy_password']
            self.disabled_after = proxy_details['disabled_after']
            self.accept()

    def generate_jwt(self):
        """Generate a JWT token."""
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    def get_proxy_details(self, username, password):
        """Call the API to get proxy details."""
        api_url = "http://127.0.0.1:5000/proxy/get-proxy"
        token = self.generate_jwt()
        headers = {'x-access-token': token}
        try:
            response = requests.post(api_url, json={"username": username, "password": password}, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 1:
                    return data['proxy_details']
                else:
                    QMessageBox.critical(self, "Login Failed", data['error_message'])
                    return None
            else:
                QMessageBox.critical(self, "Login Failed", "Error connecting to the server.")
                return None
        except requests.RequestException as e:
            print("Error calling API:", e)
            QMessageBox.critical(self, "Login Failed", "Error connecting to the server.")
            return None

    def start_session_timer(self):
        """Start a timer to check session expiration every minute."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_session_expiration)
        self.timer.start(10000)  # Check every 60 seconds

    def check_session_expiration(self):
        """Check if the session has expired."""
        print("Checking session expiration...")
        if self.disabled_after and QDateTime.currentDateTime() > QDateTime.fromString(self.disabled_after, Qt.ISODate):
            print("Session expired.")
            self.timer.stop()
            QMessageBox.warning(self, "Session Expired", "Your session has expired.")
            self.close()
            self.show_login_dialog()

    def show_login_dialog(self):
        """Show the login dialog."""
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            self.set_proxy()
            print(f"Proxy set to {proxy_url}:{proxy_port}")
        else:
            sys.exit(1)

class CustomWebEnginePage(QWebEnginePage):
    """Custom QWebEnginePage for handling JavaScript and CSP issues."""
    def javaScriptConsoleMessage(self, level, message, line, source):
        """Log JavaScript console messages for debugging."""
        print(f"JS Console: {message} (line {line}, source {source})")

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        """Accept or deny navigation requests."""
        print(f"Navigation Request: {url.toString()}")
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Show login dialog
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
            self.set_proxy()
            print(f"Proxy set to {proxy_url}:{proxy_port}")
            self.disabled_after = login_dialog.disabled_after  # Store the disabled_after value
            self.start_session_timer()
        else:
            sys.exit(1)
        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')

        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Browser Window Setup
        self.setWindowTitle("Simple Browser")
        self.resize(1280, 800)

        # Tab Widget to manage multiple tabs
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # Navigation bar (Back, Forward, Reload buttons)
        navbar = QToolBar("Navigation")
        self.addToolBar(navbar)

        # Back button (SVG icon)
        back_button = QAction(self.get_svg_icon(self.back_icon_svg()), "Back", self)
        back_button.triggered.connect(self.go_back)
        navbar.addAction(back_button)

        # Forward button (SVG icon)
        forward_button = QAction(self.get_svg_icon(self.forward_icon_svg()), "Forward", self)
        forward_button.triggered.connect(self.go_forward)
        navbar.addAction(forward_button)

        # Reload button (SVG icon)
        reload_button = QAction(self.get_svg_icon(self.reload_icon_svg()), "Reload", self)
        reload_button.triggered.connect(self.reload_page)
        navbar.addAction(reload_button)

        # New Tab button (SVG icon)
        new_tab_button = QAction(self.get_svg_icon(self.new_tab_icon_svg()), "New Tab", self)
        new_tab_button.triggered.connect(self.new_tab)
        navbar.addAction(new_tab_button)

        # Clean Data button (SVG icon)
        clean_button = QAction(self.get_svg_icon(self.clean_icon_svg()), "Clean Now", self)
        clean_button.triggered.connect(self.clean_data)
        navbar.addAction(clean_button)

        # Search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter URL or Web Address")
        self.search_bar.returnPressed.connect(self.open_url)
        navbar.addWidget(self.search_bar)

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
            }
        """)

        # Open a new tab when the browser starts
        self.new_tab()

    def set_proxy(self):
        """Set up the proxy for the browser."""
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.HttpProxy)
        proxy.setHostName(proxy_url)
        proxy.setPort(int(proxy_port))
        proxy.setUser(proxy_user)
        proxy.setPassword(proxy_password)
        QNetworkProxy.setApplicationProxy(proxy)

    def check_proxy(self):
        """Check if the proxy is active by making a test request."""
        proxy_address = f"{proxy_url}:{proxy_port}"
        proxies = {
            "http": f"http://{proxy_user}:{proxy_password}@{proxy_address}",
            "https": f"https://{proxy_user}:{proxy_password}@{proxy_address}",
        }
        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
            if response.status_code == 200:
                print("Proxy is active. IP:", response.json()["origin"])
            else:
                print("Failed to connect through proxy.")
        except requests.RequestException as e:
            print("Error connecting through proxy:", e)

    def new_tab(self):
        """Open a new tab in the tab widget."""
        # Create a new WebEngineView for the tab
        browser_view = QWebEngineView()
        browser_view.setPage(CustomWebEnginePage(browser_view))  # Use custom page
        browser_view.setUrl(QUrl("https://espotsolutions.com/"))  # Start with Google

        # Enable JavaScript and adjust settings for compatibility
        browser_view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebGLEnabled, True)

        # Set User-Agent to mimic Chrome (bypasses some stricter CSPs)
        browser_view.page().profile().setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        )

        # Add the new tab
        index = self.tabs.addTab(browser_view, "New Tab")
        self.tabs.setCurrentIndex(index)

        # Update title when the page is loaded
        browser_view.loadFinished.connect(
            lambda ok, browser_view=browser_view: self.update_tab_title(browser_view, ok)
        )

    def update_tab_title(self, browser_view, ok):
        """Update the tab title based on the page title."""
        if ok:
            title = browser_view.page().title()
            truncated_title = title[:15] if title else "Untitled"  # Truncate to 15 characters
            self.tabs.setTabText(self.tabs.indexOf(browser_view), truncated_title)
        else:
            self.tabs.setTabText(self.tabs.indexOf(browser_view), "Failed to load")

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.tabs.count() > 1:  # Ensure at least one tab remains open
            self.tabs.removeTab(index)

    def go_back(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.back()

    def go_forward(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.forward()

    def reload_page(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.reload()

    def open_url(self):
        query = self.search_bar.text().strip()
        if query:
            # If the query starts with "www" or lacks a protocol, consider it a URL
            if re.match(r"^(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", query):
                # If it doesn't have 'http://' or 'https://', add 'http://'
                if not query.startswith(('http://', 'https://')):
                    query = 'http://' + query
                # Open the URL in the current tab
                current_browser = self.get_current_browser()
                if current_browser:
                    current_browser.setUrl(QUrl(query))  # Open the URL directly
            else:
                # If not a URL, treat it as a search query
                search_url = f"https://www.google.com/search?q={query}"
                current_browser = self.get_current_browser()
                if current_browser:
                    current_browser.setUrl(QUrl(search_url))  # Perform Google search

    def get_current_browser(self):
        """Return the current browser (QWebEngineView) from the active tab."""
        current_index = self.tabs.currentIndex()
        if current_index != -1:
            return self.tabs.widget(current_index)
        return None

    def get_svg_icon(self, svg_content):
        """Convert SVG content to a QIcon."""
        try:
            svg_renderer = QSvgRenderer(svg_content.encode("utf-8"))
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            svg_renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        except Exception as e:
            print(f"Error creating SVG icon: {e}")
            return QIcon()

    def back_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H19v-2z"/></svg>"""

    def forward_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M5 13h11.17l-5.59 5.59L13 20l8-8-8-8-1.41 1.41L16.17 11H5v2z"/></svg>"""

    def reload_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.86 0 7 3.14 7 7 0 .78-.13 1.52-.36 2.22l1.46 1.46C20.68 15.31 21 14.19 21 13c0-5-4-9-9-9zm-7.64.78L2.93 3.36C2.32 4.52 2 5.73 2 7c0 5 4 9 9 9v3l4-4-4-4v3c-3.86 0-7-3.14-7-7 0-1.11.24-2.16.64-3.22z"/></svg>"""

    def new_tab_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4v8H4v2h8v8h2v-8h8v-2h-8V4h-2z"/></svg>"""

    def clean_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4v2H6v12h12V6h-6V4h-2v2h-4V4h-2zm6 14H6v-2h12v2z"/></svg>"""

    def clean_data(self):
        """Clear all the browser data like history, cookies, cache, etc."""
        profile = QWebEngineProfile.defaultProfile()

        # Clear History (Since QWebEngine does not provide a method, this is a challenge)
        # Consider implementing custom history management or integrating other solutions if necessary.

        # Clear Cookies
        profile.cookieStore().deleteAllCookies()  # Delete all cookies from the current profile

        # Clear Cache
        profile.clearHttpCache()  # Clear the HTTP cache
        
        # Clear Form Data (if desired)
        profile.clearAllData()  # If this exists in your Qt version, it clears form autofill and more

        # Show a confirmation message
        QMessageBox.information(self, "Data Cleared", "All browser data has been successfully cleared.")

if __name__ == "__main__":
    app = QApplication([])

    browser = SimpleBrowser()
    browser.show()

    app.exec_()