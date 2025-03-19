import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWebEngineCore import QWebEngineProfile

class Cookies:
    def __init__(self, profile):
        self.profile = profile
        self._CACHE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'Browser', 'cache')
        self._STORAGE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'Browser', 'storage')
        self._ensure_directories()
        self._getProfile()

    def _ensure_directories(self):
        """Ensure that the cache and storage directories exist."""
        if not os.path.exists(self._CACHE_PATH):
            os.makedirs(self._CACHE_PATH)
        if not os.path.exists(self._STORAGE_PATH):
            os.makedirs(self._STORAGE_PATH)


    def _getProfile(self) -> QWebEngineProfile:
        if self.profile is not None:
            self._printProfileDetails()

        self._ensure_directories()
        self.profile = QWebEngineProfile("MWVPersistentProfile")
        self.profile.setCachePath(self._CACHE_PATH)
        self.profile.setPersistentStoragePath(self._STORAGE_PATH)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        self._printProfileDetails()

    def _printProfileDetails(self):
        print("***********************")
        print(f"Storage Name: {self.profile.storageName()}")
        print(f"Cache Path: {self.profile.cachePath()}")
        print(f"Storage Path: {self.profile.persistentStoragePath()}")
        print(f"Cache Type: {self.profile.httpCacheType()}")
        print(f"Persistent Cookie Policy: {self.profile.persistentCookiesPolicy()}")
        print(f"Off The Record: {self.profile.isOffTheRecord()}")
        print("***********************")