import os
import sys
import requests
from PyQt6.QtWidgets import (
    QLineEdit,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from globals import config
from auth_manager import AuthenticationManager
from ui_components import UIComponents


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
        
        # Initialize authentication manager
        self.auth_manager = AuthenticationManager()
        
        # Update login page content from backend
        self.update_login_page_content()

    def update_login_page_content(self):
        """Fetch and update the login page content from the backend."""
        print("Fetching login page content...")
        try:
            response = requests.get(f"{config.BASE_URL}/get-login-page-content")
            if response.status_code == 200:
                data = response.json()
                content_details = data.get('content_details')
                self.init_ui(
                    content_details.get('logo_url', ''),
                    content_details.get('phone_number', 'Contact: +92 XXX XXXXXXX'),
                    content_details.get('slogan', 'Welcome to Espot Browser'),
                    content_details.get('contact_line', 'For Support Contact:')
                )
            else:
                # Fallback to default content
                print("Login page content not fetched, resetting to default.")
                self.init_ui('', 'Contact: +92 XXX XXXXXXX', 'Welcome to Espot Browser', 'For Support Contact:')
        except requests.RequestException as e:
            print(f"Error fetching login content: {e}")
            # Fallback to default content
            self.init_ui('', 'Contact: +92 XXX XXXXXXX', 'Welcome to Espot Browser', 'For Support Contact:')

    def init_ui(self, logo_url, phone_number, slogan, contact_line):
        """Initialize the UI components with the fetched data."""
        layout = QVBoxLayout()
        
        # Set up assets path
        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, "assets")
        else:
            assets_path = os.path.join(os.path.dirname(__file__), "assets")

        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        
        # Add logo at the top
        self.logo_label = QLabel(self)
        if logo_url:
            try:
                self.logo_pixmap = QPixmap()
                self.logo_pixmap.loadFromData(requests.get(logo_url).content)
                self.logo_pixmap = self.logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(self.logo_pixmap)
            except:
                # Fallback to local logo
                self.logo_pixmap = QPixmap(os.path.join(assets_path, "logo.png"))
                self.logo_pixmap = self.logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(self.logo_pixmap)
        else:
            # Use local logo
            self.logo_pixmap = QPixmap(os.path.join(assets_path, "logo.png"))
            self.logo_pixmap = self.logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(self.logo_pixmap)
            
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)
        
        # Add slogan
        self.tagline_label = QLabel(f"{slogan}")
        self.tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.tagline_label)
        
        # Add phone number
        self.phone_label = QLabel(phone_number)
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
        
        # Contact label
        self.contact_label = QLabel(f"{contact_line} {phone_number}")
        self.contact_label.setCursor(Qt.CursorShape.IBeamCursor)
        self.contact_label.setObjectName("contactLabel")
        self.contact_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.contact_label)
        
        self.setLayout(layout)

        # Apply CSS styling
        self.setStyleSheet(UIComponents.get_login_dialog_stylesheet())

    def login(self):
        """Handle login process."""
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        
        # Get proxy details
        details = self.auth_manager.get_proxy_details(self.username, self.password)
        if not details:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            return
        # print("Proxy details fetched successfully:", details)
        if details and 'proxy_details' in details and 'content_details' in details:
            proxy_details = details['proxy_details']
            content_details = details['content_details']
            
            # Set primary proxy configuration values
            config.PROXY_URL = proxy_details.get('proxy_url')
            config.PROXY_PORT = proxy_details.get('proxy_port')
            config.PROXY_USER = proxy_details.get('proxy_user')
            config.PROXY_PASSWORD = proxy_details.get('proxy_password')
            
            # Set backup proxy configuration values if available
            if 'proxy2_details' in details:
                proxy2_details = details['proxy2_details']
                config.BACKUP_PROXY_URL = proxy2_details.get('proxy_url')
                config.BACKUP_PROXY_PORT = proxy2_details.get('proxy_port')
                config.BACKUP_PROXY_USER = proxy2_details.get('proxy_user')
                config.BACKUP_PROXY_PASSWORD = proxy2_details.get('proxy_password')
            else:
                # Clear backup proxy if not provided
                config.BACKUP_PROXY_URL = None
                config.BACKUP_PROXY_PORT = None
                config.BACKUP_PROXY_USER = None
                config.BACKUP_PROXY_PASSWORD = None
            
            # Set special proxy (Proxy 3) configuration values if available
            if 'proxy3_details' in details:
                proxy3_details = details['proxy3_details']
                config.SPECIAL_PROXY_URL = proxy3_details.get('proxy_url')
                config.SPECIAL_PROXY_PORT = proxy3_details.get('proxy_port')
                config.SPECIAL_PROXY_USER = proxy3_details.get('proxy_user')
                config.SPECIAL_PROXY_PASSWORD = proxy3_details.get('proxy_password')
            else:
                # Clear special proxy if not provided
                config.SPECIAL_PROXY_URL = None
                config.SPECIAL_PROXY_PORT = None
                config.SPECIAL_PROXY_USER = None
                config.SPECIAL_PROXY_PASSWORD = None
            
            # Set special backup proxy (Proxy 4) configuration values if available
            if 'proxy4_details' in details:
                proxy4_details = details['proxy4_details']
                config.SPECIAL_BACKUP_PROXY_URL = proxy4_details.get('proxy_url')
                config.SPECIAL_BACKUP_PROXY_PORT = proxy4_details.get('proxy_port')
                config.SPECIAL_BACKUP_PROXY_USER = proxy4_details.get('proxy_user')
                config.SPECIAL_BACKUP_PROXY_PASSWORD = proxy4_details.get('proxy_password')
            else:
                # Clear special backup proxy if not provided
                config.SPECIAL_BACKUP_PROXY_URL = None
                config.SPECIAL_BACKUP_PROXY_PORT = None
                config.SPECIAL_BACKUP_PROXY_USER = None
                config.SPECIAL_BACKUP_PROXY_PASSWORD = None
            
            # Set special websites array if available
            if 'websites' in details:
                config.SPECIAL_WEBSITES = details['websites'] if isinstance(details['websites'], list) else []
            else:
                config.SPECIAL_WEBSITES = []
            
            config.DEFAULT_URL = content_details.get('default_url')
            config.SYNC_DATA = content_details.get('sync_data', False)
            self.disabled_after = proxy_details.get('disabled_after')
            
            # Check if device is trusted
            if not self.auth_manager.is_device_trusted(self.username):
                if details.get("requires_2fa"):
                    success, message = self.auth_manager.send_2fa(self.username)
                    if success:
                        if self.verify_2fa():
                            self.auth_manager.remember_device(self.username)
                        else:
                            QMessageBox.warning(self, "2FA Failed", "Two-factor authentication failed.")
                            return
                    else:
                        QMessageBox.warning(self, "2FA Error", f"Could not send 2FA: {message}")
                        return
            
            # Start heartbeat
            self.auth_manager.start_heartbeat(self.username)
            self.accept()
        else:
            print("Details: ", details)
            QMessageBox.warning(self, "Login Failed", "Session Limit reached. Please try again in a few minutes.")

    def verify_2fa(self):
        """Show OTP input dialog and verify it"""
        otp_dialog = TwoFADialog(self.username, self.auth_manager)
        return otp_dialog.exec() == QDialog.DialogCode.Accepted

    def stop_heartbeat(self):
        """Stop the heartbeat timer."""
        if hasattr(self, 'auth_manager'):
            self.auth_manager.stop_heartbeat(self.username)


class TwoFADialog(QDialog):
    def __init__(self, username, auth_manager):
        super().__init__()
        self.username = username
        self.auth_manager = auth_manager

        self.setWindowTitle("Two-Factor Authentication")
        self.setGeometry(600, 300, 300, 150)

        self.layout = QVBoxLayout()

        self.otp_input = QLineEdit(self)
        self.otp_input.setPlaceholderText("Enter OTP Code")
        self.layout.addWidget(self.otp_input)

        self.verify_button = QPushButton("Verify", self)
        self.verify_button.clicked.connect(self.verify_otp)
        self.layout.addWidget(self.verify_button)

        self.setLayout(self.layout)

    def verify_otp(self):
        """Verify the OTP code."""
        otp_code = self.otp_input.text().strip()
        if not otp_code:
            QMessageBox.warning(self, "Error", "Please enter the OTP code.")
            return

        success, message = self.auth_manager.verify_2fa(self.username, otp_code)
        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Verification Failed", message or "Invalid OTP code.")
