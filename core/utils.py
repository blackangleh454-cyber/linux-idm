from __future__ import annotations

import os
import re
import shutil
import urllib.parse
from pathlib import Path
from typing import Optional


def format_size(size_bytes: int | float) -> str:
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0:
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.2f} EB"


def format_speed(speed_bytes: float) -> str:
    if speed_bytes <= 0:
        return "0 B/s"
    return f"{format_size(speed_bytes)}/s"


def format_time(seconds: float) -> str:
    if seconds < 0 or seconds > 86400 * 365:
        return "∞"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"


def validate_url(url: str) -> bool:
    try:
        result = urllib.parse.urlparse(url)
        return result.scheme in ("http", "https", "ftp", "ftps", "magnet") and bool(result.netloc)
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    filename = filename.strip(". ")
    if not filename:
        filename = "download"
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext
    return filename


def get_filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    filename = os.path.basename(path)
    if not filename or "." not in filename:
        filename = "download"
    return sanitize_filename(filename)


def get_filename_from_cd(content_disposition: str) -> Optional[str]:
    if not content_disposition:
        return None
    patterns = [
        r"filename\*=UTF-8''(.+?)(?:;|$)",
        r'filename="(.+?)"',
        r"filename=(.+?)(?:;|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, content_disposition, re.IGNORECASE)
        if match:
            filename = urllib.parse.unquote(match.group(1))
            return sanitize_filename(filename)
    return None


FILE_TYPE_MAP: dict[tuple[str, ...], str] = {
    (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".vob"): "video",
    (".mp3", ".flac", ".wav", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".aiff", ".ape", ".ac3", ".dts"): "audio",
    (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico", ".heic", ".avif"): "image",
    (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf", ".txt", ".csv", ".epub", ".mobi"): "document",
    (".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".lzma", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz", ".cab", ".iso", ".dmg"): "archive",
    (".exe", ".msi", ".deb", ".rpm", ".appimage", ".snap", ".flatpak", ".AppImage", ".run", ".bin"): "executable",
    (".apk", ".ipa", ".xapk"): "mobile_app",
    (".torrent",): "torrent",
}

MIME_TYPE_MAP: dict[str, str] = {
    "video/": "video",
    "audio/": "audio",
    "image/": "image",
    "application/pdf": "document",
    "application/msword": "document",
    "application/vnd.openxmlformats": "document",
    "application/vnd.ms-": "document",
    "application/zip": "archive",
    "application/x-rar": "archive",
    "application/x-7z": "archive",
    "application/x-tar": "archive",
    "application/gzip": "archive",
    "application/x-bzip2": "archive",
    "application/x-iso9660": "archive",
    "application/x-apple-diskimage": "archive",
    "application/octet-stream": "binary",
    "application/x-executable": "executable",
    "application/vnd.android": "mobile_app",
}


def detect_file_type(filename: str, content_type: str = "") -> str:
    _, ext = os.path.splitext(filename.lower())
    for extensions, ftype in FILE_TYPE_MAP.items():
        if ext in extensions:
            return ftype
    if content_type:
        ct = content_type.lower().split(";")[0].strip()
        for mime_prefix, ftype in MIME_TYPE_MAP.items():
            if ct.startswith(mime_prefix):
                return ftype
    return "other"


def get_default_download_dir() -> Path:
    xdg = os.environ.get("XDG_DOWNLOAD_DIR")
    if xdg:
        path = Path(xdg).expanduser()
        if path.is_dir():
            return path
    home = Path.home()
    dl = home / "Downloads"
    dl.mkdir(parents=True, exist_ok=True)
    return dl


def detect_installed_browsers() -> dict[str, dict[str, Optional[str]]]:
    browsers: dict[str, dict[str, Optional[str]]] = {}

    chrome_paths = {
        "google-chrome": {
            "bin": shutil.which("google-chrome") or shutil.which("google-chrome-stable"),
            "config": str(Path.home() / ".config/google-chrome"),
            "native_host_dir": str(Path.home() / ".config/google-chrome/NativeMessagingHosts"),
        },
        "chromium": {
            "bin": shutil.which("chromium-browser") or shutil.which("chromium"),
            "config": str(Path.home() / ".config/chromium"),
            "native_host_dir": str(Path.home() / ".config/chromium/NativeMessagingHosts"),
        },
        "brave": {
            "bin": shutil.which("brave-browser") or shutil.which("brave"),
            "config": str(Path.home() / ".config/BraveSoftware/Brave-Browser"),
            "native_host_dir": str(Path.home() / ".config/BraveSoftware/Brave-Browser/NativeMessagingHosts"),
        },
        "vivaldi": {
            "bin": shutil.which("vivaldi") or shutil.which("vivaldi-stable"),
            "config": str(Path.home() / ".config/vivaldi"),
            "native_host_dir": str(Path.home() / ".config/vivaldi/NativeMessagingHosts"),
        },
        "edge": {
            "bin": shutil.which("microsoft-edge") or shutil.which("microsoft-edge-stable"),
            "config": str(Path.home() / ".config/microsoft-edge"),
            "native_host_dir": str(Path.home() / ".config/microsoft-edge/NativeMessagingHosts"),
        },
    }

    for name, info in chrome_paths.items():
        if info["bin"]:
            browsers[name] = info

    firefox_bin = shutil.which("firefox")
    if firefox_bin:
        mozilla_dir = Path.home() / ".mozilla/firefox"
        native_host_dir = str(Path.home() / ".mozilla/native-messaging-hosts")
        browsers["firefox"] = {
            "bin": firefox_bin,
            "config": str(mozilla_dir),
            "native_host_dir": native_host_dir,
        }

    return browsers


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def create_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
