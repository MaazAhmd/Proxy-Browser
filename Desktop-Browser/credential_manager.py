from PyQt6.QtCore import QSettings
from cryptography.fernet import Fernet
import os

class CredentialManager:
    def __init__(self):
        self.settings = QSettings("MyCompany", "MyApp")
        
        # Store the key in a user-writable location (AppData / ~/.myapp)
        base_dir = os.path.expanduser("~/.myapp")   # cross-platform
        os.makedirs(base_dir, exist_ok=True)
        self.key_file = os.path.join(base_dir, "secret.key")

        # Load or generate encryption key
        if not os.path.exists(self.key_file):
            with open(self.key_file, "wb") as f:
                f.write(Fernet.generate_key())

        with open(self.key_file, "rb") as f:
            key = f.read()
        self.cipher = Fernet(key)

    def save_credentials(self, username, password):
        enc_username = self.cipher.encrypt(username.encode()).decode()
        enc_password = self.cipher.encrypt(password.encode()).decode()
        self.settings.setValue("username", enc_username)
        self.settings.setValue("password", enc_password)

    def load_credentials(self):
        enc_username = self.settings.value("username", "")
        enc_password = self.settings.value("password", "")
        if enc_username and enc_password:
            try:
                username = self.cipher.decrypt(enc_username.encode()).decode()
                password = self.cipher.decrypt(enc_password.encode()).decode()
                return username, password
            except Exception:
                return "", ""
        return "", ""

    def clear_credentials(self):
        self.settings.remove("username")
        self.settings.remove("password")
