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
    QWidget
)
from PyQt6.QtCore import Qt, QTimer, QCoreApplication
from PyQt6.QtGui import QIcon, QPixmap
from globals import config
import hashlib
import uuid
import subprocess
import platform

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
            print(response.status_code)
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
                    QMessageBox.warning(self, "Error", "Failed to fetch login page content, due to server error.")
                    self.reject()  # Close the dialog if data fetch fails
                    QCoreApplication.exit()
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch login page content due to server error.")
                self.reject()  # Close the dialog if data fetch fails
                QCoreApplication.exit()

        except requests.Timeout:
            print("Request timed out.")
            QMessageBox.warning(self, "Timeout", "Request timed out while fetching login page content.")
            self.reject()
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
        self.username_input = QLineEdit("arthur")
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

        
        # Construct the WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number.lstrip('+')}"  # wa.me requires numbers without '+'

        # Create the label with hyperlink
        self.contact_label = QLabel(f'{contact_line} <a href="{whatsapp_url}">{phone_number}</a>')
        self.contact_label.setTextFormat(Qt.TextFormat.RichText)
        self.contact_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.contact_label.setOpenExternalLinks(True)  # Open the link in browser
        self.contact_label.setObjectName("contactLabel")

        # Add to layout
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


    # def get_device_id(self):
    #     return hashlib.sha256(uuid.getnode().to_bytes(6, 'big')).hexdigest()


    def login(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        # Fetch proxy details (your existing logic)
        details = self.get_proxy_details(self.username, self.password)
        if not details:
            return

        if details and 'proxy_details' in details and 'content_details' in details:
            proxy_details = details['proxy_details']
            content_details = details['content_details']
            proxy2_details = details.get('proxy2_details')  # Get backup proxy details
            proxy3_details = details.get('proxy3_details')  # Get special website proxy details
            proxy4_details = details.get('proxy4_details')  # Get backup for special website proxy
            websites = details.get('websites', [])  # Get special websites array

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

            # Save backup proxy details if available
            if proxy2_details:
                config.PROXY2_URL = proxy2_details['proxy_url']
                config.PROXY2_PORT = proxy2_details['proxy_port']
                config.PROXY2_USER = proxy2_details['proxy_user']
                config.PROXY2_PASSWORD = proxy2_details['proxy_password']

            # Save special website proxy details if available
            if proxy3_details:
                config.PROXY3_URL = proxy3_details['proxy_url']
                config.PROXY3_PORT = proxy3_details['proxy_port']
                config.PROXY3_USER = proxy3_details['proxy_user']
                config.PROXY3_PASSWORD = proxy3_details['proxy_password']

            # Save backup for special website proxy if available
            if proxy4_details:
                config.PROXY4_URL = proxy4_details['proxy_url']
                config.PROXY4_PORT = proxy4_details['proxy_port']
                config.PROXY4_USER = proxy4_details['proxy_user']
                config.PROXY4_PASSWORD = proxy4_details['proxy_password']

            # Save special websites array
            config.SPECIAL_WEBSITES = websites
            print("websites:", config.SPECIAL_WEBSITES)
            # Test primary proxy and switch to backup if needed
            if not self.test_proxy_connection():
                if proxy2_details and self.switch_to_backup_proxy():
                    print("Switched to backup proxy due to primary proxy failure")
                else:
                    QMessageBox.warning(self, "Connection Failed", "Both primary and backup proxies are unavailable.")
                    return

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

    def test_proxy_connection(self):
        """Test if the current proxy configuration is working."""
        if not config.PROXY_URL or not config.PROXY_PORT:
            return False
            
        proxy_dict = {
            "http": f"http://{config.PROXY_USER}:{config.PROXY_PASSWORD}@{config.PROXY_URL}:{config.PROXY_PORT}",
            "https": f"http://{config.PROXY_USER}:{config.PROXY_PASSWORD}@{config.PROXY_URL}:{config.PROXY_PORT}"
        }
        
        for url in config.TEST_URLS:
            try:
                # Use the stored proxy configuration
                response = requests.get(url, timeout=config.PROXY_TIMEOUT, proxies=proxy_dict)
                if response.status_code == 200:
                    print(f"✓ Connection test passed with {url}")
                    return True
            except Exception as e:
                print(f"✗ Failed to connect to {url}: {e}")
                continue
        
        print("✗ Primary proxy connection test failed")
        return False

    def switch_to_backup_proxy(self):
        """Switch to backup proxy configuration and test it."""
        if not config.PROXY2_URL or not config.PROXY2_PORT:
            print("✗ No backup proxy configured")
            return False
        
        # Test backup proxy before switching
        backup_proxy_dict = {
            "http": f"http://{config.PROXY2_USER}:{config.PROXY2_PASSWORD}@{config.PROXY2_URL}:{config.PROXY2_PORT}",
            "https": f"http://{config.PROXY2_USER}:{config.PROXY2_PASSWORD}@{config.PROXY2_URL}:{config.PROXY2_PORT}"
        }
        
        for url in config.TEST_URLS:
            try:
                response = requests.get(url, timeout=config.PROXY_TIMEOUT, proxies=backup_proxy_dict)
                if response.status_code == 200:
                    print(f"✓ Backup proxy connection test passed with {url}")
                    # Switch to backup proxy
                    config.PROXY_URL = config.PROXY2_URL
                    config.PROXY_PORT = config.PROXY2_PORT
                    config.PROXY_USER = config.PROXY2_USER
                    config.PROXY_PASSWORD = config.PROXY2_PASSWORD
                    return True
            except Exception as e:
                print(f"✗ Failed to connect to {url} with backup proxy: {e}")
                continue
        
        print("✗ Backup proxy connection test failed")
        return False

    def test_special_proxy_connection(self):
        """Test if proxy3 (special website proxy) is working."""
        if not config.PROXY3_URL or not config.PROXY3_PORT:
            return False
            
        proxy_dict = {
            "http": f"http://{config.PROXY3_USER}:{config.PROXY3_PASSWORD}@{config.PROXY3_URL}:{config.PROXY3_PORT}",
            "https": f"http://{config.PROXY3_USER}:{config.PROXY3_PASSWORD}@{config.PROXY3_URL}:{config.PROXY3_PORT}"
        }
        
        for url in config.TEST_URLS:
            try:
                response = requests.get(url, timeout=config.PROXY_TIMEOUT, proxies=proxy_dict)
                if response.status_code == 200:
                    print(f"✓ Special proxy (proxy3) connection test passed with {url}")
                    return True
            except Exception as e:
                print(f"✗ Failed to connect to {url} with proxy3: {e}")
                continue
        
        print("✗ Special proxy (proxy3) connection test failed")
        return False

    def switch_to_proxy4(self):
        """Switch to proxy4 (backup for special website proxy) and test it."""
        if not config.PROXY4_URL or not config.PROXY4_PORT:
            print("✗ No proxy4 configured")
            return False
        
        # Test proxy4 before using it
        proxy4_dict = {
            "http": f"http://{config.PROXY4_USER}:{config.PROXY4_PASSWORD}@{config.PROXY4_URL}:{config.PROXY4_PORT}",
            "https": f"http://{config.PROXY4_USER}:{config.PROXY4_PASSWORD}@{config.PROXY4_URL}:{config.PROXY4_PORT}"
        }
        
        for url in config.TEST_URLS:
            try:
                response = requests.get(url, timeout=config.PROXY_TIMEOUT, proxies=proxy4_dict)
                if response.status_code == 200:
                    print(f"✓ Proxy4 connection test passed with {url}")
                    return True
            except Exception as e:
                print(f"✗ Failed to connect to {url} with proxy4: {e}")
                continue
        
        print("✗ Proxy4 connection test failed")
        return False

    def is_special_website(self, url):
        """Check if the given URL belongs to a special website."""
        if not config.SPECIAL_WEBSITES:
            return False
        
        # Extract domain from URL
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower()
            if not domain:
                # If netloc is empty, might be a relative URL or just domain
                domain = url.lower()
        except:
            domain = url.lower()
        
        # Check if domain matches any special website
        for special_website in config.SPECIAL_WEBSITES:
            if special_website.lower() in domain:
                return True
        return False

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


    def get_device_id(self):
        """Generate a unique device ID based on hardware."""
        try:
            if platform.system() == "Windows":
                # print("Windows Platform Detected")
                result = subprocess.run(
                    ['powershell', '-Command', 'Get-CimInstance -Class Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID'],
                    capture_output=True, text=True, shell=True
                )

                lines = result.stdout.strip().split('\n')
                
                # Try to find the UUID in any line
                for i, line in enumerate(lines):
                    cleaned_line = line.strip()
                    if cleaned_line and cleaned_line not in ['UUID', '']:
                        print("Returning ", cleaned_line)
                        return cleaned_line
                    
                print("Returning None")
                return None
                
        except Exception as e:
            print(f"Error getting hardware ID: {e}")
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
            response = requests.post(api_url, json={"username": self.username, "status": login_status, 'device_id': self.get_device_id()}, headers=headers)
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
        except Exception as e:
            print("An error occurred while sending Heartbeat, probably network issue.")
            self.heartbeat_timer.stop()
            QMessageBox.warning(self, "Connection Error", "Unable to connect to the Server. Please fix your internet connection and Try Again.")
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
