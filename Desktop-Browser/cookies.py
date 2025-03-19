import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWebEngineCore import QWebEngineProfile

class Cookies:
    def __init__(self):
        self._CACHE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'Browser', 'cache')
        self._STORAGE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'Browser', 'storage')
        self.profile = self._getProfile()

    def _ensure_directories(self):
        """Ensure that the cache and storage directories exist."""
        if not os.path.exists(self._CACHE_PATH):
            os.makedirs(self._CACHE_PATH)
        if not os.path.exists(self._STORAGE_PATH):
            os.makedirs(self._STORAGE_PATH)

    def _getProfile(self) -> QWebEngineProfile:
        self._ensure_directories()
        profile = QWebEngineProfile("MWVPersistentProfile")
        profile.setCachePath(self._CACHE_PATH)
        profile.setPersistentStoragePath(self._STORAGE_PATH)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        self._printProfileDetails(profile)
        return profile

    def _printProfileDetails(self, profile):
        print("***********************")
        print(f"Storage Name: {profile.storageName()}")
        print(f"Cache Path: {profile.cachePath()}")
        print(f"Storage Path: {profile.persistentStoragePath()}")
        print(f"Cache Type: {profile.httpCacheType()}")
        print(f"Persistent Cookie Policy: {profile.persistentCookiesPolicy()}")
        print(f"Off The Record: {profile.isOffTheRecord()}")
        print("***********************")