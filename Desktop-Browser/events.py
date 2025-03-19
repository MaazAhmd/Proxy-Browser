from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

DEFAULT_URL = "https://my.qt.io/"

class Events:
    tabs = None
    profile = None
    def __init__(self, profile):
        self.profile = profile
    def new_tab(self):
        """Open a new tab in the tab widget."""
        # Create a new WebEngineView for the tab
        browser_view = self._generateWebEngineView()
        browser_view.setUrl(QUrl(DEFAULT_URL))
        self.tabs.addTab(browser_view, "New Tab")
        self.tabs.setCurrentWidget(browser_view)

        # Enable JavaScript and adjust settings for compatibility
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        # Set User-Agent to mimic Chrome (bypasses some stricter CSPs)
        browser_view.page().setWebChannel(QWebChannel(browser_view.page()))
        browser_view.page().profile().setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        )
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        browser_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled,
                                             True)  # Important for media

        def handle_permission_request(origin, feature):
            if feature in [
                QWebEnginePage.Feature.MediaAudioCapture,
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.Feature.MediaAudioVideoCapture
            ]:
                browser_view.page().setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

        browser_view.page().featurePermissionRequested.connect(handle_permission_request)

        # Add the new tab
        index = self.tabs.addTab(browser_view, "New Tab")
        self.tabs.setCurrentIndex(index)

        # Update title when the page is loaded
        browser_view.loadFinished.connect(
            lambda ok, browser=browser_view: self.update_tab_title(browser_view, ok)
        )

        # Connect urlChanged signal to update the search bar

    def _generateWebEngineView(self, parent=None) -> QWebEngineView:
        webEngine: QWebEngineView = QWebEngineView(parent=parent)
        profile: QWebEngineProfile = self.profile if self.profile else QWebEngineProfile.defaultProfile()
        webPage: QWebEnginePage = QWebEnginePage(profile, webEngine)
        webEngine.setPage(webPage)
        return webEngine

    def update_tab_title(self, browser_view, ok):
        """Update the tab title based on the page title."""
        if ok:
            title = browser_view.page().title()
            truncated_title = title[:15] if title else "Untitled"  # Truncate to 15 characters
            self.tabs.setTabText(self.tabs.indexOf(browser_view), truncated_title)
        else:
            self.tabs.setTabText(self.tabs.indexOf(browser_view), "Loading")

    def reload_page(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.reload()


    def get_current_browser(self):
        """Return the current browser (QWebEngineView) from the active tab."""
        current_index = self.tabs.currentIndex()
        if current_index != -1:
            return self.tabs.widget(current_index)
        return None

    def get_svg_icon(self, svg_content):
        """Convert SVG content to a QIcon."""
        try:
            svg_renderer = QSvgRenderer(svg_content.encode("utf-8"))
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            svg_renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        except Exception as e:
            print(f"Error creating SVG icon: {e}")
            return QIcon()

    def reload_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.86 0 7 3.14 7 7 0 .78-.13 1.52-.36 2.22l1.46 1.46C20.68 15.31 21 14.19 21 13c0-5-4-9-9-9zm-7.64.78L2.93 3.36C2.32 4.52 2 5.73 2 7c0 5 4 9 9 9v3l4-4-4-4v3c-3.86 0-7-3.14-7-7 0-1.11.24-2.16.64-3.22z"/></svg>"""
