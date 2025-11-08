import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--no-sandbox "
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp "
    "--webrtc-hide-local-ips-with-mdns "
    "--webrtc-multiple-routes-enabled=false "
    "--webrtc-nonproxied-udp-enabled=false "
    "--disable-webrtc"
)

from browser import Browser
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
import traceback

# print("requests.DEFAULT_CA_BUNDLE_PATH:", requests.utils.DEFAULT_CA_BUNDLE_PATH)
APP_KEY = "espot-browser-beta-key"  # Make this unique for your app

class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading...")
        self.setModal(True)

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint)
        # Optional: just set an initial size instead of fixing
        self.resize(300, 100)

        layout = QVBoxLayout(self)
        label = QLabel("Starting Espot Browser...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


def setup_single_instance(browser):
    """Sets up the single-instance server and activation."""
    server = QLocalServer()
    server.removeServer(APP_KEY)  # Clean stale socket if crashed before
    server.listen(APP_KEY)

    def handle_new_connection():
        socket = server.nextPendingConnection()
        if socket and socket.waitForReadyRead(100):
            message = socket.readAll().data().decode()
            if message == "ACTIVATE":
                browser.show_from_tray()
        socket.disconnectFromServer()

    server.newConnection.connect(handle_new_connection)
    return server


def is_another_instance_running():
    """Check if another instance is running and activate it."""
    socket = QLocalSocket()
    socket.connectToServer(APP_KEY)
    if socket.waitForConnected(100):
        socket.write(b"ACTIVATE")
        socket.flush()
        socket.waitForBytesWritten(100)
        socket.disconnectFromServer()
        return True
    return False



# def handle_exception(exc_type, exc_value, exc_traceback):
#     # Don’t catch KeyboardInterrupt (so Ctrl+C still works in terminal)
#     if issubclass(exc_type, KeyboardInterrupt):
#         sys.__excepthook__(exc_type, exc_value, exc_traceback)
#         return

#     # Format traceback
#     tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
#     print("Unhandled exception:", tb_text)  # still log to console

#     # Show in a QMessageBox
#     if QApplication.instance():
#         msg = QMessageBox()
#         msg.setIcon(QMessageBox.Icon.Critical)
#         msg.setWindowTitle("Application Error")
#         msg.setText("An unexpected error occurred.")
#         msg.setInformativeText(str(exc_value))
#         msg.setDetailedText(tb_text)
#         msg.exec()   # or msg.open() for non-blocking
#     else:
#         # No QApplication yet → fallback to stderr
#         sys.__excepthook__(exc_type, exc_value, exc_traceback)

# sys.excepthook = handle_exception


if __name__ == "__main__":
    if is_another_instance_running():
        print("Another instance detected. Activating...")
        sys.exit(0)

    app = QApplication(sys.argv)

    # Loader (if you have one)
    loader = LoadingDialog()
    loader.show()
    app.processEvents()

    # Browser
    browser = Browser()

    # Keep server alive for activation
    server = setup_single_instance(browser)

    loader.close()
    browser.show()

    sys.exit(app.exec())
