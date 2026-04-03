document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("status");
  const downloadCountEl = document.getElementById("downloadCount");
  const currentSpeedEl = document.getElementById("currentSpeed");
  const urlInput = document.getElementById("urlInput");
  const addBtn = document.getElementById("addBtn");
  const autoCaptureEl = document.getElementById("autoCapture");

  chrome.runtime.sendMessage({ type: "get_status" }, (response) => {
    if (chrome.runtime.lastError || !response) {
      setStatus(false);
      return;
    }
    setStatus(response.isConnected);
    downloadCountEl.textContent = response.downloadCount || 0;
    autoCaptureEl.checked = response.autoCapture !== false;
  });

  chrome.storage.local.get(["currentSpeed"], (result) => {
    if (result.currentSpeed) {
      currentSpeedEl.textContent = result.currentSpeed;
    }
  });

  function setStatus(connected) {
    if (connected) {
      statusEl.classList.add("connected");
      statusEl.classList.remove("disconnected");
      statusEl.querySelector(".status-text").textContent = "Connected";
    } else {
      statusEl.classList.remove("connected");
      statusEl.classList.add("disconnected");
      statusEl.querySelector(".status-text").textContent = "Disconnected";
    }
  }

  addBtn.addEventListener("click", () => {
    const url = urlInput.value.trim();
    if (!url) return;

    try {
      new URL(url);
    } catch {
      urlInput.classList.add("error");
      setTimeout(() => urlInput.classList.remove("error"), 1000);
      return;
    }

    chrome.runtime.sendMessage({
      type: "manual_download",
      url: url
    }, () => {
      urlInput.value = "";
      downloadCountEl.textContent = parseInt(downloadCountEl.textContent, 10) + 1;
    });
  });

  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") addBtn.click();
  });

  autoCaptureEl.addEventListener("change", () => {
    chrome.runtime.sendMessage({
      type: "set_auto_capture",
      value: autoCaptureEl.checked
    });
  });

  chrome.storage.onChanged.addListener((changes) => {
    if (changes.downloadCount) {
      downloadCountEl.textContent = changes.downloadCount.newValue || 0;
    }
    if (changes.currentSpeed) {
      currentSpeedEl.textContent = changes.currentSpeed.newValue || "0 KB/s";
    }
  });
});
