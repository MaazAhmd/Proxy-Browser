class Config:
    PROXY_URL = None
    PROXY_PORT = None
    PROXY_USER = None
    PROXY_PASSWORD = None
    
    # Backup proxy configuration
    PROXY2_URL = None
    PROXY2_PORT = None
    PROXY2_USER = None
    PROXY2_PASSWORD = None
    
    # Special website proxy configuration
    PROXY3_URL = None
    PROXY3_PORT = None
    PROXY3_USER = None
    PROXY3_PASSWORD = None
    
    # Backup for special website proxy
    PROXY4_URL = None
    PROXY4_PORT = None
    PROXY4_USER = None
    PROXY4_PASSWORD = None
    
    # Special websites array
    SPECIAL_WEBSITES = []
    
    DEFAULT_URL = None
    SYNC_DATA = None
    PROFILE = None
    BASE_URL = "http://localhost:5000/"
    COOKIE_BUCKET_NAME = "espot-browser-beta-cookies-data"
    VERSION_BUCKET_NAME = "espot-browser-beta-version"
    CLOUDFLARE_ACCESS_KEY = "6cf9c0a917cc03005d53cbd9c29255db"
    CLOUDFLARE_SECRET_KEY = "62aada3122ab29154eb5490204b62ddec5aba43e47d60267fabaee3ae447ea60"
    CLOUDFLARE_ENDPOINT_URL = "https://3e16a6f90ade2025b173edd3439f41f3.r2.cloudflarestorage.com"
    SECRET_KEY = 'QR2vZ7ocC7JkF0b02Kd7a5slN92MYgvd'
    CURRENT_VERSION = 5.1
    CLOUD_VERSION_FILE = "version.json"
    INSTALLER_FILE = "Setup - Espot Browser Beta.exe"
    
    # Proxy testing configuration
    TEST_URLS = ["http://httpbin.org/ip", "http://icanhazip.com"]
    PROXY_TIMEOUT = 10
config = Config()