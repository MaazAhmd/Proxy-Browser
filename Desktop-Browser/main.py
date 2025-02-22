from PyQt6.QtWidgets import QApplication
from browser import Browser
import sys


if __name__ == "__main__":
    app = QApplication(sys.argv)

    browser = Browser()
    browser.show()

    app.exec()
