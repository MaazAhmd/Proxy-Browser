from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl
from globals import config


class WebEngineManager:
    """Manages web engine views, pages, and settings."""
    
    @staticmethod
    def create_web_engine_view(parent=None):
        """Create a properly configured QWebEngineView."""
        web_engine = QWebEngineView(parent=parent)
        profile = config.PROFILE if config.PROFILE else QWebEngineProfile.defaultProfile()
        web_page = QWebEnginePage(profile, web_engine)
        web_engine.setPage(web_page)
        return web_engine
    
    @staticmethod
    def configure_web_engine_settings(browser_view):
        """Configure web engine settings for compatibility."""
        # Enable JavaScript and adjust settings for compatibility
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        
        # Set User-Agent
        browser_view.page().profile().setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        )
        
        # Set up web channel
        browser_view.page().setWebChannel(QWebChannel(browser_view.page()))
    
    @staticmethod
    def setup_permission_handler(browser_view):
        """Set up permission request handler for media access."""
        def handle_permission_request(origin, feature):
            if feature in [
                QWebEnginePage.Feature.MediaAudioCapture,
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.Feature.MediaAudioVideoCapture
            ]:
                browser_view.page().setFeaturePermission(
                    origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
                )
        
        browser_view.page().featurePermissionRequested.connect(handle_permission_request)
    
    @staticmethod
    def cleanup_web_engine_pages(tabs):
        """Ensure all QWebEnginePage instances are properly deleted."""
        for i in range(tabs.count()):
            browser_view = tabs.widget(i)
            if browser_view:
                browser_view.setPage(None)
                browser_view.deleteLater()
    
    @staticmethod
    def set_default_user_agent():
        """Set a custom user-agent string for the browser."""
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
