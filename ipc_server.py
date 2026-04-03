from __future__ import annotations

import json
import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Optional

IDM_SOCKET = "/tmp/linux-idm.sock"
IDM_HTTP_HOST = "127.0.0.1"
IDM_HTTP_PORT = 64000


class IDMRequestHandler(BaseHTTPRequestHandler):
    _download_callback: Optional[Callable[[dict], Any]] = None
    _status_callback: Optional[Callable[[], Any]] = None

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_POST(self) -> None:
        if self.path == "/api/download":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json({"status": "error", "message": "Invalid JSON"}, 400)
                return

            if IDMRequestHandler._download_callback:
                result = IDMRequestHandler._download_callback(data)
                self._send_json(result or {"status": "ok"})
            else:
                self._send_json({"status": "error", "message": "No callback registered"})
        else:
            self._send_json({"status": "error", "message": "Not found"}, 404)

    def do_GET(self) -> None:
        if self.path == "/api/status":
            if IDMRequestHandler._status_callback:
                result = IDMRequestHandler._status_callback()
                self._send_json(result or {"status": "ok"})
            else:
                self._send_json({"status": "ok", "running": True})
        elif self.path == "/api/ping":
            self._send_json({"status": "ok", "message": "LinuxIDM"})
        else:
            self._send_json({"status": "error", "message": "Not found"}, 404)

    def _send_json(self, data: dict, code: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


class IPCServer:
    def __init__(self, http_port: int = IDM_HTTP_PORT):
        self.http_port = http_port
        self._http_server: Optional[HTTPServer] = None
        self._socket_server: Optional[socket.socket] = None
        self._running = False
        self._threads: list[threading.Thread] = []

    def set_download_callback(self, callback: Callable[[dict], Any]) -> None:
        IDMRequestHandler._download_callback = callback

    def set_status_callback(self, callback: Callable[[], Any]) -> None:
        IDMRequestHandler._status_callback = callback

    def start(self) -> None:
        self._running = True

        http_thread = threading.Thread(target=self._run_http, daemon=True)
        http_thread.start()
        self._threads.append(http_thread)

        socket_thread = threading.Thread(target=self._run_socket, daemon=True)
        socket_thread.start()
        self._threads.append(socket_thread)

    def _run_http(self) -> None:
        try:
            self._http_server = HTTPServer((IDM_HTTP_HOST, self.http_port), IDMRequestHandler)
            self._http_server.serve_forever()
        except Exception:
            pass

    def _run_socket(self) -> None:
        if os.path.exists(IDM_SOCKET):
            try:
                os.unlink(IDM_SOCKET)
            except OSError:
                pass

        self._socket_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket_server.settimeout(1.0)
        try:
            self._socket_server.bind(IDM_SOCKET)
            self._socket_server.listen(5)
            os.chmod(IDM_SOCKET, 0o666)
        except OSError:
            return

        while self._running:
            try:
                conn, _ = self._socket_server.accept()
                data = conn.recv(4096)
                if data:
                    try:
                        message = json.loads(data.decode("utf-8"))
                        action = message.get("action", "")

                        if action == "download" and IDMRequestHandler._download_callback:
                            result = IDMRequestHandler._download_callback(message)
                        elif action == "list" and IDMRequestHandler._status_callback:
                            result = IDMRequestHandler._status_callback()
                        elif action == "ping":
                            result = {"status": "ok"}
                        else:
                            result = {"status": "unknown_action"}

                        conn.sendall(json.dumps(result or {"status": "ok"}).encode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        conn.sendall(json.dumps({"status": "error"}).encode("utf-8"))
                conn.close()
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self) -> None:
        self._running = False

        if self._http_server:
            self._http_server.shutdown()

        if self._socket_server:
            try:
                self._socket_server.close()
            except OSError:
                pass
            if os.path.exists(IDM_SOCKET):
                try:
                    os.unlink(IDM_SOCKET)
                except OSError:
                    pass
