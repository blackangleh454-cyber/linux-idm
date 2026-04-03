from __future__ import annotations

import json
import os
import struct
import sys
import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from .utils import detect_installed_browsers, get_filename_from_url, validate_url

logger = logging.getLogger(__name__)

NATIVE_HOST_NAME = "com.linux_idm.downloader"
APP_NAME = "Linux IDM"

DOWNLOAD_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".dmg",
    ".exe", ".msi", ".deb", ".rpm", ".appimage", ".run", ".bin",
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".mp3", ".flac", ".wav", ".aac", ".ogg", ".wma", ".m4a",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".epub", ".mobi", ".apk", ".ipa", ".torrent",
}


def get_manifest_path() -> Path:
    return Path(__file__).parent.parent / "native_messaging_manifest.json"


def get_host_script_path() -> Path:
    return Path(__file__).parent.parent / "native_host.py"


def create_native_messaging_manifest(host_script_path: Optional[str] = None) -> dict[str, Any]:
    script = host_script_path or str(get_host_script_path())
    manifest = {
        "name": NATIVE_HOST_NAME,
        "description": APP_NAME,
        "path": script,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://*/",
            "moz-extension://*/",
        ],
    }
    return manifest


def write_manifest_files() -> dict[str, list[str]]:
    manifest = create_native_messaging_manifest()
    written: dict[str, list[str]] = {}

    browsers = detect_installed_browsers()

    chrome_manifest = {**manifest}
    chrome_manifest.pop("allowed_extensions", None)
    chrome_manifest["allowed_origins"] = manifest["allowed_origins"]

    firefox_manifest = {
        "name": NATIVE_HOST_NAME,
        "description": APP_NAME,
        "path": manifest["path"],
        "type": "stdio",
        "allowed_extensions": ["linux-idm@extension"],
    }

    for browser_name, info in browsers.items():
        native_dir = info.get("native_host_dir", "")
        if not native_dir:
            continue

        dir_path = Path(native_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        manifest_file = dir_path / f"{NATIVE_HOST_NAME}.json"

        try:
            if browser_name == "firefox":
                content = json.dumps(firefox_manifest, indent=2)
            else:
                content = json.dumps(chrome_manifest, indent=2)

            manifest_file.write_text(content)
            os.chmod(str(manifest_file), 0o644)

            if browser_name not in written:
                written[browser_name] = []
            written[browser_name].append(str(manifest_file))
        except OSError as e:
            logger.error(f"Failed to write manifest for {browser_name}: {e}")

    return written


def register_native_host() -> dict[str, list[str]]:
    results = write_manifest_files()

    if not results:
        logger.warning("No browsers detected for native messaging registration")
    else:
        for browser, paths in results.items():
            for p in paths:
                logger.info(f"Registered native host for {browser}: {p}")

    return results


def unregister_native_host() -> dict[str, list[str]]:
    removed: dict[str, list[str]] = {}
    browsers = detect_installed_browsers()

    for browser_name, info in browsers.items():
        native_dir = info.get("native_host_dir", "")
        if not native_dir:
            continue

        manifest_file = Path(native_dir) / f"{NATIVE_HOST_NAME}.json"
        try:
            if manifest_file.exists():
                manifest_file.unlink()
                if browser_name not in removed:
                    removed[browser_name] = []
                removed[browser_name].append(str(manifest_file))
        except OSError as e:
            logger.error(f"Failed to remove manifest for {browser_name}: {e}")

    return removed


def is_registered() -> dict[str, bool]:
    browsers = detect_installed_browsers()
    status: dict[str, bool] = {}

    for browser_name, info in browsers.items():
        native_dir = info.get("native_host_dir", "")
        if not native_dir:
            status[browser_name] = False
            continue
        manifest_file = Path(native_dir) / f"{NATIVE_HOST_NAME}.json"
        status[browser_name] = manifest_file.exists()

    return status


def is_downloadable_url(url: str) -> bool:
    if not validate_url(url):
        return False

    from urllib.parse import urlparse

    parsed = urlparse(url)
    path = parsed.path.lower()

    _, ext = os.path.splitext(path)
    if ext in DOWNLOAD_EXTENSIONS:
        return True

    dl_patterns = [
        "/download/",
        "/dl/",
        "/get/",
        "/file/",
        "/attachments/",
        "/blob/",
        "/raw/",
        "/releases/download/",
    ]
    return any(p in path for p in dl_patterns)


class NativeMessageHandler:
    def __init__(self) -> None:
        self._on_download_request: Optional[Callable[[dict[str, Any]], None]] = None
        self._on_status_request: Optional[Callable[[], dict[str, Any]]] = None
        self._running = False

    def set_download_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._on_download_request = callback

    def set_status_callback(self, callback: Callable[[], dict[str, Any]]) -> None:
        self._on_status_request = callback

    def read_message(self) -> Optional[dict[str, Any]]:
        raw_length = sys.stdin.buffer.read(4)
        if not raw_length or len(raw_length) < 4:
            return None

        message_length = struct.unpack("I", raw_length)[0]
        message_data = sys.stdin.buffer.read(message_length)

        if len(message_data) < message_length:
            return None

        try:
            return json.loads(message_data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to decode message: {e}")
            return None

    def send_message(self, message: dict[str, Any]) -> None:
        encoded = json.dumps(message).encode("utf-8")
        sys.stdout.buffer.write(struct.pack("I", len(encoded)))
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any]:
        action = message.get("action", "")

        if action == "download":
            url = message.get("url", "")
            if not url or not validate_url(url):
                return {"status": "error", "message": "Invalid URL"}

            if self._on_download_request:
                self._on_download_request(message)

            return {
                "status": "ok",
                "message": "Download queued",
                "url": url,
                "filename": message.get("filename", get_filename_from_url(url)),
            }

        elif action == "ping":
            return {"status": "ok", "message": APP_NAME}

        elif action == "status":
            if self._on_status_request:
                return self._on_status_request()
            return {"status": "ok", "downloads": []}

        elif action == "detect":
            url = message.get("url", "")
            return {
                "status": "ok",
                "downloadable": is_downloadable_url(url),
                "url": url,
            }

        return {"status": "error", "message": f"Unknown action: {action}"}

    def run(self) -> None:
        self._running = True
        while self._running:
            message = self.read_message()
            if message is None:
                break
            response = self.handle_message(message)
            self.send_message(response)

    def stop(self) -> None:
        self._running = False

    async def run_async(self) -> None:
        loop = asyncio.get_event_loop()
        self._running = True

        while self._running:
            message = await loop.run_in_executor(None, self.read_message)
            if message is None:
                break
            response = self.handle_message(message)
            await loop.run_in_executor(None, self.send_message, response)
