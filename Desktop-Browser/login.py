import os
import sys
import requests
import jwt
import datetime
from PyQt6.QtWidgets import (
    QLineEdit,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt, QTimer, QCoreApplication
from PyQt6.QtGui import QIcon, QPixmap
from globals import config
import hashlib
import uuid
import smtplib
import random
from email.mime.text import MIMEText

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
        self.device_id = self.get_device_id()
        self.update_login_page_content()

    def update_login_page_content(self):
        """Fetch and update the login page content from the backend."""
        print("Fetching login page content...")
        try:
            response = requests.get(f"{config.BASE_URL}/get-login-page-content")
            if response.status_code == 200:
                data = response.json()
                if data["status"] == 1:
                    content_details = data["content_details"]
                    logo_url = content_details["logo_url"]
                    phone_number = content_details["phone_number"]
                    slogan = content_details["slogan"]
                    contact_url = content_details["contact_line"]
                    # Initialize UI components after fetching data
                    self.init_ui(logo_url, phone_number, slogan, contact_url)
                else:
                    QMessageBox.warning(self, "Error", "Failed to fetch login page content.")
                    self.reject()  # Close the dialog if data fetch fails
                    QCoreApplication.exit()
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch login page content.")
                self.reject()  # Close the dialog if data fetch fails
                QCoreApplication.exit()
        except requests.RequestException as e:
            print("Error fetching login page content:", e)
            QMessageBox.warning(self, "Error", "Failed to fetch login page content.")
            self.reject()  # Close the dialog if data fetch fails
            QCoreApplication.exit()

    def init_ui(self, logo_url, phone_number, slogan, contact_line):
        """Initialize the UI components with the fetched data."""

        layout = QVBoxLayout()
        if hasattr(sys, '_MEIPASS'):
            assets_path = os.path.join(sys._MEIPASS, 'assets')
        else:
            assets_path = os.path.join(os.path.dirname(__file__), 'assets')

        self.setWindowIcon(QIcon(os.path.join(assets_path, "logo.png")))
        # Add logo at the top
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap()
        self.logo_pixmap.loadFromData(requests.get(logo_url).content)
        self.logo_pixmap = self.logo_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(self.logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)
        self.tagline_label = QLabel(f"{slogan}")
        self.tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.tagline_label)
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
        self.contact_label = QLabel(f"{contact_line} {phone_number}")
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


    def get_device_id(self):
        return hashlib.sha256(uuid.getnode().to_bytes(6, 'big')).hexdigest()


    def login(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        # Fetch proxy details (your existing logic)
        details = self.get_proxy_details(self.username, self.password)

        if details and 'proxy_details' in details and 'content_details' in details:
            proxy_details = details['proxy_details']
            content_details = details['content_details']

            # Check if 2FA is required
            if details.get("requires_2fa") and not self.is_device_trusted():
                if not self.send_2fa(self.username):
                    return  # Stop login if 2FA fails

            # Save proxy details (existing logic)
            config.PROXY_URL = proxy_details['proxy_url']
            config.PROXY_PORT = proxy_details['proxy_port']
            config.PROXY_USER = proxy_details['proxy_user']
            config.PROXY_PASSWORD = proxy_details['proxy_password']
            config.SYNC_DATA = proxy_details['sync_data']
            config.DEFAULT_URL = content_details['default_url']
            self.disabled_after = proxy_details['disabled_after']

            # Remember this device after successful login
            self.remember_device()

            # Accept login and start heartbeat
            self.accept()
            self.start_heartbeat()

        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")

    def is_device_trusted(self):
        response = requests.post(
            f"{config.BASE_URL}/proxy/check-device",
            json={"username": self.username, "device_id": self.device_id}
        )
        return response.status_code == 200 and response.json().get("trusted", False)

    def send_2fa(self, username):
        """Request server to send a 2FA code"""
        response = requests.post(f"{config.BASE_URL}/proxy/send-2fa", json={"username": username})
        data = response.json()

        if data["status"] == 1:
            QMessageBox.information(None, "2FA Code Sent", "Please check your email for the 2FA code.")
            return self.verify_2fa(username)
        else:
            QMessageBox.critical(None, "Error", data["error_message"])

    def verify_2fa(self, username):
        """Show OTP input dialog and verify it"""
        otp_dialog = TwoFADialog(username, self.device_id)
        if otp_dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(None, "Success", "2FA Verified!")
            return True
        else:
            QMessageBox.critical(None, "Failed", "Invalid OTP or verification error.")
            return False

    def remember_device(self):
        requests.post(
            f"{config.BASE_URL}/proxy/remember-device",
            json={"username": self.username, "device_id": self.device_id}
        )



    def generate_jwt(self):
        """Generate a JWT token."""
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
        return token

    def get_proxy_details(self, username, password):
        """Call the API to get proxy details."""
        api_url = f"{config.BASE_URL}/proxy/get-proxy"
        token = self.generate_jwt()
        headers = {'x-access-token': token}
        try:
            response = requests.post(api_url, json={"username": username, "password": password}, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 1:
                    return data
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
        api_url = f"{config.BASE_URL}/heartbeat"
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

class TwoFADialog(QDialog):
    def __init__(self, username, device_id):
        super().__init__()
        self.username = username
        self.device_id = device_id

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
        otp_code = self.otp_input.text()
        response = requests.post(f"{config.BASE_URL}/proxy/verify-2fa", json={"username": self.username, "otp_code": otp_code, "device_id": self.device_id})
        data = response.json()

        if data["status"] == 1:
            self.accept()  # Close dialog and return success
        else:
            QMessageBox.warning(self, "Error", data["error_message"])
