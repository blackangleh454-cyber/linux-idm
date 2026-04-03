# 🐧 LinuxIDM

### High-Speed Download Manager for Linux - Internet Download Manager Clone

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green.svg)](https://pypi.org/project/PyQt5/)
[![Aria2](https://img.shields.io/badge/Aria2-Backend-orange.svg)](https://aria2.github.io/)

---

## ✨ Features

- 🚀 **Multi-threaded Downloads** - Accelerate downloads with up to 16 connections
- 🌐 **Browser Integration** - Catch downloads directly from Chrome, Firefox, Brave, and Chromium
- 🎯 **Pause/Resume** - Never lose progress on large files
- 📁 **Category Organization** - Keep downloads organized by type
- 🖥️ **Modern GUI** - Clean, dark-themed interface built with PyQt5
- ⚡ **Fast & Lightweight** - Powered by aria2c for maximum speed
- 🔧 **Cross-Distro** - Works on Ubuntu, Debian, Fedora, Arch, and more

---

## 📸 Screenshots

```
┌─────────────────────────────────────────────────────────┐
│  LinuxIDM - Download Manager          [─] [□] [✕]       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  +──────────────┬────────────────────────────────┐      │
│  Categories     │  Downloads                     │      │
│  ────────────   ├────────────────────────────────┤      │
│  📁 All         │  ┌────────────────────────────┐ │      │
│  📥 General     │  │ file.zip          85% ████░│ │      │
│  🎬 Video       │  │ 45.2 MB / 53.1 MB  12.5 MB │ │      │
│  🎵 Audio       │  │ ETA: 00:45    [⏸][✕][📁]  │ │      │
│  🖼️ Images      │  └────────────────────────────┘ │      │
│  📄 Documents   │                                │      │
│                 │  ┌────────────────────────────┐ │      │
│  ────────────   │  │ movie.mp4        Queued    │ │      │
│  + Add URL       │  └────────────────────────────┘ │      │
│                 │                                │      │
│  ────────────   ├────────────────────────────────┤      │
│  ⚙️ Settings    │  Active: 1  │  Speed: 12.5 MB/s │      │
└─────────────────┴────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| GUI Framework | PyQt5 |
| Download Engine | aria2 |
| IPC | Unix Socket |
| Browser Integration | Native Messaging API |
| Language | Python 3.7+ |

---

## 🚀 Quick Install

```bash
# Clone the repository
git clone https://github.com/blackangleh454-cyber/linux-idm.git
cd linux-idm

# Run the installer
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
# Install dependencies
sudo apt install aria2 python3-pip python3-pyqt5

# Install Python packages
pip3 install -r requirements.txt

# Run the application
python3 main.py
```

---

## 📋 Browser Extension Setup

### Chrome / Chromium / Brave
1. Open `chrome://extensions`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select the `extension` folder
5. Download links will now show "Download with LinuxIDM" option

### Firefox
1. Open `about:debugging`
2. Click **This Firefox** → **Load Temporary Add-on**
3. Select `extension/manifest.json`

---

## ⌨️ Usage

```bash
# Launch the GUI
linux-idm

# Download directly from CLI
linux-idm https://example.com/file.zip

# Start minimized to tray
linux-idm --minimized
```

---

## 🔧 Configuration

Download settings can be configured in the Settings panel:
- Default download path
- Number of connections (1-16)
- Speed limits
- Auto-start with system

---

## 📁 Project Structure

```
linux-idm/
├── core/              # Download engine & browser integration
├── ui/                # PyQt5 GUI components
├── extension/         # Browser extension (Chrome/Firefox)
├── native_host/       # Native messaging host
├── icons/             # Application icons
├── main.py            # Application entry point
├── ipc_server.py      # IPC server for browser communication
├── requirements.txt   # Python dependencies
└── install.sh         # Installation script
```

---

## 🌟 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Mirza Muhammad Usman**
- 🛡️ Cybersecurity Engineer
- 🌐 Network Architect (CCNA)
- 🔍 Security Researcher (CISSP)
- 🤖 AI Agent Builder

[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=flat&logo=twitter&logoColor=white)](https://twitter.com/blackangleh454)
[![GitHub](https://img.shields.io/badge/GitHub-blackangleh454--cyber?style=flat&logo=github&logoColor=white)](https://github.com/blackangleh454-cyber)

---

<p align="center">
  <sub>Built with ❤️ for the Linux community</sub>
</p>
