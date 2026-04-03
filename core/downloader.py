from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from .utils import (
    detect_file_type,
    ensure_unique_path,
    format_size,
    get_default_download_dir,
    get_filename_from_url,
    sanitize_filename,
)


class DownloadStatus(Enum):
    QUEUED = "queued"
    CONNECTING = "connecting"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    url: str
    filename: str = ""
    save_path: str = ""
    connections: int = 16
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: float = 0.0
    total_size: int = 0
    downloaded_size: int = 0
    file_type: str = "other"
    content_type: str = ""
    gid: str = ""
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 5
    start_time: float = 0.0
    eta: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "filename": self.filename,
            "save_path": self.save_path,
            "connections": self.connections,
            "status": self.status.value,
            "progress": self.progress,
            "speed": self.speed,
            "total_size": self.total_size,
            "downloaded_size": self.downloaded_size,
            "file_type": self.file_type,
            "gid": self.gid,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "start_time": self.start_time,
            "eta": self.eta,
            "created_at": self.created_at,
        }


MAX_CONNECTIONS_PER_SERVER = 16
MIN_SPLIT_SIZE = "1M"


class Aria2RPC:
    def __init__(self, url: str, secret: str = ""):
        self.url = url
        self.secret = secret
        self._counter = 0

    def _token(self) -> str:
        return f"token:{self.secret}" if self.secret else ""

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        self._counter += 1
        payload_params: list[Any] = []
        if self.secret:
            payload_params.append(self._token())
        if params:
            payload_params.extend(params)

        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": self._counter,
            "method": method,
            "params": payload_params,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if "error" in data:
            raise RuntimeError(f"aria2 RPC error: {data['error']}")
        return data.get("result")


class DownloadEngine:
    def __init__(self, download_dir: Optional[str] = None, rpc_port: int = 6800):
        self.download_dir = str(download_dir or get_default_download_dir())
        self.rpc_port = rpc_port
        self.rpc_url = f"http://localhost:{rpc_port}/jsonrpc"
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._rpc: Optional[Aria2RPC] = None
        self._tasks: dict[str, DownloadTask] = {}
        self._gid_to_task: dict[str, str] = {}
        self._running = False
        self._poll_interval = 0.5
        self._on_progress: Optional[Callable[[DownloadTask], None]] = None
        self._on_complete: Optional[Callable[[DownloadTask], None]] = None
        self._on_error: Optional[Callable[[DownloadTask], None]] = None
        self._rpc_secret: str = ""

    def set_progress_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        self._on_progress = callback

    def set_complete_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        self._on_complete = callback

    def set_error_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        self._on_error = callback

    async def start(self) -> None:
        if self._running:
            return
        await self._start_aria2()
        self._running = True
        asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        self._running = False
        if self._rpc:
            try:
                self._rpc.call("aria2.shutdown")
            except Exception:
                pass
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._rpc = None
        self._process = None

    async def _start_aria2(self) -> None:
        if shutil.which("aria2c") is None:
            raise RuntimeError("aria2c not found. Install: sudo apt install aria2")

        self._rpc_secret = os.urandom(16).hex()

        args = [
            "aria2c",
            "--enable-rpc",
            f"--rpc-listen-port={self.rpc_port}",
            "--rpc-allow-origin-all",
            "--rpc-listen-all",
            f"--dir={self.download_dir}",
            f"--max-connection-per-server={MAX_CONNECTIONS_PER_SERVER}",
            f"--split={MAX_CONNECTIONS_PER_SERVER}",
            f"--min-split-size={MIN_SPLIT_SIZE}",
            "--continue=true",
            "--always-resume=true",
            "--max-resume-failure-tries=0",
            "--auto-file-renaming=false",
            "--allow-overwrite=false",
            "--file-allocation=falloc",
            "--disk-cache=128M",
            "--optimize-concurrent-downloads=true",
            "--max-concurrent-downloads=5",
            "--max-overall-download-limit=0",
            "--max-download-limit=0",
            "--bt-max-peers=0",
            "--seed-time=0",
            "--follow-torrent=false",
            "--check-certificate=false",
            "--timeout=60",
            "--connect-timeout=30",
            "--retry-wait=3",
            "--max-tries=5",
            "--summary-interval=1",
            f"--rpc-secret={self._rpc_secret}",
        ]

        self._process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        await asyncio.sleep(2)

        if self._process.poll() is not None:
            stderr = self._process.stderr.read().decode() if self._process.stderr else ""
            raise RuntimeError(f"aria2c failed to start: {stderr}")

        self._rpc = Aria2RPC(self.rpc_url, self._rpc_secret)

        try:
            version = self._rpc.call("aria2.getVersion")
            print(f"aria2c {version.get('version', '?')} started on port {self.rpc_port}")
        except Exception as e:
            raise RuntimeError(f"aria2c RPC not responding: {e}")

    def add_download(
        self,
        url: str,
        filename: str = "",
        save_path: str = "",
        connections: int = 16,
        headers: Optional[list[str]] = None,
    ) -> str:
        task_id = os.urandom(8).hex()

        if not filename:
            filename = get_filename_from_url(url)
        filename = sanitize_filename(filename)

        save_dir = save_path or self.download_dir
        file_path = ensure_unique_path(Path(save_dir) / filename)
        filename = file_path.name

        task = DownloadTask(
            url=url,
            filename=filename,
            save_path=str(save_dir),
            connections=min(connections, MAX_CONNECTIONS_PER_SERVER),
            file_type=detect_file_type(filename),
        )

        options: dict[str, Any] = {
            "dir": save_dir,
            "out": filename,
            "split": str(task.connections),
            "min-split-size": MIN_SPLIT_SIZE,
            "max-connection-per-server": str(task.connections),
            "continue": "true",
            "allow-overwrite": "false",
            "auto-file-renaming": "true",
            "file-allocation": "falloc",
            "max-tries": str(task.max_retries),
            "retry-wait": "3",
            "timeout": "60",
            "connect-timeout": "30",
        }

        if headers:
            options["header"] = headers

        try:
            if not self._rpc:
                raise RuntimeError("Engine not started")
            result = self._rpc.call("aria2.addUri", [[url], options])
            task.gid = result
            task.status = DownloadStatus.CONNECTING
            self._gid_to_task[result] = task_id
        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)

        self._tasks[task_id] = task
        return task_id

    def pause(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task or not task.gid:
            return False
        try:
            self._rpc.call("aria2.pause", [task.gid])
            task.status = DownloadStatus.PAUSED
            return True
        except Exception:
            return False

    def resume(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task or not task.gid:
            return False
        try:
            self._rpc.call("aria2.unpause", [task.gid])
            task.status = DownloadStatus.DOWNLOADING
            return True
        except Exception:
            return False

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        try:
            if task.gid and task.status not in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
                self._rpc.call("aria2.remove", [task.gid])
            task.status = DownloadStatus.CANCELLED
            return True
        except Exception:
            task.status = DownloadStatus.CANCELLED
            return True

    def remove(self, task_id: str, delete_file: bool = False) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        self.cancel(task_id)
        if delete_file and task.filename:
            try:
                file_path = Path(task.save_path) / task.filename
                if file_path.exists():
                    file_path.unlink()
            except OSError:
                pass
        if task.gid in self._gid_to_task:
            del self._gid_to_task[task.gid]
        del self._tasks[task_id]
        return True

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[DownloadTask]:
        return list(self._tasks.values())

    def get_active_tasks(self) -> list[DownloadTask]:
        return [t for t in self._tasks.values() if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONNECTING)]

    def pause_all(self) -> None:
        try:
            self._rpc.call("aria2.pauseAll")
            for task in self._tasks.values():
                if task.status == DownloadStatus.DOWNLOADING:
                    task.status = DownloadStatus.PAUSED
        except Exception:
            pass

    def resume_all(self) -> None:
        try:
            self._rpc.call("aria2.unpauseAll")
            for task in self._tasks.values():
                if task.status == DownloadStatus.PAUSED:
                    task.status = DownloadStatus.DOWNLOADING
        except Exception:
            pass

    def get_global_stats(self) -> dict[str, Any]:
        try:
            stats = self._rpc.call("aria2.getGlobalStat")
            return {
                "download_speed": int(stats.get("downloadSpeed", 0)),
                "upload_speed": int(stats.get("uploadSpeed", 0)),
                "num_active": int(stats.get("numActive", 0)),
                "num_waiting": int(stats.get("numWaiting", 0)),
                "num_stopped": int(stats.get("numStopped", 0)),
            }
        except Exception:
            return {"download_speed": 0, "upload_speed": 0, "num_active": 0, "num_waiting": 0, "num_stopped": 0}

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._update_tasks()
            except Exception:
                pass
            await asyncio.sleep(self._poll_interval)

    async def _update_tasks(self) -> None:
        if not self._rpc:
            return

        keys = ["gid", "status", "totalLength", "completedLength", "downloadSpeed", "files", "errorCode", "errorMessage"]

        try:
            active = self._rpc.call("aria2.tellActive", [keys])
            self._process_status_list(active)
        except Exception:
            pass

        try:
            waiting = self._rpc.call("aria2.tellWaiting", [0, 100, keys])
            self._process_status_list(waiting)
        except Exception:
            pass

        try:
            stopped = self._rpc.call("aria2.tellStopped", [0, 100, keys])
            self._process_status_list(stopped)
        except Exception:
            pass

    def _process_status_list(self, status_list: list[dict[str, Any]]) -> None:
        for info in status_list:
            gid = info.get("gid", "")
            task_id = self._gid_to_task.get(gid)
            if not task_id:
                continue
            task = self._tasks.get(task_id)
            if not task:
                continue
            self._update_task_from_aria(task, info)

    def _update_task_from_aria(self, task: DownloadTask, info: dict[str, Any]) -> None:
        aria_status = info.get("status", "")

        total = int(info.get("totalLength", 0))
        completed = int(info.get("completedLength", 0))
        speed = int(info.get("downloadSpeed", 0))

        task.total_size = total
        task.downloaded_size = completed
        task.speed = speed

        if total > 0:
            task.progress = (completed / total) * 100.0
            remaining = total - completed
            task.eta = remaining / speed if speed > 0 else 0.0
        else:
            task.progress = 0.0
            task.eta = 0.0

        old_status = task.status

        if aria_status == "active":
            task.status = DownloadStatus.DOWNLOADING
            if task.start_time == 0:
                task.start_time = time.time()
        elif aria_status == "waiting":
            task.status = DownloadStatus.QUEUED
        elif aria_status == "paused":
            task.status = DownloadStatus.PAUSED
        elif aria_status == "complete":
            task.status = DownloadStatus.COMPLETED
            task.progress = 100.0
            task.speed = 0.0
            task.eta = 0.0
            if files := info.get("files"):
                if path := files[0].get("path"):
                    task.filename = os.path.basename(path)
            if old_status != DownloadStatus.COMPLETED and self._on_complete:
                self._on_complete(task)
        elif aria_status == "error":
            error_code = info.get("errorCode", "")
            error_msg = info.get("errorMessage", f"Error code: {error_code}")

            if task.retry_count < task.max_retries:
                task.retry_count += 1
                self._retry_download(task)
            else:
                task.status = DownloadStatus.FAILED
                task.error_message = error_msg
                task.speed = 0.0
                if old_status != DownloadStatus.FAILED and self._on_error:
                    self._on_error(task)
        elif aria_status == "removed":
            if task.status != DownloadStatus.CANCELLED:
                task.status = DownloadStatus.FAILED
                task.error_message = "Download removed"

        if self._on_progress and task.status == DownloadStatus.DOWNLOADING:
            self._on_progress(task)

    def _retry_download(self, task: DownloadTask) -> None:
        try:
            self._rpc.call("aria2.remove", [task.gid])
        except Exception:
            pass

        options: dict[str, Any] = {
            "dir": task.save_path,
            "out": task.filename,
            "split": str(task.connections),
            "min-split-size": MIN_SPLIT_SIZE,
            "max-connection-per-server": str(task.connections),
            "continue": "true",
            "allow-overwrite": "true",
            "auto-file-renaming": "false",
            "file-allocation": "falloc",
            "max-tries": str(task.max_retries),
            "retry-wait": "3",
        }

        try:
            result = self._rpc.call("aria2.addUri", [[task.url], options])
            old_gid = task.gid
            task.gid = result
            if old_gid in self._gid_to_task:
                task_id = self._gid_to_task.pop(old_gid)
                self._gid_to_task[result] = task_id
            task.status = DownloadStatus.CONNECTING
        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = f"Retry failed: {e}"

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def task_count(self) -> int:
        return len(self._tasks)
