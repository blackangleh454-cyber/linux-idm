#!/usr/bin/env python3

import asyncio
import os
import sys
import signal
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import QTimer

from ui.theme import Theme, Colors
from ui.main_window import MainWindow
from ui.widgets import DownloadCardWidget, DownloadStatus
from core.downloader import DownloadEngine
from core.browser_integration import register_native_host
from ipc_server import IPCServer
from core.utils import get_default_download_dir


class LinuxIDMApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("LinuxIDM")
        self.app.setApplicationVersion("1.0.0")
        self.app.setPalette(Theme.get_palette())
        self.app.setStyleSheet(Theme.get_stylesheet())

        self.download_dir = str(get_default_download_dir())
        os.makedirs(self.download_dir, exist_ok=True)

        self.loop = asyncio.new_event_loop()
        self.engine = DownloadEngine(download_dir=self.download_dir)
        self.ipc = IPCServer()
        self.window = None
        self.engine_event = threading.Event()
        self.tid_to_uid = {}

    def start_engine(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._engine_main())

    async def _engine_main(self):
        await self.engine.start()
        self.engine_event.set()
        while self.engine._running:
            await asyncio.sleep(1)

    def poll_ui(self):
        if not self.window or not self.engine_event.is_set():
            return

        for tid, task in list(self.engine._tasks.items()):
            uid = self.tid_to_uid.get(tid)
            if not uid:
                continue

            info = self.window._downloads.get(uid)
            card = self.window._download_cards.get(uid)
            if not info or not card:
                continue

            old_status = info["status"]

            if task.status.value == "downloading":
                info["progress"] = task.progress
                info["speed"] = task.speed
                info["size"] = task.total_size
                info["downloaded"] = task.downloaded_size
                info["status"] = DownloadStatus.DOWNLOADING

                eta = "--:--"
                if task.speed > 0 and task.total_size > 0:
                    remaining = task.total_size - task.downloaded_size
                    s = int(remaining / task.speed)
                    eta = f"{s // 60:02d}:{s % 60:02d}"

                card.set_progress(task.progress)
                card.set_speed(task.speed)
                card.set_size(task.total_size)
                card.set_eta(eta)
                if old_status != DownloadStatus.DOWNLOADING:
                    card.set_status(DownloadStatus.DOWNLOADING)

            elif task.status.value == "complete" and old_status != DownloadStatus.COMPLETED:
                info["progress"] = 100.0
                info["speed"] = 0.0
                info["status"] = DownloadStatus.COMPLETED
                card.set_progress(100.0)
                card.set_speed(0)
                card.set_status(DownloadStatus.COMPLETED)

            elif task.status.value == "error" and old_status != DownloadStatus.ERROR:
                info["status"] = DownloadStatus.ERROR
                card.set_status(DownloadStatus.ERROR)

            elif task.status.value == "paused" and old_status != DownloadStatus.PAUSED:
                info["status"] = DownloadStatus.PAUSED
                card.set_status(DownloadStatus.PAUSED)

        self.window._update_counts()

    def add_download(self, url, filename="", save_path="", connections=8, category="General"):
        try:
            self._do_add_download(url, filename, save_path, connections, category)
        except Exception as e:
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()

    def _do_add_download(self, url, filename="", save_path="", connections=8, category="General"):
        if not self.engine_event.is_set():
            QTimer.singleShot(500, lambda: self.add_download(url, filename, save_path, connections))
            return

        uid = str(uuid.uuid4())[:8]
        save_path = save_path or self.download_dir

        if not filename:
            filename = url.split("/")[-1].split("?")[0] or "download"

        tid = self.engine.add_download(url, filename=filename, save_path=save_path, connections=connections)
        task = self.engine.get_task(tid)
        display_name = task.filename if task else filename

        self.tid_to_uid[tid] = uid

        info = {
            "id": uid, "url": url, "filename": display_name,
            "save_path": save_path, "connections": connections,
            "category": category, "progress": 0.0, "speed": 0.0,
            "size": 0.0, "downloaded": 0.0, "eta": "--:--",
            "status": DownloadStatus.QUEUED,
        }
        self.window._downloads[uid] = info

        card = DownloadCardWidget(uid)
        card.set_filename(display_name)
        card.set_url(url)
        card.set_save_path(save_path)
        card.set_connections(connections)
        card.set_status(DownloadStatus.QUEUED)

        card.pause_clicked.connect(self._pause)
        card.resume_clicked.connect(self._resume)
        card.cancel_clicked.connect(self._cancel)
        card.delete_clicked.connect(self._cancel)
        card.open_clicked.connect(self.window._open_download)
        card.open_folder_clicked.connect(self.window._open_folder)
        card.copy_url_clicked.connect(self.window._copy_url)

        self.window._download_cards[uid] = card
        item = QListWidgetItem(self.window._download_list)
        item.setSizeHint(card.sizeHint())
        self.window._download_list.addItem(item)
        self.window._download_list.setItemWidget(item, card)
        self.window._update_counts()

    def _pause(self, uid):
        info = self.window._downloads.get(uid)
        if not info:
            return
        for tid, t in self.engine._tasks.items():
            if t.url == info["url"] and t.status.value == "downloading":
                self.engine.pause(tid)
                break
        info["status"] = DownloadStatus.PAUSED
        card = self.window._download_cards.get(uid)
        if card:
            card.set_status(DownloadStatus.PAUSED)
        self.window._update_counts()

    def _resume(self, uid):
        info = self.window._downloads.get(uid)
        if not info:
            return
        for tid, t in self.engine._tasks.items():
            if t.url == info["url"] and t.status.value == "paused":
                self.engine.resume(tid)
                break
        info["status"] = DownloadStatus.DOWNLOADING
        card = self.window._download_cards.get(uid)
        if card:
            card.set_status(DownloadStatus.DOWNLOADING)
        self.window._update_counts()

    def _cancel(self, uid):
        info = self.window._downloads.get(uid)
        if info:
            for tid, t in list(self.engine._tasks.items()):
                if t.url == info["url"]:
                    self.engine.cancel(tid)
                    break
            del self.window._downloads[uid]
        if uid in self.window._download_cards:
            card = self.window._download_cards[uid]
            for i in range(self.window._download_list.count()):
                item = self.window._download_list.item(i)
                if self.window._download_list.itemWidget(item) == card:
                    self.window._download_list.takeItem(i)
                    break
            del self.window._download_cards[uid]
        self.window._update_counts()

    def _pause_all(self):
        self.engine.pause_all()
        for uid, info in self.window._downloads.items():
            if info["status"] == DownloadStatus.DOWNLOADING:
                info["status"] = DownloadStatus.PAUSED
                card = self.window._download_cards.get(uid)
                if card:
                    card.set_status(DownloadStatus.PAUSED)
        self.window._update_counts()

    def _resume_all(self):
        self.engine.resume_all()
        for uid, info in self.window._downloads.items():
            if info["status"] in (DownloadStatus.PAUSED, DownloadStatus.QUEUED):
                info["status"] = DownloadStatus.DOWNLOADING
                card = self.window._download_cards.get(uid)
                if card:
                    card.set_status(DownloadStatus.DOWNLOADING)
        self.window._update_counts()

    def _on_browser_download(self, msg):
        url = msg.get("url", "")
        if url:
            QTimer.singleShot(0, lambda: self.add_download(url))
        return {"status": "ok"}

    def _on_status_request(self):
        return {"status": "ok", "active": len(self.engine.get_active_tasks())}

    def run(self):
        t = threading.Thread(target=self.start_engine, daemon=True)
        t.start()

        self.engine_event.wait(timeout=10)

        self.ipc.set_download_callback(self._on_browser_download)
        self.ipc.set_status_callback(self._on_status_request)
        self.ipc.start()

        try:
            register_native_host()
        except Exception:
            pass

        self.window = MainWindow()
        self.window._settings["download_path"] = self.download_dir
        self.window._status_path.setText(f" {self.download_dir}")

        self.window._add_download_from_url = self.add_download
        self.window._pause_download = self._pause
        self.window._resume_download = self._resume
        self.window._cancel_download = self._cancel
        self.window._pause_all = self._pause_all
        self.window._resume_all = self._resume_all

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.poll_ui)
        self.ui_timer.start(250)

        self.window.show()
        return self.app.exec_()

    def shutdown(self):
        self.ipc.stop()
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = LinuxIDMApp()
    exit_code = app.run()
    app.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
