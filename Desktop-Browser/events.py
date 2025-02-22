import re
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from globals import config
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView

class Events:
    tabs = None
    search_bar = None
    def new_tab(self):
        """Open a new tab in the tab widget."""
        # Create a new WebEngineView for the tab
        browser_view = self._generateWebEngineView()
        browser_view.setUrl(QUrl(config.DEFAULT_URL if config.DEFAULT_URL else "https://espotsolutions.com/"))
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
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
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
            lambda ok, browser_view=browser_view: self.update_tab_title(browser_view, ok)
        )

        # Connect urlChanged signal to update the search bar
        browser_view.urlChanged.connect(self.update_search_bar)

    def _generateWebEngineView(self, parent=None) -> QWebEngineView:
        webEngine: QWebEngineView = QWebEngineView(parent=parent)
        profile: QWebEngineProfile = config.PROFILE if config.PROFILE else QWebEngineProfile.defaultProfile()
        webPage: QWebEnginePage = QWebEnginePage(profile, webEngine)
        webEngine.setPage(webPage)
        return webEngine

    def update_search_bar(self, url):
        """Update the search bar text with the current URL."""
        self.search_bar.setText(url.toString())

    def update_tab_title(self, browser_view, ok):
        """Update the tab title based on the page title."""
        if ok:
            title = browser_view.page().title()
            truncated_title = title[:15] if title else "Untitled"  # Truncate to 15 characters
            self.tabs.setTabText(self.tabs.indexOf(browser_view), truncated_title)
        else:
            self.tabs.setTabText(self.tabs.indexOf(browser_view), "Loading")

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.tabs.count() > 1:  # Ensure at least one tab remains open
            self.tabs.removeTab(index)

    def go_back(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.back()

    def go_forward(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.forward()

    def reload_page(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.reload()

    def open_url(self):
        query = self.search_bar.text().strip()
        if query:
            # Improved URL detection pattern
            url_pattern = re.compile(
                r'^(https?://)?'  # Optional protocol
                r'(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})'  # Domain name
                r'(:\d+)?'  # Optional port
                r'(/.*)?$'  # Optional path
            )

            if url_pattern.match(query):
                # If it doesn't have 'http://' or 'https://', add 'http://'
                if not query.startswith(('http://', 'https://')):
                    query = 'http://' + query
                # Open the URL in the current tab
                current_browser = self.get_current_browser()
                if current_browser:
                    current_browser.setUrl(QUrl(query))  # Open the URL directly
            else:
                # If not a URL, treat it as a search query
                search_url = f"https://www.google.com/search?q={query}"
                current_browser = self.get_current_browser()
                if current_browser:
                    current_browser.setUrl(QUrl(search_url))  # Perform Google search

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

    def back_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H19v-2z"/></svg>"""

    def forward_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M5 13h11.17l-5.59 5.59L13 20l8-8-8-8-1.41 1.41L16.17 11H5v2z"/></svg>"""

    def reload_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.86 0 7 3.14 7 7 0 .78-.13 1.52-.36 2.22l1.46 1.46C20.68 15.31 21 14.19 21 13c0-5-4-9-9-9zm-7.64.78L2.93 3.36C2.32 4.52 2 5.73 2 7c0 5 4 9 9 9v3l4-4-4-4v3c-3.86 0-7-3.14-7-7 0-1.11.24-2.16.64-3.22z"/></svg>"""

    def new_tab_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4v8H4v2h8v8h2v-8h8v-2h-8V4h-2z"/></svg>"""

    def clean_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4v2H6v12h12V6h-6V4h-2v2h-4V4h-2zm6 14H6v-2h12v2z"/></svg>"""
