import os
import sys
import subprocess
import json
import boto3
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from globals import config


class UpdateManager:
    """Handles application updates and version checking."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self._s3_client = boto3.client(
            's3',
            aws_access_key_id=config.CLOUDFLARE_ACCESS_KEY,
            aws_secret_access_key=config.CLOUDFLARE_SECRET_KEY,
            endpoint_url=config.CLOUDFLARE_ENDPOINT_URL
        )
        self.update_dialog = None
        self.update_thread = None

    def check_for_updates(self):
        """Check if there's a newer version available."""
        try:
            response = self._s3_client.get_object(Bucket=config.VERSION_BUCKET_NAME, Key=config.CLOUD_VERSION_FILE)
            version_data = response['Body'].read().decode('utf-8')
            version_info = json.loads(version_data)
            latest_version = version_info.get('version', 0)
            
            if latest_version and float(latest_version) != config.CURRENT_VERSION:
                return latest_version
            return None
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None

    def download_and_install_update(self):
        """Download and install the latest update."""
        # Create and show the update dialog
        self.update_dialog = UpdateDialog(self.parent)
        self.update_dialog.show()

        # Start the update download in a separate thread
        self.update_thread = UpdateThread(self._s3_client)
        self.update_thread.download_progress.connect(self.update_dialog.update_progress)
        self.update_thread.download_complete.connect(self.run_installer)
        self.update_thread.start()

    def cancel_update(self):
        """Gracefully stops the update process and exits the application."""
        if hasattr(self, "update_thread") and self.update_thread.isRunning():
            self.update_thread.terminate()
            self.update_thread.wait()

        if hasattr(self, "update_dialog") and self.update_dialog.isVisible():
            self.update_dialog.close()

        sys.exit(0)

    def run_installer(self, installer_path):
        """Runs the installer and closes the update dialog."""
        self.update_dialog.user_closed = True
        self.update_dialog.close()
        print("Download complete! Installing the update...")

        # Run the installer silently
        subprocess.Popen([installer_path, "/silent"], shell=True)
        sys.exit(0)


class UpdateThread(QThread):
    """Background thread for downloading updates to prevent UI freezing."""
    download_complete = pyqtSignal(str)
    download_progress = pyqtSignal(int)

    def __init__(self, s3_client):
        super().__init__()
        self.s3_client = s3_client

    def run(self):
        try:
            installer_path = os.path.join(os.getcwd(), config.INSTALLER_FILE)
            self.bytes_transferred = 0

            self.s3_client.download_file(
                config.VERSION_BUCKET_NAME,
                config.INSTALLER_FILE,
                installer_path,
                Callback=self.progress_callback
            )
            self.download_complete.emit(installer_path)
        except Exception as e:
            print(f"Error downloading the update: {e}")

    def get_total_size(self, bucket_name, key):
        response = self.s3_client.head_object(Bucket=bucket_name, Key=key)
        return response['ContentLength']

    def progress_callback(self, bytes_received):
        """Handles the progress updates."""
        self.bytes_transferred += bytes_received
        total_size = self.get_total_size(config.VERSION_BUCKET_NAME, config.INSTALLER_FILE)
        progress = int((self.bytes_transferred / total_size) * 100)
        self.download_progress.emit(progress)


class UpdateDialog(QDialog):
    """Custom dialog to show update progress with a progress bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Updating")
        self.setMinimumSize(400, 100)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout(self)
        self.label = QLabel("Downloading update...", self)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.user_closed = False

    def update_progress(self, progress):
        """Update the progress bar and label."""
        self.progress_bar.setValue(progress)

    def closeEvent(self, event):
        """Handle window close event to cancel update."""
        if not self.user_closed:
            if self.parent():
                print("Cancelling update...")
                self.parent().cancel_update()
        event.accept()
