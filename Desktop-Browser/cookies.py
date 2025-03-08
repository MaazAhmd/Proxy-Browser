import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWebEngineCore import QWebEngineProfile
from globals import config

class Cookies:
    def __init__(self, username, s3_client):
        self.username = username
        self._s3_client = s3_client
        self._CACHE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'EspotBrowser', self.username, 'cache')
        self._STORAGE_PATH = os.path.join(os.getenv('USERPROFILE'), 'AppData', 'Roaming', 'EspotBrowser', self.username, 'storage')
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure that the cache and storage directories exist."""
        if not os.path.exists(self._CACHE_PATH):
            os.makedirs(self._CACHE_PATH)
        if not os.path.exists(self._STORAGE_PATH):
            os.makedirs(self._STORAGE_PATH)

    def upload_data_to_cloud(self):
        """Upload cache and storage data to Cloudflare."""
        self._upload_folder_to_cloud(self._CACHE_PATH, f"{self.username}/cache")
        self._upload_folder_to_cloud(self._STORAGE_PATH, f"{self.username}/storage")
        print("Data uploaded successfully")

    def download_data_from_cloud(self):
        """Download cache and storage data from Cloudflare."""
        self._download_folder_from_cloud(self._CACHE_PATH, f"{self.username}/cache")
        self._download_folder_from_cloud(self._STORAGE_PATH, f"{self.username}/storage")
        print("Data downloaded successfully")

    def _upload_file(self, file_path, key):
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            self._s3_client.put_object(Bucket=config.COOKIE_BUCKET_NAME, Key=key, Body=file_data)
            print(f"Uploaded: {file_path} -> {key}")
        except PermissionError:
            print(f"Permission denied: {file_path}")
        except NoCredentialsError:
            print("AWS credentials not available")
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

    def _upload_folder_to_cloud(self, folder_path, folder_name):
        """Upload a folder to Cloudflare."""
        with ThreadPoolExecutor() as executor:
            futures = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.access(file_path, os.R_OK):  # Ensure readable
                        key = f"{folder_name}/{os.path.relpath(file_path, folder_path)}"
                        futures.append(executor.submit(self._upload_file, file_path, key))
                    else:
                        print(f"Skipping unreadable file: {file_path}")
            for future in futures:
                future.result()

    def _download_file(self, key, file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self._s3_client.download_file(config.COOKIE_BUCKET_NAME, key, file_path)
            print(f"Downloaded: {key} -> {file_path}")
        except NoCredentialsError:
            print("AWS credentials not available")
        except Exception as e:
            print(f"Error downloading {key}: {e}")

    def _download_folder_from_cloud(self, folder_path, folder_name):
        """Download a folder from Cloudflare."""
        try:
            response = self._s3_client.list_objects_v2(Bucket=config.COOKIE_BUCKET_NAME, Prefix=folder_name)
            if 'Contents' in response:
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for obj in response['Contents']:
                        key = obj['Key']
                        file_path = os.path.join(folder_path, os.path.relpath(key, folder_name))
                        futures.append(executor.submit(self._download_file, key, file_path))
                    for future in futures:
                        future.result()
            else:
                print(f"No data found in Cloudflare for {folder_name}")
        except NoCredentialsError:
            print("AWS credentials not available")
        except Exception as e:
            print(f"Error downloading folder {folder_name}: {e}")

    def clean_data(self, tabs, new_tab, profile):
        """Clear all the browser data like history, cookies, cache, etc."""
        # Close all tabs to release resources
        while tabs.count() > 0:
            tabs.removeTab(0)

        new_tab()  # Open a new tab after clearing data

        # Clear Cookies
        if profile.cookieStore():
            profile.cookieStore().deleteAllCookies()

        # Clear Cache
        try:
            profile.clearHttpCache()
        except AttributeError:
            print("clearHttpCache() is not supported in this version of PyQt.")

        # Clear Local Storage
        profile.clearAllVisitedLinks()

        # Delete cache and storage directories
        self._delete_directory(self._CACHE_PATH)
        self._delete_directory(self._STORAGE_PATH)

        self._ensure_directories()
        # Show a confirmation message
        QMessageBox.information(None, "Data Cleared", "All browser data has been successfully cleared.")

    def _delete_directory(self, path):
        """Delete the specified directory and its contents."""
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"Deleted directory: {path}")
            except PermissionError:
                print(f"Permission denied: {path}")
            except Exception as e:
                print(f"Error deleting directory {path}: {e}")

    def _ensure_directories(self):
        if not (os.path.exists(self._CACHE_PATH) and os.path.isdir(self._CACHE_PATH)):
            os.makedirs(self._CACHE_PATH)
        if not (os.path.exists(self._STORAGE_PATH) and os.path.isdir(self._STORAGE_PATH)):
            os.makedirs(self._STORAGE_PATH)

    def _getProfile(self) -> QWebEngineProfile:
        if config.PROFILE is not None:
            self._printProfileDetails()

        self._ensure_directories()
        config.PROFILE = QWebEngineProfile("MWVPersistentProfile")
        config.PROFILE.setCachePath(self._CACHE_PATH)
        config.PROFILE.setPersistentStoragePath(self._STORAGE_PATH)
        config.PROFILE.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        config.PROFILE.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        self._printProfileDetails()

    def _printProfileDetails(self):
        print("***********************")
        print(f"Storage Name: {config.PROFILE.storageName()}")
        print(f"Cache Path: {config.PROFILE.cachePath()}")
        print(f"Storage Path: {config.PROFILE.persistentStoragePath()}")
        print(f"Cache Type: {config.PROFILE.httpCacheType()}")
        print(f"Persistent Cookie Policy: {config.PROFILE.persistentCookiesPolicy()}")
        print(f"Off The Record: {config.PROFILE.isOffTheRecord()}")
        print("***********************")