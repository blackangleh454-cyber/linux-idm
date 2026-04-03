#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

BOLD='\033[1m'

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/share/linux-idm"
DESKTOP_FILE="$HOME/.local/share/applications/linux-idm.desktop"
BIN_LINK="$HOME/.local/bin/linux-idm"

print_banner() {
    echo -e "${CYAN}"
    echo "  ╔══════════════════════════════════════╗"
    echo "  ║      LinuxIDM - Download Manager     ║"
    echo "  ║         Installer v1.0.0             ║"
    echo "  ╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    echo -e "${BLUE}[*] Detected distro: ${BOLD}$DISTRO${NC}"
}

install_dependencies() {
    echo -e "${BLUE}[*] Installing dependencies...${NC}"

    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            sudo apt-get update -qq
            sudo apt-get install -y -qq aria2 python3 python3-pip python3-pyqt5 python3-pyqt5.qtwidgets > /dev/null 2>&1
            ;;
        fedora)
            sudo dnf install -y aria2 python3 python3-pip python3-qt5 > /dev/null 2>&1
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm aria2 python python-pip python-pyqt5 > /dev/null 2>&1
            ;;
        opensuse*|sles)
            sudo zypper install -y aria2 python3 python3-pip python3-qt5 > /dev/null 2>&1
            ;;
        centos|rhel|almalinux|rocky)
            sudo yum install -y aria2 python3 python3-pip > /dev/null 2>&1
            pip3 install --user PyQt5 > /dev/null 2>&1
            ;;
        *)
            echo -e "${YELLOW}[!] Unknown distro. Trying pip install...${NC}"
            pip3 install --user PyQt5 > /dev/null 2>&1
            ;;
    esac

    pip3 install --user -r "$APP_DIR/requirements.txt" > /dev/null 2>&1 || true

    echo -e "${GREEN}[✓] Dependencies installed${NC}"
}

setup_directories() {
    echo -e "${BLUE}[*] Setting up directories...${NC}"
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/.local/share/applications"
    mkdir -p "$HOME/Downloads"
    echo -e "${GREEN}[✓] Directories created${NC}"
}

copy_files() {
    echo -e "${BLUE}[*] Copying files...${NC}"
    cp -r "$APP_DIR/core" "$INSTALL_DIR/"
    cp -r "$APP_DIR/ui" "$INSTALL_DIR/"
    cp -r "$APP_DIR/extension" "$INSTALL_DIR/"
    cp -r "$APP_DIR/native_host" "$INSTALL_DIR/"
    cp "$APP_DIR/main.py" "$INSTALL_DIR/"
    cp "$APP_DIR/ipc_server.py" "$INSTALL_DIR/"
    cp "$APP_DIR/requirements.txt" "$INSTALL_DIR/"
    echo -e "${GREEN}[✓] Files copied${NC}"
}

setup_native_host() {
    echo -e "${BLUE}[*] Setting up browser integration...${NC}"

    NATIVE_HOST_SCRIPT="$INSTALL_DIR/native_host/host.py"
    chmod +x "$NATIVE_HOST_SCRIPT"

    CHROME_NATIVE_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
    CHROMIUM_NATIVE_DIR="$HOME/.config/chromium/NativeMessagingHosts"
    BRAVE_NATIVE_DIR="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
    FIREFOX_NATIVE_DIR="$HOME/.mozilla/native-messaging-hosts"

    HOST_NAME="com.linuxidm.downloader"

    for NATIVE_DIR in "$CHROME_NATIVE_DIR" "$CHROMIUM_NATIVE_DIR" "$BRAVE_NATIVE_DIR"; do
        if [ -d "$(dirname "$NATIVE_DIR")" ]; then
            mkdir -p "$NATIVE_DIR"
            cat > "$NATIVE_DIR/$HOST_NAME.json" << MANIFEST
{
    "name": "$HOST_NAME",
    "description": "LinuxIDM Download Manager",
    "path": "$NATIVE_HOST_SCRIPT",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://*/"
    ]
}
MANIFEST
            echo -e "${GREEN}[✓] Registered for Chrome/Chromium/Brave${NC}"
        fi
    done

    if [ -d "$(dirname "$FIREFOX_NATIVE_DIR")" ]; then
        mkdir -p "$FIREFOX_NATIVE_DIR"
        cat > "$FIREFOX_NATIVE_DIR/$HOST_NAME.json" << MANIFEST
{
    "name": "$HOST_NAME",
    "description": "LinuxIDM Download Manager",
    "path": "$NATIVE_HOST_SCRIPT",
    "type": "stdio",
    "allowed_extensions": ["linux-idm@extension"]
}
MANIFEST
        echo -e "${GREEN}[✓] Registered for Firefox${NC}"
    fi
}

create_desktop_entry() {
    echo -e "${BLUE}[*] Creating desktop entry...${NC}"

    cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Name=LinuxIDM
Comment=High-Speed Download Manager
GenericName=Download Manager
Exec=/usr/bin/env python3 $INSTALL_DIR/main.py
Icon=download
Terminal=false
Type=Application
Categories=Network;FileTransfer;
Keywords=download;internet;manager;idm;
StartupNotify=true
MimeType=x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;
DESKTOP

    echo -e "${GREEN}[✓] Desktop entry created${NC}"
}

create_launcher() {
    echo -e "${BLUE}[*] Creating launcher...${NC}"

    cat > "$BIN_LINK" << LAUNCHER
#!/bin/bash
exec /usr/bin/env python3 "$INSTALL_DIR/main.py" "\$@"
LAUNCHER
    chmod +x "$BIN_LINK"

    echo -e "${GREEN}[✓] Launcher created at $BIN_LINK${NC}"
}

setup_autostart() {
    AUTOSTART_DIR="$HOME/.config/autostart"
    AUTOSTART_FILE="$AUTOSTART_DIR/linux-idm.desktop"

    read -p "$(echo -e "${YELLOW}Start LinuxIDM automatically on login? [y/N]: ${NC}")" AUTO_START
    if [[ "$AUTO_START" =~ ^[Yy]$ ]]; then
        mkdir -p "$AUTOSTART_DIR"
        cat > "$AUTOSTART_FILE" << DESKTOP
[Desktop Entry]
Name=LinuxIDM
Comment=High-Speed Download Manager
Exec=/usr/bin/env python3 $INSTALL_DIR/main.py --minimized
Icon=download
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
DESKTOP
        echo -e "${GREEN}[✓] Autostart configured${NC}"
    fi
}

print_usage() {
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo -e "  ${BOLD}linux-idm${NC}          - Launch the application"
    echo -e "  ${BOLD}linux-idm <url>${NC}    - Download a URL directly"
    echo ""
    echo -e "${CYAN}Browser Extension:${NC}"
    echo -e "  1. Open Chrome/Chromium/Brave"
    echo -e "  2. Go to chrome://extensions"
    echo -e "  3. Enable Developer Mode"
    echo -e "  4. Click 'Load unpacked'"
    echo -e "  5. Select: $INSTALL_DIR/extension"
    echo ""
    echo -e "${CYAN}Firefox Extension:${NC}"
    echo -e "  1. Open Firefox"
    echo -e "  2. Go to about:debugging"
    echo -e "  3. Click 'This Firefox' > 'Load Temporary Add-on'"
    echo -e "  4. Select: $INSTALL_DIR/extension/manifest.json"
    echo ""
}

main() {
    print_banner
    detect_distro
    install_dependencies
    setup_directories
    copy_files
    setup_native_host
    create_desktop_entry
    create_launcher
    setup_autostart

    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║    Installation Complete! ✓          ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${NC}"

    print_usage

    read -p "$(echo -e "${YELLOW}Launch LinuxIDM now? [Y/n]: ${NC}")" LAUNCH
    if [[ ! "$LAUNCH" =~ ^[Nn]$ ]]; then
        echo -e "${BLUE}[*] Launching LinuxIDM...${NC}"
        /usr/bin/env python3 "$INSTALL_DIR/main.py" &
    fi
}

main "$@"
