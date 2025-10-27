from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QMessageBox
from globals import config
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from urllib.parse import urlparse

class Events:
    tabs = None
    search_bar = None
    browser = None  # Reference to browser instance
    
    def __init__(self):
        # Initialize proxy tracking
        self.current_proxy_type = None
        
    def get_proxy_type_for_url(self, url):
        """Determine which proxy type to use based on URL."""
        if not url:
            return "general"  # Default to general proxy
            
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check if domain is in the special websites list
            for special_website in config.SPECIAL_WEBSITES:
                special_website = special_website.lower().strip()
                if domain in special_website:
                    return "special"

            return "general"
            
        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
            return "general"
    
    def can_access_url(self, url):
        """Check if URL can be accessed with available proxies."""
        required_proxy_type = self.get_proxy_type_for_url(url)
        
        if required_proxy_type == "special":
            # Check if we have at least one special proxy configured
            return (config.PROXY3_URL and config.PROXY3_PORT) or \
                   (config.PROXY4_URL and config.PROXY4_PORT)
        else:
            # Check if we have at least one general proxy configured
            return (config.PROXY_URL and config.PROXY_PORT) or \
                   (config.PROXY2_URL and config.PROXY2_PORT)
    
    def _check_and_set_proxy_for_url(self, url):
        """Check if URL can be accessed and set appropriate proxy."""
        # Check if URL can be accessed with available proxies
        if not self.can_access_url(url):
            required_proxy_type = self.get_proxy_type_for_url(url)
            if required_proxy_type == "special":
                print(f"❌ Cannot access {url}")
                print("   This website requires special proxy access, but no special proxies are configured.")
                print("   Please contact your administrator.")
            else:
                print(f"❌ Cannot access {url}")
                print("   No general proxy configuration available.")
            return False
        
        # Set appropriate proxy for this URL
        success = self.set_proxy_for_url(url)
        if not success:
            required_proxy_type = self.get_proxy_type_for_url(url)
            if required_proxy_type == "special":
                print(f"❌ Failed to set up special proxy for {url}")
                print("   All special proxies are non-functional.")
            else:
                print(f"❌ Failed to set up general proxy for {url}")
                print("   All general proxies are non-functional.")
            return False
            
        return True
    
    def set_proxy_for_url(self, url):
        """Set the appropriate proxy based on the URL and return success status."""
        required_proxy_type = self.get_proxy_type_for_url(url)
        print(f"Setting proxy for {url}: {required_proxy_type}")
        
        # Check if we're already using the correct proxy type
        if required_proxy_type == "special":
            # Check if we're already using special proxy
            if self.current_proxy_type in ["special", "special_backup"]:
                print(f"✓ Already using {self.current_proxy_type} proxy for special websites")
                return True
            return self._set_special_proxy()
        else:
            # Check if we're already using general proxy
            if self.current_proxy_type in ["primary", "backup"]:
                print(f"✓ Already using {self.current_proxy_type} proxy for general browsing")
                return True
            return self._set_general_proxy()
    
    def _set_general_proxy(self):
        """Set general proxy (primary with backup fallback)."""
        # Try primary proxy first
        if self.browser and self.browser.set_proxy():
            self.current_proxy_type = "primary"
            print("✓ Primary proxy set for general browsing")
            return True
        
        print("Primary proxy failed, trying backup...")
        
        # If primary fails, try backup
        if config.PROXY2_URL and self.browser:
            if self.browser.set_proxy(config.PROXY2_URL, config.PROXY2_PORT, config.PROXY2_USER, config.PROXY2_PASSWORD):
                self.current_proxy_type = "backup"
                print("✓ Switched to backup proxy for general browsing")
                return True
        
        print("✗ Both general proxies failed!")
        return False
    
    def _set_special_proxy(self):
        """Set special proxy (special with special_backup fallback)."""
        # Try special proxy first (proxy3)
        if config.PROXY3_URL and self.browser:
            if self.browser.set_proxy(config.PROXY3_URL, config.PROXY3_PORT, config.PROXY3_USER, config.PROXY3_PASSWORD):
                self.current_proxy_type = "special"
                print("✓ Special proxy set for special websites")
                return True
        
        print("Special proxy failed, trying special backup...")
        
        # If special fails, try special backup (proxy4)
        if config.PROXY4_URL and self.browser:
            if self.browser.set_proxy(config.PROXY4_URL, config.PROXY4_PORT, config.PROXY4_USER, config.PROXY4_PASSWORD):
                self.current_proxy_type = "special_backup"
                print("✓ Switched to special backup proxy for special websites")
                return True
        
        print("✗ Both special proxies failed!")
        return False
    
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
            lambda ok, browser_view=browser_view: self.update_tab_title(browser_view, ok)
        )

        # Connect urlChanged signal to update the search bar and handle special websites
        browser_view.urlChanged.connect(lambda url, view=browser_view: self.handle_url_change(url, view))

        # Handle new window requests (open in new tab)
        def handle_new_window(window_type):
            new_view = self._generateWebEngineView()
            # Configure new tab with same settings
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
            new_view.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            
            new_view.page().profile().setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
            )
            
            new_view.page().featurePermissionRequested.connect(handle_permission_request)
            
            # Add tab
            index = self.tabs.addTab(new_view, "New Tab")
            self.tabs.setCurrentIndex(index)
            
            # Connect signals
            new_view.loadFinished.connect(
                lambda ok, view=new_view: self.update_tab_title(view, ok)
            )
            new_view.urlChanged.connect(lambda url, view=new_view: self.handle_url_change(url, view))
            
            # Override createWindow for the new view too
            new_view.createWindow = lambda wt: handle_new_window(wt)
            
            return new_view

        # Override createWindow method to handle new window requests
        browser_view.createWindow = handle_new_window

    def _generateWebEngineView(self, parent=None) -> QWebEngineView:
        webEngine: QWebEngineView = QWebEngineView(parent=parent)
        profile: QWebEngineProfile = config.PROFILE if config.PROFILE else QWebEngineProfile.defaultProfile()
        webPage: QWebEnginePage = QWebEnginePage(profile, webEngine)
        webEngine.setPage(webPage)
        
        # Connect download handler to this tab's profile
        if self.browser and hasattr(self.browser, 'handle_download'):
            profile.downloadRequested.connect(self.browser.handle_download)
        
        return webEngine

    def update_search_bar(self, url):
        """Update the search bar text with the current URL."""
        self.search_bar.setText(url.toString())

    def handle_url_change(self, url, browser_view):
        """Handle URL changes and check for special websites."""
        url_string = url.toString()
        
        # Update search bar
        if browser_view == self.get_current_browser():
            self.update_search_bar(url)

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
            current_browser = self.get_current_browser()
            if current_browser:
                # Add protocol if missing
                if not query.startswith(('http://', 'https://')):
                    if '.' in query and ' ' not in query:
                        query = 'https://' + query
                    else:
                        # Search query
                        query = f'https://www.google.com/search?q={query}'
                
                # Check and set appropriate proxy before navigation
                if not self._check_and_set_proxy_for_url(query):
                    QMessageBox.warning(None, "Access Denied", "This website cannot be accessed. Required proxy servers are unavailable.")
                    return  # Don't navigate if proxy setup failed
                
                current_browser.setUrl(QUrl(query))

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
        return """<svg viewBox="0 -0.5 17 17" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" class="si-glyph si-glyph-brush-1" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <title>880</title> <defs> </defs> <g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"> <g transform="translate(1.000000, 0.000000)" fill="#000000"> <path d="M0.056,8.306 L4.364,4.955 L11.067,11.66 L7.717,15.968 C7.717,15.968 7.761,14.914 6.28,14.531 C4.89,14.172 4.648,12.243 3.437,11.843 C2.226,11.443 2.011,10.601 1.451,9.698 C0.891,8.795 0.056,8.306 0.056,8.306 L0.056,8.306 Z" class="si-glyph-fill"> </path> <path d="M12.981,7.83 L11.835,6.684 C13.676,5.081 15.114,3.782 15.372,3.522 C16.167,2.729 16.165,1.444 15.372,0.651 C14.579,-0.143 13.292,-0.143 12.499,0.649 C12.241,0.909 10.94,2.346 9.339,4.189 L8.193,3.043 C7.664,2.514 6.806,2.513 6.277,3.042 L5.32,3.999 L12.024,10.704 L12.982,9.745 C13.51,9.217 13.51,8.358 12.981,7.83 L12.981,7.83 Z M13.246,2.777 C12.863,2.394 12.863,1.775 13.246,1.393 C13.627,1.011 14.246,1.012 14.629,1.394 C15.012,1.777 15.012,2.396 14.629,2.777 C14.247,3.16 13.629,3.16 13.246,2.777 L13.246,2.777 Z" class="si-glyph-fill"> </path> </g> </g> </g></svg>"""
    
    def restart_icon_svg(self):
        return """<svg xmlns="http://www.w3.org/2000/svg" x="0px" y="0px" width="100" height="100" viewBox="0 0 64 64">
        <path d="M58,32c0,14.359-11.641,26-26,26S6,46.359,6,32C6,17.641,17.641,6,32,6S58,17.641,58,32z M45.581,23.785	c-1.845-2.961-4.678-5.273-7.941-6.478l-1.404,3.746c2.416,0.931,4.501,2.685,5.835,4.888c1.348,2.2,1.873,4.846,1.57,7.394	c-0.305,2.544-1.501,4.95-3.319,6.747c-1.814,1.799-4.221,2.973-6.745,3.261c-2.532,0.311-5.136-0.242-7.295-1.55	c-2.165-1.297-3.882-3.329-4.769-5.669c-0.903-2.326-0.991-4.98-0.245-7.35c0.48-1.56,1.321-3.001,2.415-4.212l3.145,3.493	l2.75-12.047l-12.281,1.462l3.057,3.395c-1.732,1.844-3.042,4.08-3.751,6.511c-1.017,3.433-0.833,7.176,0.502,10.485	c1.318,3.313,3.775,6.125,6.837,7.899c3.059,1.793,6.717,2.5,10.2,2.024c3.501-0.449,6.815-2.125,9.27-4.632	c2.466-2.498,4.068-5.84,4.438-9.33C48.226,30.353,47.446,26.742,45.581,23.785z"></path>
        </svg>"""
