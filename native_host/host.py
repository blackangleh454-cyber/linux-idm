#!/usr/bin/env python3

import sys
import json
import struct
import socket
import os

IDM_SOCKET = "/tmp/linux-idm.sock"
IDM_HTTP_HOST = "127.0.0.1"
IDM_HTTP_PORT = 64000


def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    message_length = struct.unpack("=I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)


def send_message(message):
    encoded = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("=I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def send_via_socket(message):
    try:
        if not os.path.exists(IDM_SOCKET):
            return False
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(IDM_SOCKET)
        client.sendall(json.dumps(message).encode("utf-8"))
        response = client.recv(4096)
        client.close()
        if response:
            return json.loads(response.decode("utf-8"))
        return True
    except Exception:
        return False


def send_via_http(message):
    try:
        import urllib.request
        url = f"http://{IDM_HTTP_HOST}:{IDM_HTTP_PORT}/api/download"
        data = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def handle_download(message):
    download_request = {
        "action": "download",
        "url": message.get("url", ""),
        "filename": message.get("filename", ""),
        "referrer": message.get("referrer", ""),
        "cookies": message.get("cookies", ""),
        "user_agent": message.get("userAgent", ""),
        "file_size": message.get("fileSize", 0),
        "mime_type": message.get("mimeType", "")
    }

    result = send_via_socket(download_request)
    if result:
        return result

    result = send_via_http(download_request)
    if result:
        return result

    return {"status": "rejected", "reason": "IDM not available"}


def main():
    while True:
        message = read_message()
        if message is None:
            break

        action = message.get("action", "")

        if action == "download":
            response = handle_download(message)
            send_message(response)
        elif action == "ping":
            send_message({"status": "ok"})
        elif action == "get_downloads":
            response = send_via_socket({"action": "list"})
            send_message(response if response else {"status": "error"})
        else:
            send_message({"status": "unknown_action"})


if __name__ == "__main__":
    main()
