const NATIVE_HOST_NAME = "com.linuxidm.downloader";
let nativePort = null;
let autoCapture = true;
let downloadCount = 0;
let isConnected = false;

function connectNativeHost() {
  try {
    nativePort = chrome.runtime.connectNative(NATIVE_HOST_NAME);
    nativePort.onMessage.addListener((msg) => {
      handleNativeMessage(msg);
    });
    nativePort.onDisconnect.addListener(() => {
      isConnected = false;
      nativePort = null;
      setTimeout(connectNativeHost, 5000);
    });
    isConnected = true;
  } catch (e) {
    isConnected = false;
  }
}

function handleNativeMessage(msg) {
  if (msg.type === "download_progress") {
    chrome.storage.local.set({ currentSpeed: msg.speed });
  }
  if (msg.type === "download_complete") {
    downloadCount++;
    chrome.storage.local.set({ downloadCount: downloadCount });
  }
}

function sendToNativeHost(message) {
  return new Promise((resolve, reject) => {
    if (!nativePort) {
      connectNativeHost();
      if (!nativePort) {
        reject(new Error("Native host unavailable"));
        return;
      }
    }
    try {
      nativePort.postMessage(message);
      const listener = (response) => {
        nativePort.onMessage.removeListener(listener);
        resolve(response);
      };
      nativePort.onMessage.addListener(listener);
      setTimeout(() => {
        nativePort.onMessage.removeListener(listener);
        resolve({ status: "timeout" });
      }, 3000);
    } catch (e) {
      reject(e);
    }
  });
}

function showNotification(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon48.png",
    title: title,
    message: message
  });
}

function captureDownload(downloadInfo) {
  const message = {
    action: "download",
    url: downloadInfo.url,
    filename: downloadInfo.filename || "",
    referrer: downloadInfo.referrer || "",
    cookies: downloadInfo.cookies || "",
    userAgent: downloadInfo.userAgent || "",
    fileSize: downloadInfo.fileSize || 0,
    mimeType: downloadInfo.mimeType || ""
  };

  sendToNativeHost(message)
    .then((response) => {
      if (response && response.status === "accepted") {
        showNotification("Linux IDM", "Download captured: " + (downloadInfo.filename || "file"));
      } else {
        fallbackDownload(downloadInfo.url);
      }
    })
    .catch(() => {
      fallbackDownload(downloadInfo.url);
    });
}

function fallbackDownload(url) {
  chrome.downloads.download({ url: url });
}

function shouldIntercept(filename, mimeType, fileSize) {
  const videoExts = [".mp4", ".mkv", ".avi", ".webm", ".flv", ".mov", ".wmv", ".m4v"];
  const audioExts = [".mp3", ".flac", ".wav", ".ogg", ".aac", ".m4a", ".wma"];
  const archiveExts = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"];
  const docExts = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".epub"];
  const execExts = [".exe", ".msi", ".deb", ".rpm", ".appimage", ".dmg", ".pkg", ".run"];

  const allExts = [...videoExts, ...audioExts, ...archiveExts, ...docExts, ...execExts];

  if (filename) {
    const lower = filename.toLowerCase();
    for (const ext of allExts) {
      if (lower.endsWith(ext)) return true;
    }
  }

  if (fileSize && fileSize > 5 * 1024 * 1024) return true;

  const interceptMimes = [
    "video/", "audio/", "application/zip", "application/x-rar",
    "application/x-7z", "application/pdf", "application/octet-stream",
    "application/x-executable", "application/x-msdownload"
  ];

  if (mimeType) {
    for (const mime of interceptMimes) {
      if (mimeType.startsWith(mime)) return true;
    }
  }

  return false;
}

chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
  if (!autoCapture) return;
  if (downloadItem.byExtensionId) return;

  chrome.storage.local.get(["autoCapture"], (result) => {
    if (result.autoCapture === false) return;

    if (shouldIntercept(downloadItem.filename, downloadItem.mime, downloadItem.fileSize)) {
      chrome.tabs.get(downloadItem.tabId, (tab) => {
        const referrer = tab ? tab.url : "";
        captureDownload({
          url: downloadItem.url,
          filename: downloadItem.filename,
          referrer: referrer,
          fileSize: downloadItem.fileSize,
          mimeType: downloadItem.mime
        });
        chrome.downloads.cancel(downloadItem.id);
      });
    }
  });
});

chrome.contextMenus.create({
  id: "download-with-linux-idm",
  title: "Download with Linux IDM",
  contexts: ["link", "video", "audio", "page"]
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  let url = "";
  let referrer = "";

  if (info.linkUrl) {
    url = info.linkUrl;
    referrer = info.pageUrl;
  } else if (info.srcUrl) {
    url = info.srcUrl;
    referrer = info.pageUrl;
  } else if (info.pageUrl) {
    url = info.pageUrl;
    referrer = info.pageUrl;
  }

  if (url) {
    captureDownload({
      url: url,
      referrer: referrer,
      filename: url.split("/").pop().split("?")[0] || ""
    });
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "capture_download") {
    chrome.tabs.get(sender.tab.id, (tab) => {
      captureDownload({
        url: message.url,
        filename: message.filename || "",
        referrer: tab ? tab.url : message.referrer || "",
        mimeType: message.mimeType || ""
      });
    });
    sendResponse({ status: "captured" });
    return true;
  }

  if (message.type === "video_detected") {
    chrome.storage.local.get(["autoCapture"], (result) => {
      if (result.autoCapture !== false) {
        captureDownload({
          url: message.url,
          filename: message.filename || "video",
          referrer: message.referrer || "",
          mimeType: "video/mp4"
        });
      }
    });
    sendResponse({ status: "ok" });
    return true;
  }

  if (message.type === "get_status") {
    sendResponse({
      isConnected: isConnected,
      downloadCount: downloadCount,
      autoCapture: autoCapture
    });
    return true;
  }

  if (message.type === "manual_download") {
    captureDownload({
      url: message.url,
      filename: message.url.split("/").pop().split("?")[0] || "download",
      referrer: ""
    });
    sendResponse({ status: "captured" });
    return true;
  }

  if (message.type === "set_auto_capture") {
    autoCapture = message.value;
    chrome.storage.local.set({ autoCapture: message.value });
    sendResponse({ status: "ok" });
    return true;
  }

  return false;
});

chrome.storage.local.get(["autoCapture", "downloadCount"], (result) => {
  if (result.autoCapture !== undefined) autoCapture = result.autoCapture;
  if (result.downloadCount !== undefined) downloadCount = result.downloadCount;
});

connectNativeHost();
