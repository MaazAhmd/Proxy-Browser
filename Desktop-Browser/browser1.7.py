import re
import os
import threading
import sys
import requests
import jwt
import shutil
import datetime
import boto3
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QToolBar,
    QLineEdit,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QWidget
)
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl, Qt, QTimer, QDateTime, QCoreApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QAction
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtNetwork import QNetworkProxy, QNetworkCookie

# Global variables for proxy details
SECRET_KEY = 'QR2vZ7ocC7JkF0b02Kd7a5slN92MYgvd'
proxy_url = None
proxy_port = None
proxy_user = None
proxy_password = None


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Espot Browser")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.username = None
        self.password = None
        self.disabled_after = None
        self.setFixedSize(400, 450)
        layout = QVBoxLayout()
        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')

        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Add logo at the top
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap(os.path.join(assets_path, "logo.png"))
        self.logo_pixmap = self.logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)
        self.tagline_label = QLabel("Your Gateway to Business Excellence")
        self.tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.tagline_label)
        self.phone_label = QLabel("03204342479")
        self.phone_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.phone_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.phone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.phone_label)
        # Username input
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit("")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Password input
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit("")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.login_button)
        self.contact_label = QLabel("In case of issues, contact Espot Solutions at: 03204342479")
        self.contact_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.contact_label.setObjectName("contactLabel")
        self.contact_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
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
            self.start_heartbeat()

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
        api_url = "https://espotbrowser.onrender.com/proxy/get-proxy"
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

    def start_heartbeat(self):
        """Start a timer to send heartbeat signals to the server."""
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(lambda: self.send_heartbeat(True))
        self.heartbeat_timer.start(60000)  # Send heartbeat every 60 seconds
        self.send_heartbeat(True)  # Send initial heartbeat

    def stop_heartbeat(self):
        """Stop the heartbeat timer and send a final signal to the server."""
        if hasattr(self, 'heartbeat_timer'):
            self.heartbeat_timer.stop()
        self.send_heartbeat(False)

    def send_heartbeat(self, login_status):
        """Send a heartbeat signal to the server."""
        api_url = "https://espotbrowser.onrender.com/heartbeat"
        headers = {'x-access-token': self.generate_jwt()}
        try:
            response = requests.post(api_url, json={"username": self.username, "status": login_status}, headers=headers)
            if response.status_code != 200:
                print("Heartbeat failed:", response.json())
                self.heartbeat_timer.stop()
                QMessageBox.warning(self, "Session Expired", "Your session has expired.")
                self.close()
                self.show_login_dialog()
        except requests.RequestException as e:
            print("Error sending heartbeat:", e)
            self.heartbeat_timer.stop()
            QMessageBox.warning(self, "Session Expired", "Your session has expired.")
            self.close()
            self.show_login_dialog()

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
    _profile = None
    _bucket_name = "espotbrowser-cookies-data"
    _cloudflare_access_key = "194c275f97c43291f4cbc8b54376a2f0"
    _cloudflare_secret_key = "562e52307799862466c2e92d6491d47e7ab226bacf85e8427694b43c378e3352"
    _cloudflare_endpoint_url = "https://381f96a585f51192da401d83b4af0f89.r2.cloudflarestorage.com"

    def __init__(self):
        super().__init__()
        self.username = None
        self._s3_client = boto3.client(
            's3',
            aws_access_key_id=self._cloudflare_access_key,
            aws_secret_access_key=self._cloudflare_secret_key,
            endpoint_url=self._cloudflare_endpoint_url
        )
        # Show login dialog
        self.login_dialog = LoginDialog()
        if self.login_dialog.exec() == QDialog.DialogCode.Accepted:
            self.username = self.login_dialog.username
            self._ensure_directories()
            self.set_proxy()
            print(f"Proxy set to {proxy_url}:{proxy_port}")
            self.disabled_after = self.login_dialog.disabled_after  # Store the disabled_after value
            self.start_session_timer()
            threading.Thread(target=self.download_data_from_cloud, daemon=True).start()
        else:
            sys.exit(app.exec())

        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')

        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Browser Window Setup
        self.setWindowTitle("ESpot Browser")
        self.resize(1280, 800)
        profile = self._getProfile()
        # Tab Widget to manage multiple tabs
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setMovable(True)  # Allow rearranging tabs
        self.setCentralWidget(self.tabs)

        # # Add "+" button to the tab bar
        # self.add_new_tab_button()

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
        self.new_tab()

    def closeEvent(self, event):
        """Handle application close event with uploading in the background."""
        self.login_dialog.stop_heartbeat()
        self.cleanup_webengine_pages()

        # Show a dialog box indicating that data is being uploaded
        self.msg_box = QMessageBox(self)
        self.msg_box.setWindowTitle("Uploading Data")
        self.msg_box.setText("Uploading your data to the cloud. The program will exit automatically.")
        self.msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.msg_box.show()

        # Start the upload in a separate thread
        self.upload_thread = threading.Thread(target=self.upload_data_to_cloud)
        self.upload_thread.start()

        # Use a QTimer to check if the upload is complete and close the application
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_upload_complete)
        self.timer.start(1000)

        # Ignore the close event for now
        event.ignore()

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

    def add_new_tab_button(self):
        """Add a '+' button right next to the tabs on the right side."""
        # Create a layout for the custom tab bar
        custom_tab_bar_layout = QHBoxLayout()
        custom_tab_bar_layout.setContentsMargins(0, 0, 0, 0)  # No margin

        # Add the "+" button
        new_tab_button = QPushButton("+", self)
        new_tab_button.setFixedSize(30, 30)
        new_tab_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_tab_button.clicked.connect(self.new_tab)

        # Add the "+" button to the layout
        custom_tab_bar_layout.addWidget(new_tab_button, alignment=Qt.AlignmentFlag.AlignRight)  # Align button to the right

        # Create a custom widget to hold the layout
        custom_widget = QWidget()
        custom_widget.setLayout(custom_tab_bar_layout)
        # Add the custom widget to the tab bar
        self.tabs.setCornerWidget(custom_widget, Qt.Corner.TopRightCorner)

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
            print(f"Proxy set to {proxy_url}:{proxy_port}")
            self.disabled_after = login_dialog.disabled_after
            login_dialog.start_heartbeat()
        else:
            sys.exit(app.exec())

    def set_proxy(self):
        """Set up the proxy for the browser."""
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
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

    def _ensure_directories(self):
        if not (os.path.exists(self._CACHE_PATH) and os.path.isdir(self._CACHE_PATH)):
            os.makedirs(self._CACHE_PATH)
        if not (os.path.exists(self._STORAGE_PATH) and os.path.isdir(self._STORAGE_PATH)):
            os.makedirs(self._STORAGE_PATH)

    def _getProfile(self) -> QWebEngineProfile:
        if self._profile is not None:
            self._printProfileDetails(self._profile)
            return self._profile

        self._ensure_directories()
        self._profile = QWebEngineProfile("MWVPersistentProfile")
        self._profile.setCachePath(self._CACHE_PATH)
        self._profile.setPersistentStoragePath(self._STORAGE_PATH)
        self._profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self._profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        self._printProfileDetails(self._profile)
        return self._profile

    def _generateWebEngineView(self, parent=None) -> QWebEngineView:
        webEngine: QWebEngineView = QWebEngineView(parent=parent)
        profile: QWebEngineProfile = self._getProfile()
        webPage: QWebEnginePage = QWebEnginePage(profile, webEngine)
        webEngine.setPage(webPage)
        return webEngine

    def _printProfileDetails(self, profile: QWebEngineProfile):
        print("***********************")
        print(f"Storage Name: {profile.storageName()}")
        print(f"Cache Path: {profile.cachePath()}")
        print(f"Storage Path: {profile.persistentStoragePath()}")
        print(f"Cache Type: {profile.httpCacheType()}")
        print(f"Persistent Cookie Policy: {profile.persistentCookiesPolicy()}")
        print(f"Off The Record: {profile.isOffTheRecord()}")
        print("***********************")

    def new_tab(self):
        """Open a new tab in the tab widget."""
        # Create a new WebEngineView for the tab
        browser_view = self._generateWebEngineView()
        browser_view.setUrl(QUrl("https://espotsolutions.com/"))
        self.tabs.addTab(browser_view, "New Tab")
        self.tabs.setCurrentWidget(browser_view)

        # Enable JavaScript and adjust settings for compatibility
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        # Set User-Agent to mimic Chrome (bypasses some stricter CSPs)
        browser_view.page().setWebChannel(QWebChannel(browser_view.page()))
        browser_view.page().profile().setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled,
                                             True)  # Important for media

        def handle_permission_request(origin, feature):
            if feature in [
                QWebEnginePage.Feature.MediaAudioCapture,
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.Feature.MediaAudioVideoCapture
            ]:
                browser_view.page().setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

        browser_view.page().featurePermissionRequested.connect(handle_permission_request)

        # Add the new tab
        index = self.tabs.addTab(browser_view, "New Tab")
        self.tabs.setCurrentIndex(index)

        # Update title when the page is loaded
        browser_view.loadFinished.connect(
            lambda ok, browser_view=browser_view: self.update_tab_title(browser_view, ok)
        )

        # Connect urlChanged signal to update the search bar
        browser_view.urlChanged.connect(self.update_search_bar)

    def update_search_bar(self, url):
        """Update the search bar text with the current URL."""
        self.search_bar.setText(url.toString())

    def update_tab_title(self, browser_view, ok):
        """Update the tab title based on the page title."""
        if ok:
            title = browser_view.page().title()
            truncated_title = title[:15] if title else "Untitled"  # Truncate to 15 characters
            self.tabs.setTabText(self.tabs.indexOf(browser_view), truncated_title)
        else:
            self.tabs.setTabText(self.tabs.indexOf(browser_view), "Loading")

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
            # Improved URL detection pattern
            url_pattern = re.compile(
                r'^(https?://)?'  # Optional protocol
                r'(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})'  # Domain name
                r'(:\d+)?'  # Optional port
                r'(/.*)?$'  # Optional path
            )

            if url_pattern.match(query):
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
            pixmap.fill(Qt.GlobalColor.transparent)
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

    def _ensure_directories(self):
        """Ensure that the cache and storage directories exist."""
        self._CACHE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'EspotBrowser', self.username, 'cache')
        self._STORAGE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'EspotBrowser', self.username, 'storage')
        if not os.path.exists(self._CACHE_PATH):
            os.makedirs(self._CACHE_PATH)
        if not os.path.exists(self._STORAGE_PATH):
            os.makedirs(self._STORAGE_PATH)

    def upload_data_to_cloud(self):
        """Upload cache and storage data to Cloudflare."""
        self._upload_folder_to_cloud(self._CACHE_PATH, f"{self.username}/cache")
        self._upload_folder_to_cloud(self._STORAGE_PATH, f"{self.username}/storage")

    def download_data_from_cloud(self):
        """Download cache and storage data from Cloudflare."""
        self._download_folder_from_cloud(self._CACHE_PATH, f"{self.username}/cache")
        self._download_folder_from_cloud(self._STORAGE_PATH, f"{self.username}/storage")

    def _upload_file(self, file_path, key):
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            self._s3_client.put_object(Bucket=self._bucket_name, Key=key, Body=file_data)
            print(f"Uploaded: {file_path} -> {key}")
        except PermissionError:
            print(f"Permission denied: {file_path}")
        except NoCredentialsError:
            print("AWS credentials not available")
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

    def _upload_folder_to_cloud(self, folder_path, folder_name):
        """Upload a folder to Cloudflare."""
        with ThreadPoolExecutor() as executor:
            futures = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.access(file_path, os.R_OK):  # Ensure readable
                        key = f"{folder_name}/{os.path.relpath(file_path, folder_path)}"
                        futures.append(executor.submit(self._upload_file, file_path, key))
                    else:
                        print(f"Skipping unreadable file: {file_path}")
            for future in futures:
                future.result()

    def _download_file(self, key, file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self._s3_client.download_file(self._bucket_name, key, file_path)
            print(f"Downloaded: {key} -> {file_path}")
        except NoCredentialsError:
            print("AWS credentials not available")
        except Exception as e:
            print(f"Error downloading {key}: {e}")

    def _download_folder_from_cloud(self, folder_path, folder_name):
        """Download a folder from Cloudflare."""
        try:
            response = self._s3_client.list_objects_v2(Bucket=self._bucket_name, Prefix=folder_name)
            if 'Contents' in response:
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for obj in response['Contents']:
                        key = obj['Key']
                        file_path = os.path.join(folder_path, os.path.relpath(key, folder_name))
                        futures.append(executor.submit(self._download_file, key, file_path))
                    for future in futures:
                        future.result()
            else:
                print(f"No data found in Cloudflare for {folder_name}")
        except NoCredentialsError:
            print("AWS credentials not available")
        except Exception as e:
            print(f"Error downloading folder {folder_name}: {e}")

    def clean_data(self):
        """Clear all the browser data like history, cookies, cache, etc."""
        # Close all tabs to release resources
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

        self.new_tab()  # Open a new tab after clearing data
        # Get the default profile
        profile = self._getProfile()

        # Clear Cookies
        if profile.cookieStore():
            profile.cookieStore().deleteAllCookies()

        # Clear Cache
        try:
            profile.clearHttpCache()
        except AttributeError:
            print("clearHttpCache() is not supported in this version of PyQt.")

        # Clear Local Storage
        profile.clearAllVisitedLinks()

        # Delete cache and storage directories
        self._delete_directory(self._CACHE_PATH)
        self._delete_directory(self._STORAGE_PATH)

        self._ensure_directories()
        # Show a confirmation message
        QMessageBox.information(self, "Data Cleared", "All browser data has been successfully cleared.")

    def _delete_directory(self, path):
        """Delete the specified directory and its contents."""
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"Deleted directory: {path}")
            except PermissionError:
                print(f"Permission denied: {path}")
            except Exception as e:
                print(f"Error deleting directory {path}: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    browser = SimpleBrowser()
    browser.show()

    app.exec()
