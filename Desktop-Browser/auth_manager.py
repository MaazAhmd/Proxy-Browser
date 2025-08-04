import hashlib
import uuid
import datetime
import jwt
import requests
from PyQt6.QtCore import QTimer
from globals import config
import subprocess
import platform

class AuthenticationManager:
    """Handles authentication, JWT tokens, and heartbeat."""
    
    def __init__(self):
        self.heartbeat_timer = None
        
    def get_device_id(self):
        """Generate a unique device ID based on hardware."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID'], 
                                    capture_output=True, text=True, shell=True)

                lines = result.stdout.strip().split('\n')
                
                # Try to find the UUID in any line
                for i, line in enumerate(lines):
                    cleaned_line = line.strip()
                    if cleaned_line and cleaned_line not in ['UUID', '']:
                        return cleaned_line
                return None
                
        except Exception as e:
            print(f"Error getting hardware ID: {e}")
            return None

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
            response = requests.post(api_url, headers=headers, json={
                'username': username,
                'password': password,
                'device_id': self.get_device_id()
            })
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def is_device_trusted(self, username):
        """Check if the current device is trusted."""
        device_id = self.get_device_id()
        response = requests.post(
            f"{config.BASE_URL}/proxy/check-device",
            json={"username": username, "device_id": device_id}
        )
        return response.status_code == 200 and response.json().get("trusted", False)

    def send_2fa(self, username):
        """Request server to send a 2FA code."""
        response = requests.post(f"{config.BASE_URL}/proxy/send-2fa", json={"username": username})
        data = response.json()
        return data["status"] == 1, data.get("message", "")

    def verify_2fa(self, username, otp_code):
        """Verify the 2FA code."""
        device_id = self.get_device_id()
        response = requests.post(f"{config.BASE_URL}/proxy/verify-2fa", json={
            "username": username,
            "otp": otp_code,
            "device_id": device_id
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == 1, data.get("message", "")
        return False, "Verification failed"

    def remember_device(self, username):
        """Mark the current device as trusted."""
        device_id = self.get_device_id()
        requests.post(
            f"{config.BASE_URL}/proxy/remember-device",
            json={"username": username, "device_id": device_id}
        )

    def start_heartbeat(self, username):
        """Start a timer to send heartbeat signals to the server."""
        self.username = username
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(lambda: self.send_heartbeat(username, True))
        self.heartbeat_timer.start(60000)  # Send heartbeat every 60 seconds
        self.send_heartbeat(username, True)  # Send initial heartbeat

    def stop_heartbeat(self, username=None):
        """Stop the heartbeat timer and send a final signal to the server."""
        if self.heartbeat_timer:
            self.heartbeat_timer.stop()
            self.heartbeat_timer = None
        
        if username or hasattr(self, 'username'):
            self.send_heartbeat(username or self.username, False)

    def send_heartbeat(self, username, login_status):
        """Send a heartbeat signal to the server."""
        api_url = f"{config.BASE_URL}/heartbeat"
        headers = {'x-access-token': self.generate_jwt()}
        
        try:
            requests.post(api_url, headers=headers, json={
                'username': username,
                'status': login_status,
                'device_id': self.get_device_id()
            }, timeout=10)
        except requests.RequestException as e:
            print(f"Heartbeat failed: {e}")
