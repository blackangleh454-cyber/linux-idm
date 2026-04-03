(function () {
  "use strict";

  const VIDEO_SELECTORS = [
    "video",
    "video source",
    "iframe[src*='youtube']",
    "iframe[src*='vimeo']",
    "iframe[src*='dailymotion']",
    "iframe[src*='twitch']"
  ];

  const DOWNLOAD_SELECTORS = [
    "a[href*='.mp4']",
    "a[href*='.mkv']",
    "a[href*='.mp3']",
    "a[href*='.zip']",
    "a[href*='.rar']",
    "a[href*='.pdf']",
    "a[href*='.exe']",
    "a[href*='.deb']",
    "a[href*='.tar']",
    "a[href*='.gz']",
    "a[download]",
    "a[href*='/download']",
    "a[href*='attachment']"
  ];

  const capturedUrls = new Set();

  function notifyBackground(type, data) {
    chrome.runtime.sendMessage({ type: type, ...data });
  }

  function getFilenameFromUrl(url) {
    try {
      const pathname = new URL(url).pathname;
      const segments = pathname.split("/");
      const last = segments[segments.length - 1];
      return last.split("?")[0] || "";
    } catch {
      return "";
    }
  }

  function captureVideoUrl(url, filename) {
    if (!url || capturedUrls.has(url)) return;
    capturedUrls.add(url);
    notifyBackground("video_detected", {
      url: url,
      filename: filename || getFilenameFromUrl(url),
      referrer: window.location.href
    });
  }

  function captureDownloadUrl(url, filename) {
    if (!url || capturedUrls.has(url)) return;
    capturedUrls.add(url);
    notifyBackground("capture_download", {
      url: url,
      filename: filename || getFilenameFromUrl(url),
      referrer: window.location.href
    });
  }

  function scanVideoElements() {
    document.querySelectorAll("video").forEach((video) => {
      if (video.src) captureVideoUrl(video.src, getFilenameFromUrl(video.src));
      if (video.currentSrc) captureVideoUrl(video.currentSrc, getFilenameFromUrl(video.currentSrc));
    });

    document.querySelectorAll("video source").forEach((source) => {
      if (source.src) captureVideoUrl(source.src, getFilenameFromUrl(source.src));
    });
  }

  function scanDownloadLinks() {
    document.querySelectorAll(DOWNLOAD_SELECTORS.join(",")).forEach((link) => {
      if (link.href && !link.href.startsWith("javascript:")) {
        link.addEventListener("click", (e) => {
          e.preventDefault();
          captureDownloadUrl(link.href, link.download || getFilenameFromUrl(link.href));
        }, { once: true });
      }
    });
  }

  function interceptXHR() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url) {
      this._idmUrl = url;
      return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function () {
      this.addEventListener("load", function () {
        if (this._idmUrl) {
          const contentType = this.getResponseHeader("Content-Type") || "";
          const contentLength = parseInt(this.getResponseHeader("Content-Length") || "0", 10);
          if (contentLength > 5 * 1024 * 1024 || contentType.includes("video") || contentType.includes("audio")) {
            captureVideoUrl(this._idmUrl, getFilenameFromUrl(this._idmUrl));
          }
        }
      });
      return originalSend.apply(this, arguments);
    };
  }

  function interceptFetch() {
    const originalFetch = window.fetch;
    window.fetch = function (input, init) {
      const url = typeof input === "string" ? input : input.url;
      return originalFetch.apply(this, arguments).then((response) => {
        if (url) {
          const contentType = response.headers.get("Content-Type") || "";
          const contentLength = parseInt(response.headers.get("Content-Length") || "0", 10);
          if (contentLength > 5 * 1024 * 1024 || contentType.includes("video") || contentType.includes("audio")) {
            captureVideoUrl(url, getFilenameFromUrl(url));
          }
        }
        return response;
      });
    };
  }

  function observeDOM() {
    const observer = new MutationObserver(() => {
      scanVideoElements();
      scanDownloadLinks();
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["src", "href"]
    });
  }

  function handleYouTube() {
    if (!window.location.hostname.includes("youtube.com")) return;

    const observer = new MutationObserver(() => {
      const video = document.querySelector("video");
      if (video && video.src && video.src.startsWith("http")) {
        captureVideoUrl(video.src, document.title + ".mp4");
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  function handleVimeo() {
    if (!window.location.hostname.includes("vimeo.com")) return;

    const observer = new MutationObserver(() => {
      const video = document.querySelector("video");
      if (video && (video.src || video.currentSrc)) {
        captureVideoUrl(video.src || video.currentSrc, document.title + ".mp4");
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  function handleMediaSource() {
    if (typeof MediaSource === "undefined") return;

    const originalAddSourceBuffer = MediaSource.prototype.addSourceBuffer;
    MediaSource.prototype.addSourceBuffer = function (mimeType) {
      if (mimeType.includes("video") || mimeType.includes("audio")) {
        const url = window.location.href;
        captureVideoUrl(url, document.title + (mimeType.includes("video") ? ".mp4" : ".mp3"));
      }
      return originalAddSourceBuffer.apply(this, arguments);
    };
  }

  function init() {
    scanVideoElements();
    scanDownloadLinks();
    interceptXHR();
    interceptFetch();
    handleYouTube();
    handleVimeo();
    handleMediaSource();

    if (document.readyState === "complete") {
      observeDOM();
    } else {
      window.addEventListener("load", observeDOM);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
