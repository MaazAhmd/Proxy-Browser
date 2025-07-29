import threading
from PyQt6.QtCore import QTimer, QDateTime, QCoreApplication
from PyQt6.QtWidgets import QMessageBox


class SessionManager:
    """Handles session management, timers, and expiration."""
    
    def __init__(self, parent_window, login_dialog):
        self.parent_window = parent_window
        self.login_dialog = login_dialog
        self.session_timer = None
        self.disabled_after = None
        
    def start_session_timer(self):
        """Start a timer to check session expiration every minute."""
        self.session_timer = QTimer(self.parent_window)
        self.session_timer.timeout.connect(self.check_session_expiration)
        self.session_timer.start(10000)  # Check every 10 seconds

    def stop_session_timer(self):
        """Stop the session timer."""
        if self.session_timer:
            self.session_timer.stop()

    def set_session_expiration(self, disabled_after):
        """Set the session expiration time."""
        self.disabled_after = disabled_after

    def check_session_expiration(self):
        """Check if the session has expired or is about to expire."""
        current_time = QDateTime.currentDateTime()
        expiration_time = QDateTime.fromString(self.disabled_after, "ddd, dd MMM yyyy HH:mm:ss 'GMT'")

        if self.disabled_after:
            time_left = current_time.secsTo(expiration_time)

            if time_left <= 0:
                self.session_timer.stop()
                QMessageBox.warning(self.parent_window, "Session Expired", "Your session has expired.")
                self.parent_window.close()
                self.show_login_dialog()
            elif time_left <= 300:
                QMessageBox.warning(self.parent_window, "Session Expiring Soon",
                                    "Your session will expire in 5 minutes. Please save your work.")

    def show_login_dialog(self):
        """Show the login dialog."""
        from login import LoginDialog
        login_dialog = LoginDialog()
        if login_dialog.exec():
            # Handle successful login
            pass

    def cleanup_on_close(self):
        """Cleanup session when closing application."""
        self.login_dialog.stop_heartbeat()
        self.stop_session_timer()
        
    def handle_data_upload_on_close(self, cookies_manager, config):
        """Handle data upload in background when closing."""
        if config.SYNC_DATA:
            # Start the upload in a separate thread
            upload_thread = threading.Thread(target=cookies_manager.upload_data_to_cloud)
            upload_thread.start()

            # Use a QTimer to check if the upload is complete and close the application
            upload_timer = QTimer(self.parent_window)
            upload_timer.timeout.connect(lambda: self.check_upload_complete(upload_thread, upload_timer))
            upload_timer.start(1000)
            
            return True  # Indicates that close should be ignored initially
        return False

    def check_upload_complete(self, upload_thread, upload_timer):
        """Check if the upload thread is complete."""
        if not upload_thread.is_alive():
            upload_timer.stop()
            QCoreApplication.exit()
