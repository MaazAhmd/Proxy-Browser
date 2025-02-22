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
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from globals import config

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
        self.username_input = QLineEdit("maaz1")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Password input
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit("1234")
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
        details = self.get_proxy_details(self.username, self.password)
        if details and 'proxy_details' in details and 'content_details' in details:
            proxy_details = details['proxy_details']
            content_details = details['content_details']
            config.PROXY_URL = proxy_details['proxy_url']
            config.PROXY_PORT = proxy_details['proxy_port']
            config.PROXY_USER = proxy_details['proxy_user']
            config.PROXY_PASSWORD = proxy_details['proxy_password']
            config.SYNC_DATA = proxy_details['sync_data']
            config.DEFAULT_URL = content_details['default_url']
            config.CLOSING_DIALOG = content_details['closing_dialog']
            self.disabled_after = proxy_details['disabled_after']
            self.accept()
            self.start_heartbeat()

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
        api_url = "https://proxy-browser-test.onrender.com/proxy/get-proxy"
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
        api_url = "https://proxy-browser-test.onrender.com/heartbeat"
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
