from browser import Browser
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

APP_KEY = "espot-browser-beta-key"  # Make this unique for your app

class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading...")
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(300, 100)

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
