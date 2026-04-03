from typing import Dict, Tuple
from PyQt5.QtGui import QColor, QPalette, QLinearGradient, QGradient


class Colors:
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#16213e"
    BG_LIGHT = "#0f3460"
    BG_CARD = "#1e2a4a"
    BG_HOVER = "#253565"
    BG_SELECTED = "#2a3f6e"

    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    ACCENT_BLUE = "#00d4ff"
    ACCENT_GREEN = "#00ff88"
    ACCENT_ORANGE = "#ff6b35"
    ACCENT_PURPLE = "#a855f7"
    ACCENT_RED = "#ef4444"
    ACCENT_YELLOW = "#fbbf24"

    BORDER = "#2d3f5a"
    BORDER_HOVER = "#3d5578"
    SHADOW = "rgba(0, 0, 0, 0.5)"

    GRADIENT_BLUE_START = "#00d4ff"
    GRADIENT_BLUE_END = "#0099cc"
    GRADIENT_GREEN_START = "#00ff88"
    GRADIENT_GREEN_END = "#00cc6a"
    GRADIENT_PURPLE_START = "#a855f7"
    GRADIENT_PURPLE_END = "#7c3aed"
    GRADIENT_ORANGE_START = "#ff6b35"
    GRADIENT_ORANGE_END = "#e55a2b"


class Theme:
    @staticmethod
    def get_palette() -> QPalette:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(Colors.BG_DARK))
        palette.setColor(QPalette.WindowText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(Colors.BG_MEDIUM))
        palette.setColor(QPalette.AlternateBase, QColor(Colors.BG_LIGHT))
        palette.setColor(QPalette.ToolTipBase, QColor(Colors.BG_CARD))
        palette.setColor(QPalette.ToolTipText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.Text, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.Button, QColor(Colors.BG_MEDIUM))
        palette.setColor(QPalette.ButtonText, QColor(Colors.TEXT_PRIMARY))
        palette.setColor(QPalette.BrightText, QColor(Colors.ACCENT_BLUE))
        palette.setColor(QPalette.Link, QColor(Colors.ACCENT_BLUE))
        palette.setColor(QPalette.Highlight, QColor(Colors.ACCENT_BLUE))
        palette.setColor(QPalette.HighlightedText, QColor(Colors.BG_DARK))
        return palette

    @staticmethod
    def get_stylesheet() -> str:
        return f"""
        QMainWindow {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_PRIMARY};
        }}

        QWidget {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_PRIMARY};
            font-family: 'Segoe UI', 'Roboto', 'Ubuntu', sans-serif;
            font-size: 13px;
        }}

        QMenuBar {{
            background-color: {Colors.BG_MEDIUM};
            border-bottom: 1px solid {Colors.BORDER};
            padding: 2px;
            spacing: 2px;
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
            margin: 2px;
        }}

        QMenuBar::item:selected {{
            background-color: {Colors.BG_HOVER};
        }}

        QMenuBar::item:pressed {{
            background-color: {Colors.ACCENT_BLUE};
            color: {Colors.BG_DARK};
        }}

        QMenu {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 6px;
            margin: 2px;
        }}

        QMenu::item {{
            padding: 8px 32px 8px 12px;
            border-radius: 6px;
            margin: 2px;
        }}

        QMenu::item:selected {{
            background-color: {Colors.BG_HOVER};
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {Colors.BORDER};
            margin: 6px 8px;
        }}

        QMenu::icon {{
            left: 8px;
        }}

        QToolBar {{
            background-color: {Colors.BG_MEDIUM};
            border-bottom: 1px solid {Colors.BORDER};
            padding: 6px;
            spacing: 6px;
        }}

        QToolButton {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 8px 16px;
            margin: 2px;
            font-weight: 500;
            min-width: 80px;
        }}

        QToolButton:hover {{
            background-color: {Colors.BG_HOVER};
            border-color: {Colors.BORDER_HOVER};
        }}

        QToolButton:pressed {{
            background-color: {Colors.ACCENT_BLUE};
            color: {Colors.BG_DARK};
            border-color: {Colors.ACCENT_BLUE};
        }}

        QToolButton:checked {{
            background-color: {Colors.ACCENT_BLUE};
            color: {Colors.BG_DARK};
            border-color: {Colors.ACCENT_BLUE};
        }}

        QPushButton {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 8px 20px;
            font-weight: 500;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {Colors.BG_HOVER};
            border-color: {Colors.BORDER_HOVER};
        }}

        QPushButton:pressed {{
            background-color: {Colors.ACCENT_BLUE};
            color: {Colors.BG_DARK};
            border-color: {Colors.ACCENT_BLUE};
        }}

        QPushButton:disabled {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_MUTED};
            border-color: {Colors.BORDER};
        }}

        QPushButton#primaryButton {{
            background-color: {Colors.ACCENT_BLUE};
            color: {Colors.BG_DARK};
            border: none;
            font-weight: 600;
        }}

        QPushButton#primaryButton:hover {{
            background-color: #33ddff;
        }}

        QPushButton#dangerButton {{
            background-color: transparent;
            color: {Colors.ACCENT_RED};
            border: 1px solid {Colors.ACCENT_RED};
        }}

        QPushButton#dangerButton:hover {{
            background-color: {Colors.ACCENT_RED};
            color: white;
        }}

        QPushButton#successButton {{
            background-color: {Colors.ACCENT_GREEN};
            color: {Colors.BG_DARK};
            border: none;
            font-weight: 600;
        }}

        QPushButton#successButton:hover {{
            background-color: #33ffaa;
        }}

        QLineEdit {{
            background-color: {Colors.BG_CARD};
            border: 2px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            selection-background-color: {Colors.ACCENT_BLUE};
            selection-color: {Colors.BG_DARK};
        }}

        QLineEdit:focus {{
            border-color: {Colors.ACCENT_BLUE};
        }}

        QLineEdit::placeholder {{
            color: {Colors.TEXT_MUTED};
        }}

        QLabel {{
            background-color: transparent;
            border: none;
            padding: 0;
        }}

        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        QScrollBar:vertical {{
            background-color: {Colors.BG_DARK};
            width: 10px;
            margin: 0;
            border-radius: 5px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {Colors.BORDER};
            min-height: 30px;
            border-radius: 5px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {Colors.BORDER_HOVER};
        }}

        QScrollBar::handle:vertical:pressed {{
            background-color: {Colors.ACCENT_BLUE};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}

        QScrollBar:horizontal {{
            background-color: {Colors.BG_DARK};
            height: 10px;
            margin: 0;
            border-radius: 5px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {Colors.BORDER};
            min-width: 30px;
            border-radius: 5px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {Colors.BORDER_HOVER};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}

        QFrame#card {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 12px;
            padding: 12px;
        }}

        QFrame#card:hover {{
            border-color: {Colors.BORDER_HOVER};
            background-color: {Colors.BG_HOVER};
        }}

        QFrame#separator {{
            background-color: {Colors.BORDER};
            max-height: 1px;
            min-height: 1px;
        }}

        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
        }}

        QListWidget::item {{
            background-color: transparent;
            border: none;
            padding: 0;
            margin: 4px 0;
        }}

        QListWidget::item:selected {{
            background-color: transparent;
        }}

        QTreeWidget {{
            background-color: transparent;
            border: none;
            outline: none;
        }}

        QTreeWidget::item {{
            padding: 6px 8px;
            border-radius: 6px;
            margin: 1px 4px;
        }}

        QTreeWidget::item:selected {{
            background-color: {Colors.BG_HOVER};
        }}

        QTreeWidget::item:hover {{
            background-color: {Colors.BG_CARD};
        }}

        QHeaderView::section {{
            background-color: {Colors.BG_MEDIUM};
            color: {Colors.TEXT_SECONDARY};
            border: none;
            border-bottom: 1px solid {Colors.BORDER};
            padding: 8px 12px;
            font-weight: 500;
        }}

        QTabWidget::pane {{
            background-color: {Colors.BG_DARK};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
        }}

        QTabBar::tab {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}

        QTabBar::tab:selected {{
            background-color: {Colors.BG_DARK};
            border-bottom-color: {Colors.BG_DARK};
        }}

        QTabBar::tab:hover {{
            background-color: {Colors.BG_HOVER};
        }}

        QGroupBox {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 20px;
            font-weight: 600;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 12px;
            background-color: {Colors.BG_CARD};
            border-radius: 4px;
            left: 12px;
        }}

        QComboBox {{
            background-color: {Colors.BG_CARD};
            border: 2px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
            min-width: 120px;
        }}

        QComboBox:hover {{
            border-color: {Colors.BORDER_HOVER};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox::down-arrow {{
            width: 10px;
            height: 10px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            selection-background-color: {Colors.BG_HOVER};
            padding: 4px;
        }}

        QSpinBox {{
            background-color: {Colors.BG_CARD};
            border: 2px solid {Colors.BORDER};
            border-radius: 8px;
            padding: 8px 12px;
        }}

        QSpinBox:focus {{
            border-color: {Colors.ACCENT_BLUE};
        }}

        QCheckBox {{
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {Colors.BORDER};
            background-color: {Colors.BG_CARD};
        }}

        QCheckBox::indicator:checked {{
            background-color: {Colors.ACCENT_BLUE};
            border-color: {Colors.ACCENT_BLUE};
        }}

        QCheckBox::indicator:hover {{
            border-color: {Colors.BORDER_HOVER};
        }}

        QSlider::groove:horizontal {{
            height: 6px;
            background-color: {Colors.BORDER};
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            width: 16px;
            height: 16px;
            margin: -5px 0;
            background-color: {Colors.ACCENT_BLUE};
            border-radius: 8px;
        }}

        QSlider::handle:horizontal:hover {{
            background-color: #33ddff;
        }}

        QSlider::sub-page:horizontal {{
            background-color: {Colors.ACCENT_BLUE};
            border-radius: 3px;
        }}

        QStatusBar {{
            background-color: {Colors.BG_MEDIUM};
            border-top: 1px solid {Colors.BORDER};
            padding: 4px;
            font-size: 12px;
        }}

        QStatusBar::item {{
            border: none;
        }}

        QToolTip {{
            background-color: {Colors.BG_CARD};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}

        QSplitter::handle {{
            background-color: {Colors.BORDER};
            width: 1px;
        }}

        QSplitter::handle:hover {{
            background-color: {Colors.ACCENT_BLUE};
        }}

        QProgressBar {{
            background-color: {Colors.BG_DARK};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {Colors.TEXT_PRIMARY};
            font-weight: 600;
            font-size: 11px;
            min-height: 20px;
        }}

        QProgressBar::chunk {{
            border-radius: 4px;
        }}

        QFrame#sidebar {{
            background-color: {Colors.BG_MEDIUM};
            border-right: 1px solid {Colors.BORDER};
        }}

        QFrame#statsPanel {{
            background-color: {Colors.BG_CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 12px;
            padding: 16px;
        }}
        """

    @staticmethod
    def get_status_color(status: str) -> str:
        color_map: Dict[str, str] = {
            "downloading": Colors.ACCENT_BLUE,
            "completed": Colors.ACCENT_GREEN,
            "paused": Colors.ACCENT_ORANGE,
            "error": Colors.ACCENT_RED,
            "queued": Colors.ACCENT_PURPLE,
            "stopped": Colors.TEXT_MUTED,
        }
        return color_map.get(status.lower(), Colors.TEXT_MUTED)

    @staticmethod
    def get_gradient_css(start_color: str, end_color: str, direction: str = "horizontal") -> str:
        if direction == "horizontal":
            return f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {start_color}, stop:1 {end_color})"
        return f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {start_color}, stop:1 {end_color})"

    @staticmethod
    def get_card_shadow_css() -> str:
        return f"""
        QFrame#card {{
            border: 1px solid {Colors.BORDER};
            border-radius: 12px;
        }}
        """
