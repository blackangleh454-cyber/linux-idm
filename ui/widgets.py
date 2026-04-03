import os
import time
from typing import Optional, List, Dict, Any
from enum import Enum
from collections import deque

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QLineEdit, QFormLayout, QSpinBox,
    QFileDialog, QComboBox, QDialogButtonBox, QProgressBar,
    QSizePolicy, QMenu, QAction, QGraphicsDropShadowEffect,
    QApplication, QStyle, QToolButton
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect,
    QRectF, pyqtSignal, pyqtProperty, QSize, QPoint
)
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush,
    QPainterPath, QFont, QFontMetrics, QIcon, QCursor
)

from .theme import Colors, Theme


class DownloadStatus(Enum):
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    QUEUED = "queued"
    STOPPED = "stopped"


class AnimatedProgressBar(QWidget):
    value_changed = pyqtSignal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._value: float = 0.0
        self._max_value: float = 100.0
        self._animation_offset: float = 0.0
        self._glow_intensity: float = 0.5
        self._gradient_start = QColor(Colors.ACCENT_BLUE)
        self._gradient_end = QColor(Colors.GRADIENT_BLUE_END)
        self._background_color = QColor(Colors.BG_DARK)
        self._text_color = QColor(Colors.TEXT_PRIMARY)
        self._border_radius: int = 6
        self._show_text: bool = True
        self._animated: bool = True
        self._pulse_phase: float = 0.0

        self.setMinimumHeight(24)
        self.setMaximumHeight(24)
        self.setMinimumWidth(100)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(30)

    def set_gradient(self, start: str, end: str) -> None:
        self._gradient_start = QColor(start)
        self._gradient_end = QColor(end)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(value, self._max_value))
        self.value_changed.emit(self._value)
        self.update()

    def get_value(self) -> float:
        return self._value

    def set_max_value(self, max_val: float) -> None:
        self._max_value = max_val
        self.update()

    def set_animated(self, animated: bool) -> None:
        self._animated = animated
        if animated:
            self._timer.start(30)
        else:
            self._timer.stop()

    def _update_animation(self) -> None:
        self._animation_offset = (self._animation_offset + 2) % 200
        self._pulse_phase = (self._pulse_phase + 0.05) % (2 * 3.14159)
        self._glow_intensity = 0.3 + 0.2 * abs(
            __import__("math").sin(self._pulse_phase)
        )
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        progress_ratio = self._value / self._max_value if self._max_value > 0 else 0
        progress_width = rect.width() * progress_ratio

        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), self._border_radius, self._border_radius)
        painter.fillPath(bg_path, self._background_color)

        if progress_width > 0:
            glow_rect = QRectF(
                0, 0, progress_width, rect.height()
            )
            glow_path = QPainterPath()
            glow_path.addRoundedRect(glow_rect, self._border_radius, self._border_radius)

            for i in range(3, 0, -1):
                glow_color = QColor(self._gradient_start)
                glow_color.setAlphaF(self._glow_intensity * 0.15 * i)
                painter.setPen(QPen(glow_color, i * 2))
                painter.drawPath(glow_path)

            fill_path = QPainterPath()
            fill_rect = QRectF(0, 0, progress_width, rect.height())
            fill_path.addRoundedRect(fill_rect, self._border_radius, self._border_radius)

            gradient = QLinearGradient(0, 0, progress_width, 0)
            offset = self._animation_offset / 200.0

            c1 = QColor(self._gradient_start)
            c2 = QColor(self._gradient_end)
            c_mid = QColor(
                (c1.red() + c2.red()) // 2,
                (c1.green() + c2.green()) // 2,
                (c1.blue() + c2.blue()) // 2,
            )

            gradient.setColorAt(0, c1)
            gradient.setColorAt(min(0.5 + offset * 0.3, 1.0), c_mid)
            gradient.setColorAt(1, c2)

            painter.fillPath(fill_path, gradient)

            shine_path = QPainterPath()
            shine_rect = QRectF(0, 0, progress_width, rect.height() / 2)
            shine_path.addRoundedRect(shine_rect, self._border_radius, self._border_radius)
            shine_color = QColor(255, 255, 255, 25)
            painter.fillPath(shine_path, shine_color)

        if self._show_text:
            text = f"{self._value:.1f}%"
            painter.setPen(self._text_color)
            font = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, text)

        painter.end()

    value = pyqtProperty(float, get_value, set_value)


class SpeedGraphWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None, max_points: int = 60):
        super().__init__(parent)
        self._max_points = max_points
        self._speed_history: deque = deque(maxlen=max_points)
        self._max_speed: float = 1.0
        self._line_color = QColor(Colors.ACCENT_BLUE)
        self._fill_color = QColor(Colors.ACCENT_BLUE)
        self._glow_color = QColor(Colors.ACCENT_BLUE)
        self._grid_color = QColor(Colors.BORDER)
        self._bg_color = QColor(Colors.BG_CARD)
        self._text_color = QColor(Colors.TEXT_MUTED)
        self._border_radius = 8
        self._hue_offset = 0.0
        self._pulse_phase = 0.0

        for _ in range(max_points):
            self._speed_history.append(0.0)

        self.setMinimumHeight(120)
        self.setMaximumHeight(160)
        self.setMinimumWidth(200)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(50)

    def _animate(self) -> None:
        self._hue_offset = (self._hue_offset + 1.5) % 360
        self._pulse_phase = (self._pulse_phase + 0.08) % (2 * 3.14159)
        self.update()

    def add_speed(self, speed: float) -> None:
        self._speed_history.append(speed)
        self._max_speed = max(max(self._speed_history) * 1.2, 1.0)

    def clear(self) -> None:
        self._speed_history.clear()
        for _ in range(self._max_points):
            self._speed_history.append(0.0)
        self.update()

    def _get_dynamic_color(self, alpha: int = 255) -> QColor:
        c = QColor()
        c.setHslF(
            (0.52 + 0.15 * __import__("math").sin(self._hue_offset * 3.14159 / 180)) % 1.0,
            1.0, 0.6, alpha / 255.0
        )
        return c

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        bg_path = QPainterPath()
        bg_path.addRoundedRect(QRectF(rect), self._border_radius, self._border_radius)
        painter.fillPath(bg_path, self._bg_color)

        grid_pen = QPen(QColor(Colors.BORDER), 0.3, Qt.DotLine)
        painter.setPen(grid_pen)
        for i in range(1, 5):
            y = h * i / 5
            painter.drawLine(0, int(y), w, int(y))

        if len(self._speed_history) < 2:
            painter.end()
            return

        pulse = 0.7 + 0.3 * __import__("math").sin(self._pulse_phase)
        dyn_color = self._get_dynamic_color()

        points: List[QPoint] = []
        step = w / (self._max_points - 1)
        for i, speed in enumerate(self._speed_history):
            x = int(i * step)
            y = int(h - (speed / self._max_speed) * (h - 24) - 12)
            points.append(QPoint(x, y))

        fill_path = QPainterPath()
        fill_path.moveTo(points[0].x(), h)
        for p in points:
            fill_path.lineTo(p)
        fill_path.lineTo(points[-1].x(), h)
        fill_path.closeSubpath()

        fill_gradient = QLinearGradient(0, 0, 0, h)
        fc = QColor(dyn_color)
        fc.setAlphaF(0.35 * pulse)
        fill_gradient.setColorAt(0, fc)
        fc2 = QColor(dyn_color)
        fc2.setAlphaF(0.0)
        fill_gradient.setColorAt(1, fc2)
        painter.fillPath(fill_path, fill_gradient)

        for blur in range(4, 0, -1):
            glow_pen = QPen(dyn_color, blur * 3, Qt.SolidLine)
            glow_color = QColor(dyn_color)
            glow_color.setAlphaF(0.08 * pulse)
            glow_pen.setColor(glow_color)
            painter.setPen(glow_pen)
            glow_path = QPainterPath()
            glow_path.moveTo(points[0])
            for p in points[1:]:
                glow_path.lineTo(p)
            painter.drawPath(glow_path)

        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for p in points[1:]:
            line_path.lineTo(p)

        line_pen = QPen(dyn_color, 2.5, Qt.SolidLine)
        line_pen.setCapStyle(Qt.RoundCap)
        line_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(line_pen)
        painter.drawPath(line_path)

        if points:
            last = points[-1]
            glow_r = 10 * pulse
            glow = QColor(dyn_color)
            glow.setAlphaF(0.3)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(last, int(glow_r), int(glow_r))

            painter.setBrush(QBrush(QColor(Colors.TEXT_PRIMARY)))
            painter.drawEllipse(last, 3, 3)

            painter.setBrush(QBrush(dyn_color))
            painter.drawEllipse(last, 2, 2)

        current_speed = self._speed_history[-1]
        if current_speed > 0:
            speed_size = 13
        else:
            speed_size = 10

        font = QFont("Segoe UI", speed_size, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        speed_text = f"{current_speed:.1f} MB/s"
        painter.drawText(QRect(10, 4, w - 20, 20), Qt.AlignLeft | Qt.AlignVCenter, speed_text)

        peak_font = QFont("Segoe UI", 9)
        painter.setFont(peak_font)
        peak_color = QColor(Colors.ACCENT_ORANGE)
        painter.setPen(peak_color)
        peak_text = f"PEAK {self._max_speed:.1f}"
        painter.drawText(QRect(10, 4, w - 20, 20), Qt.AlignRight | Qt.AlignVCenter, peak_text)

        painter.end()


class StatsWidget(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("statsPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        title = QLabel("Statistics")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)

        self._speed_label = self._create_stat_row("↓ Speed", "0 KB/s", Colors.ACCENT_BLUE, layout)
        self._active_label = self._create_stat_row("Active", "0", Colors.ACCENT_GREEN, layout)
        self._queued_label = self._create_stat_row("Queued", "0", Colors.ACCENT_PURPLE, layout)
        self._completed_label = self._create_stat_row("Completed", "0", Colors.ACCENT_GREEN, layout)
        self._total_label = self._create_stat_row("Total", "0", Colors.TEXT_SECONDARY, layout)

        layout.addStretch()

    def _create_stat_row(self, name: str, value: str, color: str, parent_layout: QVBoxLayout) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 8px;")
        dot.setFixedWidth(16)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")
        value_label.setAlignment(Qt.AlignRight)

        row.addWidget(dot)
        row.addWidget(name_label)
        row.addStretch()
        row.addWidget(value_label)
        parent_layout.addLayout(row)
        return value_label

    def update_stats(self, speed: str, active: int, queued: int, completed: int, total: int) -> None:
        self._speed_label.setText(speed)
        self._active_label.setText(str(active))
        self._queued_label.setText(str(queued))
        self._completed_label.setText(str(completed))
        self._total_label.setText(str(total))


class DownloadCardWidget(QFrame):
    pause_clicked = pyqtSignal(str)
    resume_clicked = pyqtSignal(str)
    cancel_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    open_clicked = pyqtSignal(str)
    open_folder_clicked = pyqtSignal(str)
    copy_url_clicked = pyqtSignal(str)

    def __init__(self, download_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._download_id = download_id
        self._filename: str = ""
        self._url: str = ""
        self._save_path: str = ""
        self._progress: float = 0.0
        self._speed: float = 0.0
        self._size: float = 0.0
        self._downloaded: float = 0.0
        self._eta: str = "--:--"
        self._status: DownloadStatus = DownloadStatus.QUEUED
        self._connections: int = 8
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setObjectName("card")
        self.setCursor(Qt.ArrowCursor)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self._status_icon = QLabel()
        self._status_icon.setFixedSize(24, 24)
        self._status_icon.setAlignment(Qt.AlignCenter)
        self._update_status_icon()
        top_row.addWidget(self._status_icon)

        self._filename_label = QLabel("filename.ext")
        self._filename_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
        """)
        self._filename_label.setTextFormat(Qt.PlainText)
        self._filename_label.setWordWrap(True)
        top_row.addWidget(self._filename_label, 1)

        self._size_label = QLabel("0 MB")
        self._size_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_SECONDARY};
        """)
        top_row.addWidget(self._size_label)

        main_layout.addLayout(top_row)

        self._progress_bar = AnimatedProgressBar(self)
        self._progress_bar.set_gradient(Colors.ACCENT_BLUE, Colors.GRADIENT_BLUE_END)
        main_layout.addWidget(self._progress_bar)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        self._speed_label = QLabel("0 KB/s")
        self._speed_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.ACCENT_BLUE};
            font-weight: 500;
        """)
        bottom_row.addWidget(self._speed_label)

        self._eta_label = QLabel("ETA: --:--")
        self._eta_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_SECONDARY};
        """)
        bottom_row.addWidget(self._eta_label)

        self._connections_label = QLabel("8 connections")
        self._connections_label.setStyleSheet(f"""
            font-size: 11px;
            color: {Colors.TEXT_MUTED};
        """)
        bottom_row.addWidget(self._connections_label)

        bottom_row.addStretch()

        self._status_label = QLabel("Queued")
        self._status_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {Colors.ACCENT_PURPLE};
            padding: 2px 8px;
            background-color: rgba(168, 85, 247, 0.15);
            border-radius: 4px;
        """)
        bottom_row.addWidget(self._status_label)

        self._pause_btn = self._create_icon_button("⏸", "Pause")
        self._pause_btn.clicked.connect(lambda: self.pause_clicked.emit(self._download_id))

        self._resume_btn = self._create_icon_button("▶", "Resume")
        self._resume_btn.clicked.connect(lambda: self.resume_clicked.emit(self._download_id))
        self._resume_btn.setVisible(False)

        self._cancel_btn = self._create_icon_button("⏹", "Cancel")
        self._cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self._download_id))

        self._delete_btn = self._create_icon_button("✕", "Delete")
        self._delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._download_id))

        bottom_row.addWidget(self._pause_btn)
        bottom_row.addWidget(self._resume_btn)
        bottom_row.addWidget(self._cancel_btn)
        bottom_row.addWidget(self._delete_btn)

        main_layout.addLayout(bottom_row)

    def _create_icon_button(self, icon: str, tooltip: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(28, 28)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                font-size: 12px;
                padding: 0;
                min-width: 28px;
                max-width: 28px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
                border-color: {Colors.BORDER_HOVER};
            }}
        """)
        return btn

    def _update_status_icon(self) -> None:
        icons = {
            DownloadStatus.DOWNLOADING: "↓",
            DownloadStatus.PAUSED: "‖",
            DownloadStatus.COMPLETED: "✓",
            DownloadStatus.ERROR: "!",
            DownloadStatus.QUEUED: "◷",
            DownloadStatus.STOPPED: "■",
        }
        icon = icons.get(self._status, "?")
        self._status_icon.setText(icon)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 24px 8px 12px;
                border-radius: 6px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.BG_HOVER};
            }}
        """)

        if self._status == DownloadStatus.COMPLETED:
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.open_clicked.emit(self._download_id))
            menu.addAction(open_action)

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.triggered.connect(lambda: self.open_folder_clicked.emit(self._download_id))
        menu.addAction(open_folder_action)

        copy_url_action = QAction("Copy URL", self)
        copy_url_action.triggered.connect(lambda: self.copy_url_clicked.emit(self._download_id))
        menu.addAction(copy_url_action)

        menu.addSeparator()

        if self._status in (DownloadStatus.DOWNLOADING, DownloadStatus.QUEUED):
            pause_action = QAction("Pause", self)
            pause_action.triggered.connect(lambda: self.pause_clicked.emit(self._download_id))
            menu.addAction(pause_action)
        elif self._status in (DownloadStatus.PAUSED, DownloadStatus.STOPPED):
            resume_action = QAction("Resume", self)
            resume_action.triggered.connect(lambda: self.resume_clicked.emit(self._download_id))
            menu.addAction(resume_action)

        menu.addSeparator()

        remove_action = QAction("Remove from List", self)
        remove_action.triggered.connect(lambda: self.cancel_clicked.emit(self._download_id))
        menu.addAction(remove_action)

        delete_action = QAction("Delete File", self)
        delete_action.triggered.connect(lambda: self.delete_clicked.emit(self._download_id))
        menu.addAction(delete_action)

        menu.exec_(event.globalPos())

    def set_filename(self, filename: str) -> None:
        self._filename = filename
        self._filename_label.setText(filename)

    def set_url(self, url: str) -> None:
        self._url = url

    def set_save_path(self, path: str) -> None:
        self._save_path = path

    def set_progress(self, progress: float) -> None:
        self._progress = progress
        self._progress_bar.set_value(progress)

    def set_speed(self, speed: float) -> None:
        self._speed = speed
        self._speed_label.setText(self._format_speed(speed))

    def set_size(self, size: float) -> None:
        self._size = size
        self._size_label.setText(self._format_size(size))

    def set_downloaded(self, downloaded: float) -> None:
        self._downloaded = downloaded

    def set_eta(self, eta: str) -> None:
        self._eta = eta
        self._eta_label.setText(f"ETA: {eta}")

    def set_status(self, status: DownloadStatus) -> None:
        self._status = status
        self._update_status_icon()
        color = Theme.get_status_color(status.value)
        label_text = status.value.capitalize()

        if status == DownloadStatus.DOWNLOADING:
            self._progress_bar.set_gradient(Colors.ACCENT_BLUE, Colors.GRADIENT_BLUE_END)
            self._progress_bar.set_animated(True)
            self._pause_btn.setVisible(True)
            self._resume_btn.setVisible(False)
            label_text = "Downloading"
        elif status == DownloadStatus.PAUSED:
            self._progress_bar.set_gradient(Colors.ACCENT_ORANGE, Colors.GRADIENT_ORANGE_END)
            self._progress_bar.set_animated(False)
            self._pause_btn.setVisible(False)
            self._resume_btn.setVisible(True)
            label_text = "Paused"
        elif status == DownloadStatus.COMPLETED:
            self._progress_bar.set_gradient(Colors.ACCENT_GREEN, Colors.GRADIENT_GREEN_END)
            self._progress_bar.set_animated(False)
            self._pause_btn.setVisible(False)
            self._resume_btn.setVisible(False)
            self._cancel_btn.setVisible(False)
            label_text = "Completed"
        elif status == DownloadStatus.ERROR:
            self._progress_bar.set_gradient(Colors.ACCENT_RED, "#b91c1c")
            self._progress_bar.set_animated(False)
            label_text = "Error"
        elif status == DownloadStatus.QUEUED:
            self._progress_bar.set_gradient(Colors.ACCENT_PURPLE, Colors.GRADIENT_PURPLE_END)
            self._progress_bar.set_animated(False)
            label_text = "Queued"

        bg_alpha = "0.15"
        self._status_label.setText(label_text)
        self._status_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {color};
            padding: 2px 8px;
            background-color: rgba({QColor(color).red()}, {QColor(color).green()}, {QColor(color).blue()}, 0.15);
            border-radius: 4px;
        """)
        self._status_icon.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")

    def set_connections(self, connections: int) -> None:
        self._connections = connections
        self._connections_label.setText(f"{connections} connections")

    def get_download_id(self) -> str:
        return self._download_id

    def get_filename(self) -> str:
        return self._filename

    def get_url(self) -> str:
        return self._url

    def get_save_path(self) -> str:
        return self._save_path

    def get_status(self) -> DownloadStatus:
        return self._status

    @staticmethod
    def _format_speed(speed: float) -> str:
        if speed >= 1024 * 1024:
            return f"{speed / (1024 * 1024):.1f} MB/s"
        elif speed >= 1024:
            return f"{speed / 1024:.1f} KB/s"
        return f"{speed:.0f} B/s"

    @staticmethod
    def _format_size(size: float) -> str:
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
        elif size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        elif size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size:.0f} B"


class AddUrlDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, default_save_path: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Add Download")
        self.setMinimumWidth(500)
        self._default_save_path = default_save_path or os.path.expanduser("~/Downloads")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Add New Download")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: 8px;
        """)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft)

        label_style = f"""
            font-size: 13px;
            font-weight: 500;
            color: {Colors.TEXT_SECONDARY};
        """

        url_label = QLabel("URL")
        url_label.setStyleSheet(label_style)
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://example.com/file.zip")
        self._url_input.setMinimumHeight(36)
        form.addRow(url_label, self._url_input)

        filename_label = QLabel("Filename")
        filename_label.setStyleSheet(label_style)
        self._filename_input = QLineEdit()
        self._filename_input.setPlaceholderText("Auto-detect from URL")
        self._filename_input.setMinimumHeight(36)
        form.addRow(filename_label, self._filename_input)

        path_label = QLabel("Save to")
        path_label.setStyleSheet(label_style)
        path_row = QHBoxLayout()
        self._path_input = QLineEdit(self._default_save_path)
        self._path_input.setMinimumHeight(36)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedHeight(36)
        browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(self._path_input, 1)
        path_row.addWidget(browse_btn)
        form.addRow(path_label, path_row)

        connections_label = QLabel("Connections")
        connections_label.setStyleSheet(label_style)
        self._connections_spin = QSpinBox()
        self._connections_spin.setRange(1, 32)
        self._connections_spin.setValue(8)
        self._connections_spin.setMinimumHeight(36)
        form.addRow(connections_label, self._connections_spin)

        category_label = QLabel("Category")
        category_label.setStyleSheet(label_style)
        self._category_combo = QComboBox()
        self._category_combo.addItems(["General", "Videos", "Music", "Documents", "Archives", "Compressed"])
        self._category_combo.setMinimumHeight(36)
        form.addRow(category_label, self._category_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet(f"""
            QDialogButtonBox {{
                spacing: 8px;
            }}
        """)

        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Add Download")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setMinimumHeight(36)

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setMinimumHeight(36)

        layout.addWidget(buttons)

    def _browse_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self._path_input.text())
        if path:
            self._path_input.setText(path)

    def get_url(self) -> str:
        return self._url_input.text().strip()

    def get_filename(self) -> str:
        return self._filename_input.text().strip()

    def get_save_path(self) -> str:
        return self._path_input.text().strip()

    def get_connections(self) -> int:
        return self._connections_spin.value()

    def get_category(self) -> str:
        return self._category_combo.currentText()
