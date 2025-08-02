import requests
import time
from urllib.parse import urlparse
from PyQt6.QtNetwork import QNetworkProxy
from globals import config
from PyQt6.QtWebEngineCore import QWebEngineProfile


class ProxyRouter:
    """Advanced proxy router that handles different proxy types based on URL patterns."""
    
    def __init__(self):
        self.test_urls = [
            "https://www.google.com",
            "https://httpbin.org/ip",
            "https://www.cloudflare.com"
        ]
        self.current_proxy_type = None
        self.timeout = 10  # 10 seconds timeout
        self.proxy_dict = None  # Store current proxy configuration for requests
        
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
            print(f"Checking proxy type for URL: {domain} ({config.SPECIAL_WEBSITES})")
            
            # Check if domain is in the special websites list
            for special_website in config.SPECIAL_WEBSITES:
                special_website = special_website.lower().strip()
                if domain in special_website:
                    return "special"

            return "general"
            
        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
            return "general"
    
    def test_connection(self, proxy_type=None):
        """Test if specified proxy type works by pinging test websites."""
        if proxy_type:
            test_proxy_type = proxy_type
        else:
            test_proxy_type = self.current_proxy_type
            
        print(f"Testing {test_proxy_type} proxy connection...")
        
        for url in self.test_urls:
            try:
                # Use the stored proxy configuration
                response = requests.get(url, timeout=self.timeout, proxies=self.proxy_dict)
                if response.status_code == 200:
                    print(f"✓ Connection test passed with {url}")
                    return True
            except Exception as e:
                print(f"✗ Failed to connect to {url}: {e}")
                continue
        
        print(f"✗ All connection tests failed for {test_proxy_type} proxy")
        return False
    
    def set_proxy(self, proxy_type):
        """Set up proxy configuration based on type."""
        proxy_url = None
        proxy_port = None
        proxy_user = None
        proxy_password = None
        
        if proxy_type == "primary":
            proxy_url = config.PROXY_URL
            proxy_port = config.PROXY_PORT
            proxy_user = config.PROXY_USER
            proxy_password = config.PROXY_PASSWORD
        elif proxy_type == "backup":
            proxy_url = config.BACKUP_PROXY_URL
            proxy_port = config.BACKUP_PROXY_PORT
            proxy_user = config.BACKUP_PROXY_USER
            proxy_password = config.BACKUP_PROXY_PASSWORD
        elif proxy_type == "special":
            proxy_url = config.SPECIAL_PROXY_URL
            proxy_port = config.SPECIAL_PROXY_PORT
            proxy_user = config.SPECIAL_PROXY_USER
            proxy_password = config.SPECIAL_PROXY_PASSWORD
        elif proxy_type == "special_backup":
            proxy_url = config.SPECIAL_BACKUP_PROXY_URL
            proxy_port = config.SPECIAL_BACKUP_PROXY_PORT
            proxy_user = config.SPECIAL_BACKUP_PROXY_USER
            proxy_password = config.SPECIAL_BACKUP_PROXY_PASSWORD
        else:
            print(f"Unknown proxy type: {proxy_type}")
            return False
            
        if not proxy_url or not proxy_port:
            print(f"No {proxy_type} proxy configuration available")
            return False
            
        try:
            # Set up Qt proxy
            proxy = QNetworkProxy()
            proxy.setType(QNetworkProxy.ProxyType.HttpProxy)
            proxy.setHostName(proxy_url)
            proxy.setPort(int(proxy_port))
            
            if proxy_user and proxy_password:
                proxy.setUser(proxy_user)
                proxy.setPassword(proxy_password)
                
            QNetworkProxy.setApplicationProxy(proxy)
            
            # Also set up requests proxy for testing
            self.proxy_dict = {
                'http': f'http://{proxy_user}:{proxy_password}@{proxy_url}:{proxy_port}' if proxy_user else f'http://{proxy_url}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_password}@{proxy_url}:{proxy_port}' if proxy_user else f'http://{proxy_url}:{proxy_port}'
            }
            
            # Update requests session with proxy
            requests.packages.urllib3.disable_warnings()
            requests.adapters.DEFAULT_RETRIES = 1
            
            self.current_proxy_type = proxy_type
            print(f"Successfully set {proxy_type} proxy: {proxy_url}:{proxy_port}")
            
            return True
            
        except Exception as e:
            print(f"Error setting {proxy_type} proxy: {e}")
            return False
    
    def set_proxy_for_url(self, url):
        """Set the appropriate proxy based on the URL and return success status."""
        required_proxy_type = self.get_proxy_type_for_url(url)
        print(f"Setting proxy for {url}: {required_proxy_type}")
        
        # Check if we're already using the correct proxy type
        if required_proxy_type == "special":
            # Check if we're already using special or special_backup proxy
            if self.current_proxy_type in ["special", "special_backup"]:
                print(f"✓ Already using {self.current_proxy_type} proxy for special websites")
                return True
            return self._set_special_proxy()
        else:
            # Check if we're already using primary or backup proxy
            if self.current_proxy_type in ["primary", "backup"]:
                print(f"✓ Already using {self.current_proxy_type} proxy for general browsing")
                return True
            return self._set_general_proxy()
    
    def _set_general_proxy(self):
        """Set general proxy (primary with backup fallback)."""
        # Try primary proxy first
        if self.set_proxy("primary"):
            # Skip connection test if we're switching from backup to primary
            # (assume it works to avoid delay)
            print("✓ Primary proxy set for general browsing")
            return True
        
        print("Primary proxy failed, trying backup...")
        
        # If primary fails, try backup
        if config.BACKUP_PROXY_URL and self.set_proxy("backup"):
            print("✓ Switched to backup proxy for general browsing")
            return True
        
        print("✗ Both general proxies failed!")
        return False
    
    def _set_special_proxy(self):
        """Set special proxy (special with special_backup fallback)."""
        # Try special proxy first
        if config.SPECIAL_PROXY_URL and self.set_proxy("special"):
            # Skip connection test to avoid delay
            print("✓ Special proxy set for special websites")
            return True
        
        print("Special proxy failed, trying special backup...")
        
        # If special fails, try special backup
        if config.SPECIAL_BACKUP_PROXY_URL and self.set_proxy("special_backup"):
            print("✓ Switched to special backup proxy for special websites")
            return True
        
        print("✗ Both special proxies failed!")
        return False
    
    def can_access_url(self, url):
        """Check if URL can be accessed with available proxies."""
        required_proxy_type = self.get_proxy_type_for_url(url)
        
        if required_proxy_type == "special":
            # Check if we have at least one special proxy configured
            return (config.SPECIAL_PROXY_URL and config.SPECIAL_PROXY_PORT) or \
                   (config.SPECIAL_BACKUP_PROXY_URL and config.SPECIAL_BACKUP_PROXY_PORT)
        else:
            # Check if we have at least one general proxy configured
            return (config.PROXY_URL and config.PROXY_PORT) or \
                   (config.BACKUP_PROXY_URL and config.BACKUP_PROXY_PORT)
    
    def get_proxy_info_for_url(self, url):
        """Get information about which proxy type should be used for a URL."""
        required_proxy_type = self.get_proxy_type_for_url(url)
        
        info = {
            'url': url,
            'required_proxy_type': required_proxy_type,
            'is_special_website': required_proxy_type == "special",
            'can_access': self.can_access_url(url)
        }
        
        if required_proxy_type == "special":
            info['available_proxies'] = []
            if config.SPECIAL_PROXY_URL:
                info['available_proxies'].append('special')
            if config.SPECIAL_BACKUP_PROXY_URL:
                info['available_proxies'].append('special_backup')
        else:
            info['available_proxies'] = []
            if config.PROXY_URL:
                info['available_proxies'].append('primary')
            if config.BACKUP_PROXY_URL:
                info['available_proxies'].append('backup')
        
        return info
    
    def get_current_proxy_type(self):
        """Return current proxy type."""
        return self.current_proxy_type
    
    def print_configuration_summary(self):
        """Print a summary of all proxy configurations."""
        print("\n" + "="*60)
        print("PROXY CONFIGURATION SUMMARY")
        print("="*60)
        
        print("\nGeneral Proxies (for regular browsing):")
        print(f"  Primary: {config.PROXY_URL}:{config.PROXY_PORT}" if config.PROXY_URL else "  Primary: Not configured")
        print(f"  Backup:  {config.BACKUP_PROXY_URL}:{config.BACKUP_PROXY_PORT}" if config.BACKUP_PROXY_URL else "  Backup:  Not configured")
        
        print("\nSpecial Proxies (for special websites only):")
        print(f"  Special: {config.SPECIAL_PROXY_URL}:{config.SPECIAL_PROXY_PORT}" if config.SPECIAL_PROXY_URL else "  Special: Not configured")
        print(f"  Special Backup: {config.SPECIAL_BACKUP_PROXY_URL}:{config.SPECIAL_BACKUP_PROXY_PORT}" if config.SPECIAL_BACKUP_PROXY_URL else "  Special Backup: Not configured")
        
        print(f"\nSpecial Websites ({len(config.SPECIAL_WEBSITES)} configured):")
        if config.SPECIAL_WEBSITES:
            for website in config.SPECIAL_WEBSITES:
                print(f"  - {website}")
        else:
            print("  None configured")
        
        print("="*60 + "\n")
