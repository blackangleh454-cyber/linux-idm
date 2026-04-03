import os
import sys
import uuid
from typing import Optional, List, Dict, Any
from enum import Enum

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QToolBar, QAction, QStatusBar, QListWidget,
    QListWidgetItem, QScrollArea, QFrame, QSplitter, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QComboBox, QDialog, QFormLayout,
    QSpinBox, QCheckBox, QFileDialog, QDialogButtonBox, QMenu,
    QSystemTrayIcon, QGraphicsDropShadowEffect, QApplication,
    QSizePolicy, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import (
    Qt, QSize, QTimer, QPoint, QMimeData, QUrl, pyqtSignal,
    QPropertyAnimation, QEasingCurve, QRect, QEvent
)
from PyQt5.QtGui import (
    QIcon, QFont, QColor, QDragEnterEvent, QDropEvent,
    QCursor, QPainter, QPen, QBrush, QPixmap
)

from .theme import Colors, Theme
from .widgets import (
    DownloadCardWidget, AnimatedProgressBar, SpeedGraphWidget,
    StatsWidget, AddUrlDialog, DownloadStatus
)


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None, current_settings: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._settings = current_settings or {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Settings")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: 8px;
        """)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)

        general_group = self._create_group("General")
        general_form = QFormLayout()
        general_form.setSpacing(12)

        dl_label = QLabel("Default Download Path")
        dl_label.setStyleSheet(self._label_style())
        path_row = QHBoxLayout()
        self._dl_path_input = QLineEdit(self._settings.get("download_path", os.path.expanduser("~/Downloads")))
        self._dl_path_input.setMinimumHeight(36)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedHeight(36)
        browse_btn.clicked.connect(self._browse_download_path)
        path_row.addWidget(self._dl_path_input, 1)
        path_row.addWidget(browse_btn)
        general_form.addRow(dl_label, path_row)

        general_group.layout().addLayout(general_form)
        container_layout.addWidget(general_group)

        conn_group = self._create_group("Connection")
        conn_form = QFormLayout()
        conn_form.setSpacing(12)

        max_conn_label = QLabel("Max Connections per Download")
        max_conn_label.setStyleSheet(self._label_style())
        self._max_conn_spin = QSpinBox()
        self._max_conn_spin.setRange(1, 32)
        self._max_conn_spin.setValue(self._settings.get("max_connections", 8))
        self._max_conn_spin.setMinimumHeight(36)
        conn_form.addRow(max_conn_label, self._max_conn_spin)

        max_speed_label = QLabel("Max Speed (KB/s, 0 = unlimited)")
        max_speed_label.setStyleSheet(self._label_style())
        self._max_speed_spin = QSpinBox()
        self._max_speed_spin.setRange(0, 1024000)
        self._max_speed_spin.setSingleStep(100)
        self._max_speed_spin.setValue(self._settings.get("max_speed", 0))
        self._max_speed_spin.setMinimumHeight(36)
        conn_form.addRow(max_speed_label, self._max_speed_spin)

        max_dl_label = QLabel("Max Concurrent Downloads")
        max_dl_label.setStyleSheet(self._label_style())
        self._max_dl_spin = QSpinBox()
        self._max_dl_spin.setRange(1, 20)
        self._max_dl_spin.setValue(self._settings.get("max_downloads", 5))
        self._max_dl_spin.setMinimumHeight(36)
        conn_form.addRow(max_dl_label, self._max_dl_spin)

        conn_group.layout().addLayout(conn_form)
        container_layout.addWidget(conn_group)

        int_group = self._create_group("Integration")
        int_layout = QVBoxLayout()
        int_layout.setSpacing(12)

        self._browser_integration_cb = QCheckBox("Enable browser integration")
        self._browser_integration_cb.setChecked(self._settings.get("browser_integration", True))
        int_layout.addWidget(self._browser_integration_cb)

        self._autostart_cb = QCheckBox("Start with system")
        self._autostart_cb.setChecked(self._settings.get("autostart", False))
        int_layout.addWidget(self._autostart_cb)

        self._notifications_cb = QCheckBox("Show desktop notifications")
        self._notifications_cb.setChecked(self._settings.get("notifications", True))
        int_layout.addWidget(self._notifications_cb)

        self._minimize_tray_cb = QCheckBox("Minimize to system tray")
        self._minimize_tray_cb.setChecked(self._settings.get("minimize_to_tray", True))
        int_layout.addWidget(self._minimize_tray_cb)

        int_group.layout().addLayout(int_layout)
        container_layout.addWidget(int_group)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)

        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Save")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setMinimumHeight(36)

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setMinimumHeight(36)

        apply_btn = buttons.button(QDialogButtonBox.Apply)
        apply_btn.setMinimumHeight(36)

        layout.addWidget(buttons)

    def _create_group(self, title: str) -> QFrame:
        group = QFrame()
        group.setObjectName("statsPanel")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        label = QLabel(title)
        label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {Colors.ACCENT_BLUE};
            margin-bottom: 4px;
        """)
        layout.addWidget(label)
        return group

    def _label_style(self) -> str:
        return f"font-size: 13px; font-weight: 500; color: {Colors.TEXT_SECONDARY};"

    def _browse_download_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self._dl_path_input.text())
        if path:
            self._dl_path_input.setText(path)

    def _get_settings(self) -> Dict[str, Any]:
        return {
            "download_path": self._dl_path_input.text(),
            "max_connections": self._max_conn_spin.value(),
            "max_speed": self._max_speed_spin.value(),
            "max_downloads": self._max_dl_spin.value(),
            "browser_integration": self._browser_integration_cb.isChecked(),
            "autostart": self._autostart_cb.isChecked(),
            "notifications": self._notifications_cb.isChecked(),
            "minimize_to_tray": self._minimize_tray_cb.isChecked(),
        }

    def _apply_settings(self) -> None:
        self.settings_changed.emit(self._get_settings())

    def _save_and_accept(self) -> None:
        self.settings_changed.emit(self._get_settings())
        self.accept()


class SortOption(Enum):
    NAME = "name"
    DATE = "date"
    SIZE = "size"
    STATUS = "status"
    SPEED = "speed"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._downloads: Dict[str, Dict[str, Any]] = {}
        self._download_cards: Dict[str, DownloadCardWidget] = {}
        self._current_filter: str = "all"
        self._current_search: str = ""
        self._sort_option: SortOption = SortOption.DATE
        self._sort_ascending: bool = False
        self._settings: Dict[str, Any] = {
            "download_path": os.path.expanduser("~/Downloads"),
            "max_connections": 8,
            "max_speed": 0,
            "max_downloads": 5,
            "browser_integration": True,
            "autostart": False,
            "notifications": True,
            "minimize_to_tray": True,
        }
        self._setup_ui()
        self._setup_tray()
        self._setup_timer()

    def _setup_ui(self) -> None:
        self.setWindowTitle("LinuxIDM - Download Manager")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self.setAcceptDrops(True)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_menubar()
        self._setup_toolbar()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter {{ background-color: {Colors.BG_DARK}; }}")

        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)

        content = self._create_content_area()
        splitter.addWidget(content)

        splitter.setSizes([200, 900])
        main_layout.addWidget(splitter)

        self._setup_statusbar()

    def _setup_menubar(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        add_action = QAction("&Add Download", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self._show_add_dialog)
        file_menu.addAction(add_action)

        file_menu.addSeparator()

        import_action = QAction("&Import URLs from File...", self)
        import_action.triggered.connect(self._import_urls)
        file_menu.addAction(import_action)

        export_action = QAction("&Export Download List...", self)
        export_action.triggered.connect(self._export_list)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")

        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut("Ctrl+A")
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut("Ctrl+P")
        preferences_action.triggered.connect(self._show_settings)
        edit_menu.addAction(preferences_action)

        view_menu = menubar.addMenu("&View")

        toolbar_action = QAction("&Toolbar", self)
        toolbar_action.setCheckable(True)
        toolbar_action.setChecked(True)
        view_menu.addAction(toolbar_action)

        sidebar_action = QAction("&Sidebar", self)
        sidebar_action.setCheckable(True)
        sidebar_action.setChecked(True)
        view_menu.addAction(sidebar_action)

        view_menu.addSeparator()

        sort_menu = view_menu.addMenu("&Sort By")

        sort_name = QAction("&Name", self)
        sort_name.triggered.connect(lambda: self._set_sort(SortOption.NAME))
        sort_menu.addAction(sort_name)

        sort_date = QAction("&Date", self)
        sort_date.triggered.connect(lambda: self._set_sort(SortOption.DATE))
        sort_menu.addAction(sort_date)

        sort_size = QAction("&Size", self)
        sort_size.triggered.connect(lambda: self._set_sort(SortOption.SIZE))
        sort_menu.addAction(sort_size)

        sort_status = QAction("&Status", self)
        sort_status.triggered.connect(lambda: self._set_sort(SortOption.STATUS))
        sort_menu.addAction(sort_status)

        sort_speed = QAction("S&peed", self)
        sort_speed.triggered.connect(lambda: self._set_sort(SortOption.SPEED))
        sort_menu.addAction(sort_speed)

        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        add_btn = QPushButton("+ Add URL")
        add_btn.setObjectName("primaryButton")
        add_btn.setMinimumHeight(34)
        add_btn.clicked.connect(self._show_add_dialog)
        toolbar.addWidget(add_btn)

        toolbar.addSeparator()

        pause_all_btn = QPushButton("⏸ Pause All")
        pause_all_btn.setMinimumHeight(34)
        pause_all_btn.clicked.connect(self._pause_all)
        toolbar.addWidget(pause_all_btn)

        resume_all_btn = QPushButton("▶ Resume All")
        resume_all_btn.setMinimumHeight(34)
        resume_all_btn.clicked.connect(self._resume_all)
        toolbar.addWidget(resume_all_btn)

        toolbar.addSeparator()

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search downloads...")
        search_input.setMinimumHeight(34)
        search_input.setMaximumWidth(250)
        search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(search_input)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setMinimumHeight(34)
        settings_btn.clicked.connect(self._show_settings)
        toolbar.addWidget(settings_btn)

        about_btn = QPushButton("? About")
        about_btn.setMinimumHeight(34)
        about_btn.clicked.connect(self._show_about)
        toolbar.addWidget(about_btn)

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(240)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        categories_label = QLabel("Categories")
        categories_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {Colors.TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0 8px;
            margin-bottom: 4px;
        """)
        layout.addWidget(categories_label)

        categories = [
            ("all", "All Downloads", "📥"),
            ("downloading", "Downloading", "↓"),
            ("completed", "Completed", "✓"),
            ("paused", "Paused", "⏸"),
            ("queued", "Queued", "◷"),
            ("error", "Errors", "!"),
        ]

        self._category_buttons: Dict[str, QPushButton] = {}
        for cat_id, cat_name, icon in categories:
            btn = QPushButton(f"  {icon}  {cat_name}")
            btn.setCheckable(True)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(self._category_button_style(cat_id == "all"))
            btn.clicked.connect(lambda checked, cid=cat_id: self._set_category(cid))
            layout.addWidget(btn)
            self._category_buttons[cat_id] = btn

        self._category_buttons["all"].setChecked(True)

        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        type_label = QLabel("File Types")
        type_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {Colors.TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0 8px;
            margin-top: 8px;
            margin-bottom: 4px;
        """)
        layout.addWidget(type_label)

        file_types = [
            ("videos", "Videos", "🎬"),
            ("music", "Music", "🎵"),
            ("documents", "Documents", "📄"),
            ("archives", "Archives", "📦"),
            ("compressed", "Compressed", "🗜"),
        ]

        for cat_id, cat_name, icon in file_types:
            btn = QPushButton(f"  {icon}  {cat_name}")
            btn.setCheckable(True)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(self._category_button_style(False))
            btn.clicked.connect(lambda checked, cid=cat_id: self._set_category(cid))
            layout.addWidget(btn)
            self._category_buttons[cat_id] = btn

        layout.addStretch()

        self._stats_widget = StatsWidget()
        layout.addWidget(self._stats_widget)

        self._speed_graph = SpeedGraphWidget()
        layout.addWidget(self._speed_graph)

        return sidebar

    def _category_button_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: rgba(0, 212, 255, 0.15);
                    border: 1px solid transparent;
                    border-radius: 8px;
                    color: {Colors.ACCENT_BLUE};
                    text-align: left;
                    padding: 0 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: rgba(0, 212, 255, 0.25);
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 8px;
                color: {Colors.TEXT_SECONDARY};
                text-align: left;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_CARD};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: rgba(0, 212, 255, 0.15);
                color: {Colors.ACCENT_BLUE};
            }}
        """

    def _create_content_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)

        self._category_title = QLabel("All Downloads")
        self._category_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
        """)
        header.addWidget(self._category_title)

        header.addStretch()

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["Sort: Date", "Sort: Name", "Sort: Size", "Sort: Status", "Sort: Speed"])
        self._sort_combo.setMinimumHeight(32)
        self._sort_combo.setMaximumWidth(150)
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        header.addWidget(self._sort_combo)

        self._download_count_label = QLabel("0 items")
        self._download_count_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_MUTED};
        """)
        header.addWidget(self._download_count_label)

        layout.addLayout(header)

        self._download_list = QListWidget()
        self._download_list.setSpacing(4)
        self._download_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self._download_list.setSelectionMode(QAbstractItemView.NoSelection)
        self._download_list.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self._download_list)

        return container

    def _setup_statusbar(self) -> None:
        statusbar = self.statusBar()

        self._status_speed = QLabel("↓ 0 KB/s")
        self._status_speed.setStyleSheet(f"""
            color: {Colors.ACCENT_BLUE};
            font-weight: 600;
            padding: 0 8px;
        """)
        statusbar.addWidget(self._status_speed)

        self._status_downloads = QLabel("0 active / 0 total")
        self._status_downloads.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            padding: 0 8px;
        """)
        statusbar.addWidget(self._status_downloads)

        statusbar.addPermanentWidget(QLabel(""))

        self._status_path = QLabel(f"📁 {self._settings['download_path']}")
        self._status_path.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: 11px;
            padding: 0 8px;
        """)
        statusbar.addPermanentWidget(self._status_path)

    def _setup_tray(self) -> None:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(Colors.ACCENT_BLUE)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setPen(QPen(QColor(Colors.BG_DARK), 3))
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "D")
        painter.end()
        tray_icon = QIcon(pixmap)

        self._tray_icon = QSystemTrayIcon(tray_icon, self)
        self._tray_icon.setToolTip("LinuxIDM")

        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        pause_all_action = QAction("Pause All", self)
        pause_all_action.triggered.connect(self._pause_all)
        tray_menu.addAction(pause_all_action)

        self._tray_downloading = QAction("Downloading: 0", self)
        self._tray_downloading.setEnabled(False)
        tray_menu.addAction(self._tray_downloading)

        tray_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_app)
        tray_menu.addAction(exit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._tray_activated)
        self._tray_icon.show()

    def _setup_timer(self) -> None:
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_ui)
        self._update_timer.start(500)

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            for url in mime.urls():
                text = url.toString()
                if text.startswith("http://") or text.startswith("https://") or text.startswith("ftp://"):
                    self._add_download_from_url(text)
        elif mime.hasText():
            text = mime.text().strip()
            if text.startswith("http://") or text.startswith("https://") or text.startswith("ftp://"):
                self._add_download_from_url(text)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:
        if self._settings.get("minimize_to_tray", True):
            event.ignore()
            self.hide()
        else:
            self._exit_app()

    def _exit_app(self) -> None:
        self._tray_icon.hide()
        QApplication.quit()

    def _show_add_dialog(self) -> None:
        dialog = AddUrlDialog(self, self._settings.get("download_path", ""))
        if dialog.exec_() == QDialog.Accepted:
            url = dialog.get_url()
            if url:
                self._add_download_from_url(
                    url=url,
                    filename=dialog.get_filename(),
                    save_path=dialog.get_save_path(),
                    connections=dialog.get_connections(),
                    category=dialog.get_category(),
                )

    def _add_download_from_url(self, url: str, filename: str = "", save_path: str = "", connections: int = 0, category: str = "General") -> None:
        self._add_download(
            url=url,
            filename=filename or "",
            save_path=save_path or self._settings.get("download_path", ""),
            connections=connections or self._settings.get("max_connections", 8),
            category=category,
        )

    def _add_download(
        self,
        url: str,
        filename: str,
        save_path: str,
        connections: int,
        category: str,
    ) -> None:
        download_id = str(uuid.uuid4())

        if not filename:
            filename = url.split("/")[-1].split("?")[0] or "download"

        download_info = {
            "id": download_id,
            "url": url,
            "filename": filename,
            "save_path": save_path,
            "connections": connections,
            "category": category,
            "progress": 0.0,
            "speed": 0.0,
            "size": 0.0,
            "downloaded": 0.0,
            "eta": "--:--",
            "status": DownloadStatus.QUEUED,
        }
        self._downloads[download_id] = download_info

        card = DownloadCardWidget(download_id)
        card.set_filename(filename)
        card.set_url(url)
        card.set_save_path(save_path)
        card.set_connections(connections)
        card.set_status(DownloadStatus.QUEUED)

        card.pause_clicked.connect(self._pause_download)
        card.resume_clicked.connect(self._resume_download)
        card.cancel_clicked.connect(self._cancel_download)
        card.delete_clicked.connect(self._delete_download)
        card.open_clicked.connect(self._open_download)
        card.open_folder_clicked.connect(self._open_folder)
        card.copy_url_clicked.connect(self._copy_url)

        self._download_cards[download_id] = card

        item = QListWidgetItem(self._download_list)
        item.setSizeHint(card.sizeHint())
        self._download_list.addItem(item)
        self._download_list.setItemWidget(item, card)

        self._update_counts()

    def _pause_download(self, download_id: str) -> None:
        if download_id in self._downloads:
            self._downloads[download_id]["status"] = DownloadStatus.PAUSED
            self._download_cards[download_id].set_status(DownloadStatus.PAUSED)
            self._update_counts()

    def _resume_download(self, download_id: str) -> None:
        if download_id in self._downloads:
            self._downloads[download_id]["status"] = DownloadStatus.DOWNLOADING
            self._download_cards[download_id].set_status(DownloadStatus.DOWNLOADING)
            self._update_counts()

    def _cancel_download(self, download_id: str) -> None:
        if download_id in self._downloads:
            self._remove_download_card(download_id)
            del self._downloads[download_id]
            self._update_counts()

    def _delete_download(self, download_id: str) -> None:
        if download_id in self._downloads:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Delete '{self._downloads[download_id]['filename']}' and its file?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._remove_download_card(download_id)
                del self._downloads[download_id]
                self._update_counts()

    def _remove_download_card(self, download_id: str) -> None:
        if download_id in self._download_cards:
            card = self._download_cards[download_id]
            for i in range(self._download_list.count()):
                item = self._download_list.item(i)
                if self._download_list.itemWidget(item) == card:
                    self._download_list.takeItem(i)
                    break
            del self._download_cards[download_id]

    def _open_download(self, download_id: str) -> None:
        if download_id in self._downloads:
            info = self._downloads[download_id]
            filepath = os.path.join(info["save_path"], info["filename"])
            if os.path.exists(filepath):
                os.system(f'xdg-open "{filepath}"')

    def _open_folder(self, download_id: str) -> None:
        if download_id in self._downloads:
            info = self._downloads[download_id]
            if os.path.exists(info["save_path"]):
                os.system(f'xdg-open "{info["save_path"]}"')

    def _copy_url(self, download_id: str) -> None:
        if download_id in self._downloads:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._downloads[download_id]["url"])

    def _pause_all(self) -> None:
        for did, info in self._downloads.items():
            if info["status"] == DownloadStatus.DOWNLOADING:
                info["status"] = DownloadStatus.PAUSED
                self._download_cards[did].set_status(DownloadStatus.PAUSED)
        self._update_counts()

    def _resume_all(self) -> None:
        for did, info in self._downloads.items():
            if info["status"] in (DownloadStatus.PAUSED, DownloadStatus.QUEUED):
                info["status"] = DownloadStatus.DOWNLOADING
                self._download_cards[did].set_status(DownloadStatus.DOWNLOADING)
        self._update_counts()

    def _set_category(self, category: str) -> None:
        self._current_filter = category

        for cat_id, btn in self._category_buttons.items():
            btn.setChecked(cat_id == category)
            btn.setStyleSheet(self._category_button_style(cat_id == category))

        titles = {
            "all": "All Downloads",
            "downloading": "Downloading",
            "completed": "Completed",
            "paused": "Paused",
            "queued": "Queued",
            "error": "Errors",
            "videos": "Videos",
            "music": "Music",
            "documents": "Documents",
            "archives": "Archives",
            "compressed": "Compressed",
        }
        self._category_title.setText(titles.get(category, "Downloads"))
        self._update_counts()

    def _set_sort(self, option: SortOption) -> None:
        self._sort_option = option
        self._update_counts()

    def _on_sort_changed(self, index: int) -> None:
        options = [SortOption.DATE, SortOption.NAME, SortOption.SIZE, SortOption.STATUS, SortOption.SPEED]
        if 0 <= index < len(options):
            self._sort_option = options[index]
            self._update_counts()

    def _on_search_changed(self, text: str) -> None:
        self._current_search = text.lower().strip()
        self._update_counts()

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self, self._settings)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec_()

    def _apply_settings(self, settings: Dict[str, Any]) -> None:
        self._settings.update(settings)
        self._status_path.setText(f"📁 {self._settings['download_path']}")

    def _show_about(self) -> None:
        about_text = """
        <div style="text-align: center;">
            <p style="font-size: 28px; font-weight: 800; margin: 0;">
                <span style="color: #00d4ff;">Linux</span><span style="color: #00ff88;">IDM</span>
            </p>
            <p style="font-size: 11px; color: #64748b; margin: 2px 0 12px 0;">Version 1.0.0</p>
            <div style="background: linear-gradient(90deg, #00d4ff, #a855f7, #ff6b35); height: 2px; margin: 8px 40px; border-radius: 1px;"></div>
            <p style="font-size: 13px; color: #94a3b8; margin: 12px 0 8px 0;">High-Speed Download Manager for Linux</p>
            <p style="font-size: 12px; color: #64748b; margin: 4px 0;">
                16-Connection Multi-Threaded Downloads<br>
                Browser Integration &bull; System Tray &bull; Auto-Resume
            </p>
            <div style="background: linear-gradient(90deg, #ff6b35, #a855f7, #00d4ff); height: 2px; margin: 12px 40px; border-radius: 1px;"></div>
            <p style="font-size: 14px; font-weight: 700; margin: 12px 0 4px 0;">
                <span style="color: #00d4ff;">Built by </span>
                <span style="color: #00ff88;">AI</span>
                <span style="color: #a855f7;"> + </span>
                <span style="color: #ff6b35;">Mirza</span>
            </p>
            <p style="font-size: 10px; color: #64748b; margin: 2px 0 0 0;">Crafted with intelligence & ambition</p>
        </div>
        """
        QMessageBox.about(self, "About LinuxIDM", about_text)

    def _import_urls(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import URLs", "", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "r") as f:
                for line in f:
                    url = line.strip()
                    if url and (url.startswith("http://") or url.startswith("https://") or url.startswith("ftp://")):
                        self._add_download_from_url(url)

    def _export_list(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Download List", "downloads.txt", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                for info in self._downloads.values():
                    f.write(f"{info['url']}\n")

    def _update_counts(self) -> None:
        visible_count = 0
        total_speed = 0.0
        active_count = 0
        queued_count = 0
        completed_count = 0

        for i in range(self._download_list.count()):
            item = self._download_list.item(i)
            card = self._download_list.itemWidget(item)
            if not card:
                continue

            did = card.get_download_id()
            if did not in self._downloads:
                continue

            info = self._downloads[did]
            show = True

            if self._current_filter == "downloading" and info["status"] != DownloadStatus.DOWNLOADING:
                show = False
            elif self._current_filter == "completed" and info["status"] != DownloadStatus.COMPLETED:
                show = False
            elif self._current_filter == "paused" and info["status"] != DownloadStatus.PAUSED:
                show = False
            elif self._current_filter == "queued" and info["status"] != DownloadStatus.QUEUED:
                show = False
            elif self._current_filter == "error" and info["status"] != DownloadStatus.ERROR:
                show = False
            elif self._current_filter == "videos" and info.get("category") != "Videos":
                show = False
            elif self._current_filter == "music" and info.get("category") != "Music":
                show = False
            elif self._current_filter == "documents" and info.get("category") != "Documents":
                show = False
            elif self._current_filter == "archives" and info.get("category") != "Archives":
                show = False
            elif self._current_filter == "compressed" and info.get("category") != "Compressed":
                show = False

            if self._current_search and self._current_search not in info["filename"].lower():
                show = False

            item.setHidden(not show)
            if show:
                visible_count += 1

            if info["status"] == DownloadStatus.DOWNLOADING:
                total_speed += info.get("speed", 0)
                active_count += 1
            elif info["status"] == DownloadStatus.QUEUED:
                queued_count += 1
            elif info["status"] == DownloadStatus.COMPLETED:
                completed_count += 1

        self._download_count_label.setText(f"{visible_count} items")
        self._status_speed.setText(f"↓ {self._format_speed(total_speed)}")
        self._status_downloads.setText(f"{active_count} active / {len(self._downloads)} total")
        self._tray_downloading.setText(f"Downloading: {active_count}")

        self._stats_widget.update_stats(
            speed=self._format_speed(total_speed),
            active=active_count,
            queued=queued_count,
            completed=completed_count,
            total=len(self._downloads),
        )

        self._speed_graph.add_speed(total_speed / (1024 * 1024))

    def _update_ui(self) -> None:
        self._update_counts()

    @staticmethod
    def _format_speed(speed: float) -> str:
        if speed >= 1024 * 1024:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        elif speed >= 1024:
            return f"{speed / 1024:.1f} KB/s"
        return f"{speed:.0f} B/s"
