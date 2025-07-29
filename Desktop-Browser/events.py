from PyQt6.QtCore import QUrl
from globals import config
from web_engine_manager import WebEngineManager
from ui_components import IconProvider


class Events:
    """Handles browser events and navigation."""
    
    def __init__(self):
        self.tabs = None
        self.search_bar = None

    def new_tab(self):
        """Open a new tab in the tab widget."""
        # Create a new WebEngineView for the tab
        browser_view = WebEngineManager.create_web_engine_view()
        browser_view.setUrl(QUrl(config.DEFAULT_URL if config.DEFAULT_URL else "https://espotsolutions.com/"))
        
        # Configure the browser view
        WebEngineManager.configure_web_engine_settings(browser_view)
        WebEngineManager.setup_permission_handler(browser_view)

        # Add the new tab
        index = self.tabs.addTab(browser_view, "New Tab")
        self.tabs.setCurrentIndex(index)

        # Update title when the page is loaded
        browser_view.loadFinished.connect(
            lambda ok, browser_view=browser_view: self.update_tab_title(browser_view, ok)
        )

        # Connect urlChanged signal to update the search bar
        browser_view.urlChanged.connect(self.update_search_bar)

        # Handle new window requests (open in new tab)
        def handle_new_window(window_type):
            new_view = WebEngineManager.create_web_engine_view()
            WebEngineManager.configure_web_engine_settings(new_view)
            WebEngineManager.setup_permission_handler(new_view)
            
            # Add tab
            index = self.tabs.addTab(new_view, "New Tab")
            self.tabs.setCurrentIndex(index)
            
            # Connect signals
            new_view.loadFinished.connect(
                lambda ok, new_view=new_view: self.update_tab_title(new_view, ok)
            )
            new_view.urlChanged.connect(self.update_search_bar)
            
            return new_view

        # Override createWindow method to handle new window requests
        browser_view.createWindow = handle_new_window

    def update_search_bar(self, url):
        """Update the search bar text with the current URL."""
        if self.search_bar:
            self.search_bar.setText(url.toString())

    def update_tab_title(self, browser_view, ok):
        """Update the tab title based on the page title."""
        if ok:
            title = browser_view.page().title()
            if title:
                # Find the tab index and update its title
                for i in range(self.tabs.count()):
                    if self.tabs.widget(i) == browser_view:
                        self.tabs.setTabText(i, title[:20] + "..." if len(title) > 20 else title)
                        break
        else:
            # Find the tab index and set error title
            for i in range(self.tabs.count()):
                if self.tabs.widget(i) == browser_view:
                    self.tabs.setTabText(i, "Error")
                    break

    def close_tab(self, index):
        """Close the tab at the given index."""
        if self.tabs.count() > 1:
            widget = self.tabs.widget(index)
            self.tabs.removeTab(index)
            if widget:
                widget.deleteLater()
        else:
            # If it's the last tab, create a new one
            self.tabs.removeTab(index)
            self.new_tab()

    def go_back(self):
        """Navigate back in the current tab."""
        current_browser = self.get_current_browser()
        if current_browser and current_browser.history().canGoBack():
            current_browser.back()

    def go_forward(self):
        """Navigate forward in the current tab."""
        current_browser = self.get_current_browser()
        if current_browser and current_browser.history().canGoForward():
            current_browser.forward()

    def reload_page(self):
        """Reload the current page."""
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.reload()

    def open_url(self):
        """Open URL from search bar in current tab."""
        if not self.search_bar:
            return
            
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
                
                current_browser.setUrl(QUrl(query))

    def get_current_browser(self):
        """Return the current browser (QWebEngineView) from the active tab."""
        current_index = self.tabs.currentIndex()
        if current_index != -1:
            return self.tabs.widget(current_index)
        return None

    # Icon methods for backward compatibility
    def back_icon_svg(self):
        return IconProvider.back_icon_svg()

    def forward_icon_svg(self):
        return IconProvider.forward_icon_svg()

    def reload_icon_svg(self):
        return IconProvider.reload_icon_svg()

    def new_tab_icon_svg(self):
        return IconProvider.new_tab_icon_svg()

    def clean_icon_svg(self):
        return IconProvider.clean_icon_svg()
