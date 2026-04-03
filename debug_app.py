#!/usr/bin/env python3
"""Deep debug script for LinuxIDM - traces every step of download flow"""
import sys, os, signal, time
sys.path.insert(0, os.path.dirname(__file__))
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import QTimer
from ui.theme import Theme
from ui.main_window import MainWindow
from ui.widgets import DownloadCardWidget, DownloadStatus
from core.downloader import DownloadEngine
from core.utils import get_default_download_dir
import asyncio, threading, uuid

app = QApplication(sys.argv)
app.setApplicationName("LinuxIDM Debug")
app.setPalette(Theme.get_palette())
app.setStyleSheet(Theme.get_stylesheet())

download_dir = str(get_default_download_dir())
os.makedirs(download_dir, exist_ok=True)

# ---- ENGINE SETUP ----
loop = asyncio.new_event_loop()
engine = DownloadEngine(download_dir=download_dir)
engine_ready = False
tid_to_uid = {}

def start_engine():
    global engine_ready
    asyncio.set_event_loop(loop)
    async def go():
        try:
            print("[ENGINE] Starting aria2c...", flush=True)
            await engine.start()
            print(f"[ENGINE] aria2c started, is_running={engine.is_running}", flush=True)
            engine_ready = True
            while engine._running:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"[ENGINE] ERROR: {e}", flush=True)
            import traceback
            traceback.print_exc()
    try:
        loop.run_until_complete(go())
    except Exception as e:
        print(f"[ENGINE] LOOP ERROR: {e}", flush=True)

t = threading.Thread(target=start_engine, daemon=True)
t.start()

for _ in range(50):
    if engine_ready:
        break
    time.sleep(0.1)

print(f"[INIT] Engine ready: {engine_ready}", flush=True)

# ---- WINDOW SETUP ----
window = MainWindow()
window._settings["download_path"] = download_dir

# ---- ADD DOWNLOAD FUNCTION ----
def add_download(url, filename="", save_path="", connections=8, category="General"):
    print(f"[ADD] Called with url={url}", flush=True)

    if not engine_ready:
        print("[ADD] Engine not ready!", flush=True)
        return

    uid = str(uuid.uuid4())[:8]
    save_path = save_path or download_dir
    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "download"

    print(f"[ADD] Calling engine.add_download({url})", flush=True)
    tid = engine.add_download(url, filename=filename, save_path=save_path, connections=connections)
    task = engine.get_task(tid)
    display_name = task.filename if task else filename
    print(f"[ADD] Engine returned: tid={tid}, gid={task.gid if task else 'None'}, filename={display_name}", flush=True)

    tid_to_uid[tid] = uid

    info = {
        "id": uid, "url": url, "filename": display_name,
        "save_path": save_path, "connections": connections,
        "category": category, "progress": 0.0, "speed": 0.0,
        "size": 0.0, "downloaded": 0.0, "eta": "--:--",
        "status": DownloadStatus.QUEUED,
    }
    window._downloads[uid] = info

    card = DownloadCardWidget(uid)
    card.set_filename(display_name)
    card.set_url(url)
    card.set_save_path(save_path)
    card.set_connections(connections)
    card.set_status(DownloadStatus.QUEUED)

    card.pause_clicked.connect(lambda x: None)
    card.resume_clicked.connect(lambda x: None)
    card.cancel_clicked.connect(lambda x: None)
    card.delete_clicked.connect(lambda x: None)
    card.open_clicked.connect(window._open_download)
    card.open_folder_clicked.connect(window._open_folder)
    card.copy_url_clicked.connect(window._copy_url)

    window._download_cards[uid] = card
    item = QListWidgetItem(window._download_list)
    item.setSizeHint(card.sizeHint())
    window._download_list.addItem(item)
    window._download_list.setItemWidget(item, card)
    window._update_counts()
    print(f"[ADD] UI card created: uid={uid}", flush=True)

# ---- POLL TIMER ----
poll_count = 0
def poll_ui():
    global poll_count
    poll_count += 1

    if not engine_ready:
        return

    tasks = list(engine._tasks.items())
    if poll_count % 20 == 1:  # Print every 5 seconds
        print(f"[POLL #{poll_count}] Engine has {len(tasks)} tasks", flush=True)
        for tid, task in tasks:
            uid = tid_to_uid.get(tid, "?")
            print(f"  tid={tid} uid={uid} gid={task.gid} status={task.status.value} progress={task.progress:.1f}% speed={task.speed}", flush=True)

    for tid, task in tasks:
        uid = tid_to_uid.get(tid)
        if not uid:
            continue

        info = window._downloads.get(uid)
        card = window._download_cards.get(uid)
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
                print(f"[UI] Card {uid} -> DOWNLOADING", flush=True)

        elif task.status.value == "complete" and old_status != DownloadStatus.COMPLETED:
            info["progress"] = 100.0
            info["speed"] = 0.0
            info["status"] = DownloadStatus.COMPLETED
            card.set_progress(100.0)
            card.set_speed(0)
            card.set_status(DownloadStatus.COMPLETED)
            print(f"[UI] Card {uid} -> COMPLETED", flush=True)

        elif task.status.value == "error" and old_status != DownloadStatus.ERROR:
            info["status"] = DownloadStatus.ERROR
            card.set_status(DownloadStatus.ERROR)
            print(f"[UI] Card {uid} -> ERROR: {task.error_message}", flush=True)

        elif task.status.value == "connecting" and old_status != DownloadStatus.CONNECTING:
            info["status"] = DownloadStatus.CONNECTING
            card.set_status(DownloadStatus.QUEUED)

    window._update_counts()

timer = QTimer()
timer.timeout.connect(poll_ui)
timer.start(250)
print("[INIT] Poll timer started at 250ms", flush=True)

# ---- OVERRIDE ----
window._add_download_from_url = add_download
window._pause_download = lambda x: None
window._resume_download = lambda x: None
window._cancel_download = lambda x: None
window._pause_all = lambda: None
window._resume_all = lambda: None

# ---- AUTO TEST after 3 seconds ----
def auto_test():
    print("[TEST] Auto-adding download...", flush=True)
    add_download('https://httpbin.org/bytes/5242880', filename='debug_test.bin', connections=4)

QTimer.singleShot(3000, auto_test)

window.show()
print("[INIT] Window shown, entering event loop", flush=True)
exit_code = app.exec_()
print(f"[EXIT] Code: {exit_code}", flush=True)
sys.exit(exit_code)
