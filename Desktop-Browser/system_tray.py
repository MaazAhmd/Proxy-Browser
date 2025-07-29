from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject


class SystemTrayManager(QObject):
    """Handles system tray functionality."""
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.tray_icon = None
        
    def init_system_tray(self):
        """Initialize system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.parent_window)
        self.tray_icon.setIcon(self.parent_window.windowIcon())
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show action
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show_from_tray)
        
        # Hide action
        hide_action = tray_menu.addAction("Hide")
        hide_action.triggered.connect(self.parent_window.hide)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def show_from_tray(self):
        """Show window from system tray"""
        self.parent_window.show()
        self.parent_window.raise_()
        self.parent_window.activateWindow()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        # Check if it's a double-click using the enum value property
        if reason.value == QSystemTrayIcon.ActivationReason.DoubleClick.value:
            if self.parent_window.isVisible():
                self.parent_window.hide()
            else:
                self.show_from_tray()
    
    def quit_application(self):
        """Quit the application completely"""
        self.parent_window.force_quit = True
        self.parent_window.close()
        
    def show_message(self, title, message):
        """Show a system tray message"""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
