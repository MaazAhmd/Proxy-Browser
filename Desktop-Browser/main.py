from browser import Browser
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Step 1: Show loader before creating Browser
    loader = LoadingDialog()   # Create loader dialog (QDialog)
    loader.show()
    app.processEvents()        # Ensure it renders immediately

    # Step 2: Create and initialize Browser
    browser = Browser()

    # Step 3: Hide loader and show Browser
    loader.close()
    browser.show()

    sys.exit(app.exec())
