import sys
import os
import json
import shutil
import subprocess
import traceback
import ctypes
import time
import urllib.request
import urllib.parse
import ssl
from functools import partial

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                               QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QMessageBox, 
                               QScroller, QScrollerProperties, QMenu, QDialog, 
                               QLineEdit, QFileDialog, QDialogButtonBox, 
                               QFormLayout, QPushButton, QSizePolicy, QLayout,
                               QInputDialog, QFileIconProvider, QGraphicsDropShadowEffect,
                               QStackedWidget, QTabBar) 
from PySide6.QtCore import Qt, QSize, Signal, QMimeData, QPoint, QRect, QFileInfo, QKeyCombination
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QDrag, QIcon, QLinearGradient, QBrush, QKeySequence, QFontMetrics

# --- [Configuration] ---
VERSION = "v0.4.3"

# Layout Constants
APP_WIDTH = 60
APP_HEIGHT = 80
ICON_SIZE = 48
ICON_RADIUS = 14
LAYOUT_MARGIN = 2
LAYOUT_H_SPACING = 4
LAYOUT_V_SPACING = 2

# Style Constants
COLOR_BG = "#1A1A1A"
COLOR_TAB_BG = "#252525"
COLOR_TAB_HOVER = "#333333"
COLOR_TAB_SELECTED = "#202020"
COLOR_ACCENT = "#0A84FF"
COLOR_TEXT_PRIMARY = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#777777"

# --- [Paths & Migration Logic] ---
APPDATA_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'Bifrost')
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
ICON_DIR = os.path.join(APPDATA_DIR, 'icons')
ERROR_LOG_FILE = os.path.join(APPDATA_DIR, 'error_log.txt')

if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG = {
    "settings": {
        "always_on_top": True,
        "group_order": ["홈"],
        "window_geometry": {},
        "group_shortcuts": {}
    },
    "apps": []
}

def migrate_data():
    """
    마이그레이션 로직:
    1. APPDATA_DIR이 없으면 생성.
    2. APPDATA_DIR/config.json이 없으면:
       -> EXE_DIR/config.json(구버전 데이터)이 있는지 확인 후 복사.
       -> EXE_DIR/icons 폴더도 통째로 복사.
    """
    if not os.path.exists(APPDATA_DIR):
        try:
            os.makedirs(APPDATA_DIR)
        except: pass

    if not os.path.exists(ICON_DIR):
        try:
            os.makedirs(ICON_DIR)
        except: pass

    # 글로벌 설정이 없을 때만 마이그레이션 시도 (덮어쓰기 방지)
    if not os.path.exists(CONFIG_FILE):
        local_config = os.path.join(EXE_DIR, 'config.json')
        local_icons = os.path.join(EXE_DIR, 'icons')
        
        # 1. Config Migration
        if os.path.exists(local_config):
            try:
                shutil.copy2(local_config, CONFIG_FILE)
            except Exception as e:
                log_error(f"Config migration failed: {e}")
        
        # 2. Icons Migration
        if os.path.exists(local_icons):
            try:
                for item in os.listdir(local_icons):
                    s = os.path.join(local_icons, item)
                    d = os.path.join(ICON_DIR, item)
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
            except Exception as e:
                log_error(f"Icon migration failed: {e}")

    # [Force Update Logic] 항상 기본 앱 아이콘은 최신 버전으로 덮어쓰기
    # 배포판에 포함된 최신 아이콘을 AppData로 강제 복사하여 구버전 아이콘 잔재 문제 해결
    try:
        force_update_icons = ["app_icon.png", "app_icon.ico"]
        
        # [Path Check]
        # 1. 개발 환경: EXE_DIR/icons
        # 2. 배포 환경(Frozen): EXE_DIR/_internal (또는 루트)
        # PyInstaller OneDir 모드에서는 데이터가 _internal(혹은 루트)에 있음.
        
        # 후보 경로들
        candidates = [
            os.path.join(EXE_DIR, 'icons'),          # Dev
            os.path.join(EXE_DIR, '_internal'),      # Dist (OneDir default for 6.0+)
            EXE_DIR                                  # Dist (Root fallback)
        ]
        
        source_dir = None
        for c in candidates:
            # 후보 경로에 아이콘이 하나라도 있으면 채택
            if os.path.exists(os.path.join(c, "app_icon.ico")):
                source_dir = c
                break
        
        if source_dir:
            for icon_name in force_update_icons:
                src = os.path.join(source_dir, icon_name)
                dst = os.path.join(ICON_DIR, icon_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
    except Exception as e:
        log_error(f"Force icon update failed: {e}")

# Call migration before anything else
migrate_data()

# --- [스타일 시트] ---
PREMIUM_STYLE = """
    QMainWindow { 
        background-color: #1A1A1A; 
    }
    QWidget {
        color: #E0E0E0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    QStackedWidget {
        background: transparent;
        border: none;
        padding: 0px;
        margin: 0px;
    }

    QTabBar {
        background: transparent; 
        border: none;
        padding: 0px;
        margin: 0px; 
        qproperty-drawBase: 0; 
    }
    QTabBar::tab {
        background: #252525; 
        color: #777777;
        padding: 6px 14px; 
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
        margin-right: 4px;
        font-weight: 600;
        font-size: 13px;
        border: none; 
    }
    QTabBar::tab:selected {
        background: #202020; 
        color: #FFFFFF;
        border-bottom: 2px solid #0A84FF; 
    }
    QTabBar::tab:hover {
        background: #333333;
        color: #BBBBBB;
    }
    
    QPushButton#AddGroupButton {
        background-color: #252525;
        color: #777777;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
        border: none;
        font-size: 18px; 
        font-weight: normal;
        padding-bottom: 8px;
        margin-bottom: 1px;
    }
    QPushButton#AddGroupButton:hover {
        background-color: #333333;
        color: white;
    }
    QPushButton#AddGroupButton:pressed {
        background-color: #1A1A1A;
    }

    QPushButton#PinButton { 
        background: #252525; 
        border: none; 
        border-radius: 8px; 
        color: #777; 
        font-size: 14px; 
        padding: 0px; 
    }
    QPushButton#PinButton:checked { 
        background: #0A84FF; 
        color: #FFFFFF; 
    }
    QPushButton#PinButton:hover { 
        background: #333; 
        color: #EEE; 
    }

    QToolTip {
        background-color: #333333;
        color: #E0E0E0;
        border: 1px solid #555;
        border-radius: 4px;
        font-size: 12px;
    }

    QLineEdit { 
        background-color: #333333; 
        color: white; 
        border: 1px solid #444; 
        border-radius: 6px; 
        padding: 6px; 
        selection-background-color: #0A84FF;
    }
    QLineEdit:focus {
        border: 1px solid #0A84FF;
        background-color: #3A3A3A;
    }
    QPushButton {
        background-color: #3A3A3A;
        color: white;
        border-radius: 6px;
        padding: 6px 12px;
        border: 1px solid #555;
    }
    QPushButton:hover { background-color: #4A4A4A; }
    QPushButton:pressed { background-color: #2A2A2A; }
    QPushButton#PrimaryButton {
        background-color: #0A84FF;
        border: none;
    }
    QPushButton#PrimaryButton:hover { background-color: #007AFF; }
    QPushButton#PrimaryButton:pressed { background-color: #005BB5; }
    
    /* Shortcut Input Button Style */
    QPushButton#ShortcutButton {
        background-color: #333;
        border: 1px dashed #666;
        color: #AAA;
    }
    QPushButton#ShortcutButton:checked {
        background-color: transparent;
        border: 1px solid #0A84FF;
        color: #0A84FF;
    }
    
    QScrollArea { border: none; background: transparent; }
    QScrollBar:vertical {
        border: none;
        background: #202020;
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #444;
        min-height: 30px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover { background: #555; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; background: none; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    QMenu {
        background-color: #3A3A3A;
        border: 1px solid #555;
        border-radius: 8px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
        color: #EEE;
        background-color: transparent; /* 투명 배경 명시 */
    }
    QMenu::item:selected {
        background-color: #0A84FF;
        color: white;
    }
    QMenu::separator {
        height: 1px;
        background: #444;
        margin: 4px 0;
    }
    QDialog, QMessageBox, QInputDialog {
        background-color: #252525;
    }
    QMessageBox QLabel, QInputDialog QLabel {
        color: #E0E0E0;
    }
"""

def log_error(msg):
    try:
        with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(msg + "\n")
    except: pass

def apply_dark_title_bar(window_handle):
    try:
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        hwnd = window_handle
        if hwnd:
            value = ctypes.c_int(1)
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
    except: pass

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.data = DEFAULT_CONFIG.copy()
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_config() 
        else:
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Smart Merge
                    self._merge_config(self.data, loaded_data)
            except Exception as e:
                log_error(f"Config load error: {e}")
                self.save_config()
    
    def _merge_config(self, default, loaded):
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            log_error(f"Config save error: {e}")

    def get_apps(self):
        return self.data.get('apps', [])
    
    def set_apps(self, apps):
        self.data['apps'] = apps
        self.save_config()

    def get_setting(self, key, default=None):
        return self.data.get('settings', {}).get(key, default)

    def set_setting(self, key, value):
        if 'settings' not in self.data:
            self.data['settings'] = {}
        self.data['settings'][key] = value
        self.save_config()

class IconManager:
    _cache = {}
    @staticmethod
    def get_icon(filename, app_name="?"):
        cache_key = filename if filename else f"__text_{app_name}__"
        if cache_key in IconManager._cache: return IconManager._cache[cache_key]

        file_path = os.path.join(ICON_DIR, filename) if filename else ""
        pixmap = QPixmap(64, 64)
        try:
            if file_path and os.path.exists(file_path):
                loaded = QPixmap(file_path)
                if not loaded.isNull():
                    pixmap = loaded
                    if pixmap.width() > 128: pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pixmap = pixmap.scaled(56, 56, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    final_icon = IconManager._style_icon_flat(pixmap)
                else: final_icon = IconManager._create_text_icon_flat(app_name)
            else: final_icon = IconManager._create_text_icon_flat(app_name)
        except: final_icon = IconManager._create_text_icon_flat(app_name)

        IconManager._cache[cache_key] = final_icon
        return final_icon

    @staticmethod
    def import_icon(source_path):
        """외부 아이콘을 AppData/icons 폴더로 복사하고, 새 파일명을 반환합니다."""
        if not source_path or not os.path.exists(source_path): return None
        try:
            filename = os.path.basename(source_path)
            # 이름 충돌 방지를 위해 timestamp 추가
            safe_name = f"custom_{int(time.time())}_{filename}"
            dest_path = os.path.join(ICON_DIR, safe_name)
            shutil.copy2(source_path, dest_path)
            return safe_name
        except Exception as e:
            log_error(f"Icon import error: {e}")
            return None

    @staticmethod
    def _create_text_icon_flat(text):
        size = 56
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, size, size)
        gradient.setColorAt(0, QColor("#3D3D3D")) 
        gradient.setColorAt(1, QColor("#333333"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, 14, 14) 
        painter.drawPath(path)

        first = text[0].upper() if text else "?"
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRect(0, -2, size, size), Qt.AlignCenter, first)
        painter.end()
        return pix

    @staticmethod
    def _style_icon_flat(source_pixmap):
        size = 56
        target = QPixmap(size, size)
        target.fill(Qt.transparent)
        p = QPainter(target)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, 14, 14)
        p.setClipPath(path)
        x = (size - source_pixmap.width()) // 2
        y = (size - source_pixmap.height()) // 2
        p.drawPixmap(x, y, source_pixmap)
        p.end()
        return target

    @staticmethod
    def extract_and_save_icon(file_path):
        try:
            file_info = QFileInfo(file_path)
            provider = QFileIconProvider()
            icon = provider.icon(file_info)
            if not icon.isNull():
                pix = icon.pixmap(128, 128)
                base = os.path.basename(file_path)
                safe_name = "".join(c for c in base if c.isalnum() or c in (' ', '.', '_')).strip() or "icon"
                savename = f"auto_{safe_name}.png"
                pix.save(os.path.join(ICON_DIR, savename), "PNG")
                return savename
        except: pass
        return None

    @staticmethod
    def delete_if_unused(icon_name, all_apps):
        """특정 아이콘이 다른 앱에서 사용되지 않으면 삭제합니다."""
        if not icon_name or not os.path.exists(ICON_DIR): return
        # 안전 장치: 'auto_' 또는 'custom_'으로 시작하는 파일만 삭제 (사용자가 넣은 파일 보호)
        if not (icon_name.startswith("auto_") or icon_name.startswith("custom_")): return 
        if icon_name == 'app_icon.png': return # 기본 아이콘 보호
        
        # 다른 앱에서 사용 중인지 확인
        for app in all_apps:
            if app.get('icon') == icon_name:
                return # 사용 중이므로 삭제 안 함
        
        # 사용되지 않음 -> 삭제
        try:
            full_path = os.path.join(ICON_DIR, icon_name)
            if os.path.exists(full_path):
                os.remove(full_path)
        except: pass

    @staticmethod
    def fetch_favicon(url):
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc
            if not domain: return None
            
            # Google Favicon API (sz=64 -> 64px)
            favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
            
            # Download
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(favicon_url, context=ctx, timeout=3) as response:
                data = response.read()
                
            if data:
                # Save to icons dir
                safe_name = "".join(c for c in domain if c.isalnum() or c in (' ', '.', '_')).strip()
                save_name = f"auto_{safe_name}.png"
                full_path = os.path.join(ICON_DIR, save_name)
                with open(full_path, 'wb') as f:
                    f.write(data)
                return save_name
        except Exception as e:
            log_error(f"Favicon fetch error: {e}")
        return None


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, h_spacing=LAYOUT_H_SPACING, v_spacing=LAYOUT_V_SPACING):
        super(FlowLayout, self).__init__(parent)
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)
        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item: item = self.takeAt(0)

    def addItem(self, item): self._item_list.append(item)
    def count(self): return len(self._item_list)
    def itemAt(self, index): return self._item_list[index] if 0 <= index < len(self._item_list) else None
    def takeAt(self, index): return self._item_list.pop(index) if 0 <= index < len(self._item_list) else None
    def expandingDirections(self): return Qt.Orientations(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, width): return self._do_layout(QRect(0, 0, width, 0), True)
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)
    def sizeHint(self): return self.minimumSize()
    def minimumSize(self):
        size = QSize()
        for item in self._item_list: size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        for item in self._item_list:
            next_x = x + item.sizeHint().width() + self.h_spacing
            if next_x - self.h_spacing > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + self.v_spacing
                next_x = x + item.sizeHint().width() + self.h_spacing
                line_height = 0
            if not test_only: item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y()

class AppButton(QFrame):
    edit_requested = Signal()
    delete_requested = Signal()
    copy_requested = Signal()
    reorder_requested = Signal(object)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(APP_WIDTH, APP_HEIGHT) 
        self.setAcceptDrops(True)
        self.setObjectName("AppButton")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.icon_containter = QWidget(self)
        self.icon_containter.setFixedSize(ICON_SIZE, ICON_SIZE)
        
        # Icon Label
        self.icon_label = QLabel(self.icon_containter)
        self.icon_label.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.icon_label.setScaledContents(True)

        # Hover Overlay
        self.overlay = QWidget(self.icon_containter)
        self.overlay.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.overlay.setStyleSheet(f"background-color: rgba(255, 255, 255, 30); border-radius: {ICON_RADIUS}px;")
        self.overlay.hide()
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12) 
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.icon_containter.setGraphicsEffect(shadow)
        self.icon_label.setPixmap(IconManager.get_icon(data.get('icon'), data.get('name')))

        self.name_label = QLabel(data.get('name', 'App'))
        self.name_label.setFixedWidth(APP_WIDTH)
        self.name_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.name_label.setWordWrap(True)
        
        # [Dynamic Font Sizing]
        font_size = 11
        text = self.name_label.text()
        font = QFont("Segoe UI", font_size, QFont.Medium)
        fm = QFontMetrics(font)
        
        # 너비가 넘치면 폰트 사이즈 줄이기 (최소 9px)
        if fm.horizontalAdvance(text) > APP_WIDTH:
            font_size = 10
            font.setPointSize(font_size)
            fm = QFontMetrics(font)
            if fm.horizontalAdvance(text) > APP_WIDTH:
                font_size = 9
                font.setPointSize(font_size)
        
        # 2줄 제한 설정 (높이로 제어)
        # 줄간격 고려하여 대략적인 높이 설정 (1줄당 약 1.2~1.4em)
        # 9px -> ~24px, 11px -> ~28px
        max_height = 28 if font_size < 11 else 32
        self.name_label.setMaximumHeight(max_height)
        
        self.name_label.setStyleSheet(f"color: #CCCCCC; font-size: {font_size}px; font-weight: 500; background: transparent; line-height: 1.2;")
        
        layout.addWidget(self.icon_containter, 0, Qt.AlignHCenter)
        layout.addWidget(self.name_label, 0, Qt.AlignHCenter)
        layout.addStretch() # 아래로 밀어내기 (상단 정렬 유지)
        
        shortcut_txt = data.get('shortcut', '')
        if shortcut_txt:
            self.setToolTip(f"{data.get('name')}\n단축키: {shortcut_txt}")
        else:
            self.setToolTip(f"{data.get('name')}")

    def enterEvent(self, event):
        self.icon_containter.move(self.icon_containter.x(), 4)
        self.overlay.show()
        # 호버 시에도 폰트 사이즈/스타일 유지 (색상과 굵기만 변경)
        current_style = self.name_label.styleSheet()
        new_style = current_style.replace("#CCCCCC", "#FFFFFF").replace("font-weight: 500", "font-weight: 600")
        self.name_label.setStyleSheet(new_style)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.icon_containter.move(self.icon_containter.x(), 6)
        self.overlay.hide()
        current_style = self.name_label.styleSheet()
        new_style = current_style.replace("#FFFFFF", "#CCCCCC").replace("font-weight: 600", "font-weight: 500")
        self.name_label.setStyleSheet(new_style)
        super().leaveEvent(event)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            try: self.drag_start_position = e.position().toPoint()
            except: self.drag_start_position = e.globalPos() 
            self.icon_label.setGraphicsEffect(None)
            self.icon_containter.move(self.icon_containter.x(), 8)
        super().mousePressEvent(e)
    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.LeftButton): return
        try: curr_pos = e.position().toPoint()
        except: curr_pos = e.globalPos()
        if (curr_pos - self.drag_start_position).manhattanLength() < QApplication.startDragDistance(): return
        
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.data['name'])
        drag.setMimeData(mime)
        pixmap = self.icon_label.pixmap()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width()/2, pixmap.height()/2))
        drag.exec(Qt.MoveAction)
        self.icon_containter.move(self.icon_containter.x(), 6)
    def mouseReleaseEvent(self, e):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.icon_containter.setGraphicsEffect(shadow)
        self.icon_containter.move(self.icon_containter.x(), 6)
        if e.button() == Qt.LeftButton:
            try: curr_pos = e.position().toPoint()
            except: curr_pos = e.globalPos()
            if (curr_pos - self.drag_start_position).manhattanLength() < QApplication.startDragDistance(): self.execute_action()
        super().mouseReleaseEvent(e)
    def dragEnterEvent(self, e):
        if e.source() != self: e.acceptProposedAction()
    def dropEvent(self, e):
        if isinstance(e.source(), AppButton):
            self.reorder_requested.emit(e.source())
            e.acceptProposedAction()
    def contextMenuEvent(self, e):
        menu = QMenu(self.window())
        menu.addAction("수정", self.edit_requested.emit)
        menu.addAction("복사", self.copy_requested.emit)
        menu.addSeparator()
        menu.addAction("삭제", self.delete_requested.emit)
        menu.exec(e.globalPos())
    def execute_action(self):
        action_cmd = self.data.get('action', '')
        if not action_cmd: return
        try: os.startfile(action_cmd)
        except:
            try: subprocess.Popen(action_cmd, shell=True)
            except: pass

class AddButton(QFrame):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(APP_WIDTH, APP_HEIGHT) 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.box = QLabel("+")
        self.box.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.box.setAlignment(Qt.AlignCenter)
        self.box.setStyleSheet(f"QLabel {{ border: 2px dashed #555; border-radius: {ICON_RADIUS}px; color: #555; font-size: 24px; background: transparent; padding-bottom: 4px; }}")
        self.lbl = QLabel("추가")
        self.lbl.setAlignment(Qt.AlignHCenter)
        self.lbl.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.box)
        layout.addWidget(self.lbl)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.box.setStyleSheet(self.box.styleSheet().replace("border-color: #555", "border-color: #777"))
            self.clicked.emit()
    def mouseReleaseEvent(self, e):
        self.box.setStyleSheet(self.box.styleSheet().replace("border-color: #777", "border-color: #555"))
    def enterEvent(self, e):
        self.box.setStyleSheet(self.box.styleSheet().replace("#555", "#777").replace("#555", "#777"))
        self.lbl.setStyleSheet("color: #888; font-size: 11px;")
    def leaveEvent(self, e):
        self.box.setStyleSheet(self.box.styleSheet().replace("#777", "#555").replace("#777", "#555"))
        self.lbl.setStyleSheet("color: #666; font-size: 11px;")

class CustomTabBar(QTabBar):
    app_now_moved = Signal(object, int) # source_btn, target_tab_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setExpanding(False)
        self.setUsesScrollButtons(False)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setAcceptDrops(True)

    def minimumSizeHint(self): return QSize(0, 0)
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        current = self.currentIndex()
        count = self.count()
        if count == 0: return
        if delta > 0: 
            if current > 0: self.setCurrentIndex(current - 1)
        else: 
            if current < count - 1: self.setCurrentIndex(current + 1)
        event.accept()

    def dragEnterEvent(self, event):
        if isinstance(event.source(), AppButton):
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if isinstance(event.source(), AppButton):
            tab_index = self.tabAt(event.position().toPoint())
            if tab_index != -1:
                self.app_now_moved.emit(event.source(), tab_index)
                event.accept()
        else:
            super().dropEvent(event)


class ShortcutInputButton(QPushButton):
    def __init__(self, text="없음", parent=None):
        super().__init__(text, parent)
        self.setObjectName("ShortcutButton")
        self.setCheckable(True)
        self.current_key = None
        self.toggled.connect(self.update_text)

    def update_text(self, checked):
        if checked:
            self.setText("키 입력 중...")
            self.setStyleSheet("border: 1px solid #0A84FF; color: #0A84FF;")
        else:
            self.setText(self.current_key if self.current_key else "없음")
            self.setStyleSheet("") # 스타일 초기화

    def keyPressEvent(self, event):
        if not self.isChecked():
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        # 무시할 키 (Modifiers 키 자체만 눌렸을 때)
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        # 차단할 키 조합 (Win키, Alt+F4 등)
        if modifiers & Qt.MetaModifier:
            self.setText("사용 불가")
            self.setChecked(False)
            return
        if key == Qt.Key_F4 and (modifiers & Qt.AltModifier):
            self.setText("사용 불가")
            self.setChecked(False)
            return

        # 키 조합 문자열 생성
        combo = QKeyCombination(modifiers, Qt.Key(key))
        sequence = QKeySequence(combo).toString(QKeySequence.NativeText)
        self.current_key = sequence
        self.setText(sequence)
        self.setChecked(False) # 입력 완료 후 해제

    def focusOutEvent(self, event):
        if self.isChecked():
            self.setChecked(False)
            if not self.current_key: self.setText("없음")
        super().focusOutEvent(event)

class AppEditDialog(QDialog):
    def __init__(self, parent=None, app_data=None, current_group="", occupied_shortcuts=None):
        super().__init__(parent)
        self.setWindowTitle("앱 설정")
        self.setFixedWidth(400)
        self.occupied_shortcuts = occupied_shortcuts or {}
        self.app_data = app_data
        
        layout = QFormLayout(self)
        layout.setVerticalSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: Chrome")
        if app_data: self.name_input.setText(app_data.get('name', ''))
        layout.addRow("이름", self.name_input)

        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("예: 업무")
        initial_group = app_data.get('group', '') if app_data else current_group
        if not initial_group: initial_group = "홈"
        self.group_input.setText(initial_group)
        layout.addRow("그룹", self.group_input)

        path_layout = QHBoxLayout()
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText("파일 경로 또는 URL")
        if app_data: self.action_input.setText(app_data.get('action', ''))
        self.action_input.editingFinished.connect(self.try_auto_fetch_favicon) # URL 입력 시 파비콘 자동 가져오기
        btn_file = QPushButton("파일")
        btn_file.clicked.connect(self.find_file)
        btn_folder = QPushButton("폴더")
        btn_folder.clicked.connect(self.find_folder)
        path_layout.addWidget(self.action_input)
        path_layout.addWidget(btn_file)
        path_layout.addWidget(btn_folder)
        layout.addRow("경로", path_layout)

        icon_layout = QHBoxLayout()
        self.icon_display = QLineEdit()
        self.icon_display.setPlaceholderText("아이콘 경로")
        self.icon_display.setReadOnly(True)
        if app_data: self.icon_display.setText(app_data.get('icon', ''))
        btn_icon = QPushButton("찾기")
        btn_icon.clicked.connect(self.find_icon)
        btn_reset = QPushButton("삭제")
        btn_reset.setFixedWidth(50)
        btn_reset.clicked.connect(self.reset_icon)
        icon_layout.addWidget(self.icon_display)
        icon_layout.addWidget(btn_icon)
        icon_layout.addWidget(btn_reset)
        layout.addRow("아이콘", icon_layout)

        # 단축키 설정
        shortcut_layout = QHBoxLayout()
        self.shortcut_btn = ShortcutInputButton()
        self.shortcut_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        current_shortcut = app_data.get('shortcut', '') if app_data else ''
        if current_shortcut:
            self.shortcut_btn.setText(current_shortcut)
            self.shortcut_btn.current_key = current_shortcut
            
        btn_del_shortcut = QPushButton("삭제")
        btn_del_shortcut.setFixedWidth(50)
        btn_del_shortcut.clicked.connect(self.clear_shortcut)
        
        shortcut_layout.addWidget(self.shortcut_btn)
        shortcut_layout.addWidget(btn_del_shortcut)
        
        layout.addRow("단축키", shortcut_layout)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setObjectName("PrimaryButton")
        btn_box.accepted.connect(self.validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def clear_shortcut(self):
        self.shortcut_btn.current_key = ""
        self.shortcut_btn.setText("없음")
        self.shortcut_btn.setChecked(False)

    def validate_and_accept(self):
        new_shortcut = self.shortcut_btn.current_key
        # 단축키 충돌 검사
        if new_shortcut:
             # 내 자신(수정 중인 앱)의 기존 키는 제외하고 검사
            my_id = id(self.app_data) if self.app_data else None
            
            # 다른 앱이 사용 중인지 확인
            for shortcut, owner_name in self.occupied_shortcuts.items():
                if shortcut == new_shortcut:
                    # 충돌! owner가 나 자신이 아니면 경고
                    # (여기서 owner 식별을 위해 owner_name만 썼지만, 실제로는 좀 더 정교해야 함.
                    #  다만 occupied_shortcuts를 만들 때 나 자신을 제외하고 넘겨주면 됨.)
                    reply = QMessageBox.question(
                        self, "단축키 중복", 
                        f"단축키 '{new_shortcut}'은(는) 이미 '{owner_name}'에서 사용 중입니다.\n해당 앱의 단축키를 해제하고 현재 앱에 적용하시겠습니까?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                    # Yes 선택 시: 호출자(MainWindow)에서 처리하도록 플래그 설정 가능하지만,
                    # 여기서는 그냥 진행하고 MainWindow에서 최종 저장 시에 덮어쓰기 로직 수행
                    break
        self.accept()

    def find_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "파일 선택", "", "All Files (*)")
        if f:
            self.action_input.setText(f)
            extracted = IconManager.extract_and_save_icon(f)
            if extracted: self.icon_display.setText(extracted)
            if not self.name_input.text(): self.name_input.setText(os.path.splitext(os.path.basename(f))[0])
            
    def try_auto_fetch_favicon(self):
        """사용자가 URL을 직접 입력했을 때 파비콘을 가져옵니다."""
        url = self.action_input.text()
        if (url.startswith("http://") or url.startswith("https://")) and not self.icon_display.text():
            icon_name = IconManager.fetch_favicon(url)
            if icon_name:
                self.icon_display.setText(icon_name)
                # 이름이 비어있으면 도메인으로 채움
                if not self.name_input.text():
                    domain = urllib.parse.urlparse(url).netloc
                    self.name_input.setText(domain)
    def find_folder(self):
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path: self.action_input.setText(path)
    def find_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "아이콘 선택", "", "Images (*.png *.jpg *.jpeg *.ico *.bmp)")
        if path:
            # 외부 아이콘을 AppData/icons로 임포트
            imported_name = IconManager.import_icon(path)
            if imported_name:
                self.icon_display.setText(imported_name)
            else:
                # 실패 시 그냥 경로라도 넣음 (거의 발생 안 함)
                self.icon_display.setText(path)
    def reset_icon(self): self.icon_display.clear()
    def clear_shortcut(self):
        self.shortcut_btn.current_key = ""
        self.shortcut_btn.setText("없음")
        self.shortcut_btn.setChecked(False)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "group": self.group_input.text().strip() or "홈",
            "type": "auto",
            "action": self.action_input.text(),
            "icon": self.icon_display.text(),
            "shortcut": self.shortcut_btn.current_key if self.shortcut_btn.current_key else ""
        }

class ShortcutDialog(QDialog):
    def __init__(self, group_name, current_shortcut="", occupied_shortcuts=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("그룹 단축키 설정")
        self.occupied_shortcuts = occupied_shortcuts or {}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"'{group_name}' 탭으로 이동할 단축키:"))
        
        self.btn = ShortcutInputButton(current_shortcut or "없음")
        self.btn.current_key = current_shortcut
        
        shortcut_layout = QHBoxLayout()
        shortcut_layout.addWidget(self.btn)
        
        btn_del = QPushButton("삭제")
        btn_del.setFixedWidth(50)
        btn_del.clicked.connect(self.clear_shortcut)
        shortcut_layout.addWidget(btn_del)
        
        layout.addLayout(shortcut_layout)
        
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.validate)
        box.rejected.connect(self.reject)
        layout.addWidget(box)
    
    def clear_shortcut(self):
        self.btn.current_key = ""
        self.btn.setText("없음")
        self.btn.setChecked(False)
    
    def validate(self):
        new_key = self.btn.current_key
        if new_key:
            for s, owner in self.occupied_shortcuts.items():
                if s == new_key:
                    reply = QMessageBox.question(self, "중복", f"'{new_key}'는 '{owner}'가 사용 중입니다. 가져오시겠습니까?", QMessageBox.Yes|QMessageBox.No)
                    if reply == QMessageBox.No: return
        self.accept()
    def get_shortcut(self): return self.btn.current_key

class BifrostWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.setWindowTitle(f"Bifrost {VERSION} HoneyMo") 
        self.resize(400, 650)
        QApplication.instance().setStyleSheet(PREMIUM_STYLE)
        
        # 메인 윈도우 컨텍스트 메뉴 설정
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_main_context_menu)
        
        # 메인 윈도우 드롭 활성화 (외부 파일/링크 수신용)
        self.setAcceptDrops(True)
        
        # 기본 아이콘 로드 (ico 우선)
        icon_path_ico = os.path.join(ICON_DIR, "app_icon.ico")
        icon_path_png = os.path.join(ICON_DIR, "app_icon.png")
        
        if os.path.exists(icon_path_ico):
            app_icon = QIcon(icon_path_ico)
        elif os.path.exists(icon_path_png):
            app_icon = QIcon(icon_path_png)
        else:
            self.create_default_icon(icon_path_png)
            app_icon = QIcon(icon_path_png)
            
        self.setWindowIcon(app_icon)
        QApplication.setWindowIcon(app_icon)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 5, 0, 0)
        self.main_layout.setSpacing(0)
        
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(0)
        
        self.tab_bar = CustomTabBar()
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)
        self.tab_bar.app_now_moved.connect(self.on_app_moved_to_tab)
        self.tab_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.on_tab_context_menu)
        
        self.add_group_btn = QPushButton("+")
        self.add_group_btn.setObjectName("AddGroupButton")
        self.add_group_btn.setFixedSize(32, 32)
        self.add_group_btn.setCursor(Qt.PointingHandCursor)
        self.add_group_btn.clicked.connect(self.add_new_group)
        
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setObjectName("PinButton")
        self.pin_btn.setFixedSize(32, 32)
        self.pin_btn.setCheckable(True)
        self.pin_btn.clicked.connect(self.toggle_pin)
        

        header_layout.addWidget(self.tab_bar, 0, Qt.AlignLeft)
        header_layout.addWidget(self.add_group_btn, 0, Qt.AlignLeft)
        header_layout.addStretch() 
        header_layout.addWidget(self.pin_btn)
        
        self.main_layout.addWidget(header_container)
        
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        self.center_window()
        
        # 윈도우 위치/크기 복구
        geo = self.config.get_setting('window_geometry')
        if geo:
            try: self.setGeometry(geo['x'], geo['y'], geo['w'], geo['h'])
            except: self.center_window()

        self.initialize()
        try: apply_dark_title_bar(int(self.winId()))
        except: pass

    def showEvent(self, event):
        super().showEvent(event)
        try: apply_dark_title_bar(int(self.winId()))
        except: pass

    # Key Event Handling for Shortcuts
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta): return
        
        combo = QKeyCombination(modifiers, Qt.Key(key))
        sequence = QKeySequence(combo).toString(QKeySequence.NativeText)
        
        # 1. 앱 단축키 확인
        apps = self.config.get_apps()
        for app in apps:
            if app.get('shortcut') == sequence:
                cmd = app.get('action')
                if cmd:
                    try: os.startfile(cmd)
                    except:
                        try: subprocess.Popen(cmd, shell=True)
                        except: pass
                    return # 실행 후 종료

        # 2. 그룹 단축키 확인
        group_shortcuts = self.config.get_setting('group_shortcuts', {})
        for g_name, s_key in group_shortcuts.items():
            if s_key == sequence:
                # 해당 탭 찾기
                for i in range(self.tab_bar.count()):
                    if self.tab_bar.tabText(i) == g_name:
                        self.tab_bar.setCurrentIndex(i)
                        return
        
        super().keyPressEvent(event)

    # Drag & Drop Handling (External Files/URLs)
    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md.hasUrls() or md.hasText():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        md = event.mimeData()
        # 내부 이동(AppButton)은 CustomTabBar나 FlowLayout에서 처리되지만,
        # 윈도우 배경에 놓았을 때도 처리하려면 구분이 필요함.
        # 여기서는 외부 소스만 처리하도록 간단히 필터링 (내부 소스는 mime text가 앱 이름 등일 수 있음)
        # 하지만 hasUrls()는 파일 드롭시 확실함.
        
        if md.hasUrls():
            # 파일 또는 웹 링크(일부 브라우저는 url을 파일처럼 취급할 수도 있음)
            urls = md.urls()
            if urls:
                path = urls[0].toLocalFile()
                if path:
                    # 로컬 파일 드롭
                    self.add_app_from_path(path)
                else:
                    # 웹 링크 드롭 (브라우저에서 드래그 등)
                    url_text = urls[0].toString()
                    self.add_app_from_url(url_text)
            event.accept()
        elif md.hasText():
            text = md.text()
            # http로 시작하면 링크로 간주
            if text.startswith("http://") or text.startswith("https://"):
                self.add_app_from_url(text)
                event.accept()
            else:
                super().dropEvent(event)
        else:
            super().dropEvent(event)

    def add_app_from_path(self, path):
        # 파일/폴더 추가 다이얼로그 띄우기 (자동 채움)
        current_group = self.tab_bar.tabText(self.tab_bar.currentIndex())
        
        # 임시 데이터 구조 생성
        temp_data = {
            "name": os.path.splitext(os.path.basename(path))[0],
            "group": current_group,
            "action": path,
            "icon": ""
        }
        
        # 아이콘 추출 시도
        extracted = IconManager.extract_and_save_icon(path)
        if extracted: temp_data['icon'] = extracted
        
        # 다이얼로그 열기
        self.open_add_dialog_with_data(current_group, temp_data)

    def add_app_from_url(self, url):
        current_group = self.tab_bar.tabText(self.tab_bar.currentIndex())
        
        # 파비콘 가져오기 시도 (UI 멈춤 방지를 위해 스레드 쓰면 좋지만 간단하게 처리)
        # 사용자 경험을 위해 다이얼로그 띄우기 전에 가져오거나, 다이얼로그에서 가져오게 할 수 있음.
        # 여기서는 미리 가져와서 다이얼로그에 채워줌.
        favicon = IconManager.fetch_favicon(url)
        
        domain = urllib.parse.urlparse(url).netloc
        name = domain if domain else "New Link"
        
        temp_data = {
            "name": name,
            "group": current_group,
            "action": url,
            "icon": favicon if favicon else ""
        }
        
        self.open_add_dialog_with_data(current_group, temp_data)

    def open_add_dialog_with_data(self, group, data):
        occupied = self.get_all_shortcuts()
        dialog = AppEditDialog(self, app_data=data, current_group=group, occupied_shortcuts=occupied)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data.get('shortcut'):
                self.claim_shortcut(new_data['shortcut'])
            apps = self.config.get_apps()
            apps.append(new_data)
            self.config.set_apps(apps)
            self.reload_ui()

    def center_window(self):
        try:
            screen = QApplication.primaryScreen().geometry()
            size = self.geometry()
            self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
        except: pass

    def create_default_icon(self, path):
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, 64, 64)
        grad.setColorAt(0, QColor("#0A84FF"))
        grad.setColorAt(1, QColor("#005BB5"))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 64, 64, 16, 16)
        p.setPen(QColor("white"))
        font = QFont("Segoe UI", 36, QFont.Bold)
        p.setFont(font)
        p.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "B")
        p.end()
        try: pix.save(path, "PNG")
        except: pass

    def initialize(self):
        is_pinned = self.config.get_setting('always_on_top', False)
        self.pin_btn.setChecked(is_pinned)
        self.toggle_pin(is_pinned)
        self.reload_ui()

    def toggle_pin(self, checked):
        flags = self.windowFlags()
        if checked: flags |= Qt.WindowStaysOnTopHint
        else: flags &= ~Qt.WindowStaysOnTopHint
        
        # X 버튼 비활성화 방지
        flags |= Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint
        
        self.setWindowFlags(flags)
        self.show()
        self.config.set_setting('always_on_top', checked)
        try: apply_dark_title_bar(int(self.winId()))
        except: pass

    def closeEvent(self, event):
        geo = {'x': self.x(), 'y': self.y(), 'w': self.width(), 'h': self.height()}
        self.config.set_setting('window_geometry', geo)
        event.accept()

    def reload_ui(self):
        current_idx = self.tab_bar.currentIndex()
        while self.tab_bar.count() > 0: self.tab_bar.removeTab(0)
        while self.stacked_widget.count() > 0:
            w = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(w)
            w.deleteLater()

        apps = self.config.get_apps()
        groups = {}
        for app in apps:
            g = app.get('group', '홈') or '홈'
            if g not in groups: groups[g] = []
            groups[g].append(app)
        
        saved_order = self.config.get_setting('group_order', [])
        current_keys = list(groups.keys())
        processed = set()
        ordered_groups = []
        for g_name in saved_order:
            if g_name in groups:
                ordered_groups.append(g_name)
                processed.add(g_name)
            elif g_name not in current_keys:
                ordered_groups.append(g_name)
                processed.add(g_name)
        
        remaining = sorted([k for k in current_keys if k not in processed])
        for g_name in remaining: ordered_groups.append(g_name)
        if not ordered_groups: ordered_groups = ["홈"]
        
        for g_name in ordered_groups:
            self.tab_bar.addTab(g_name)
            self.add_page_content(g_name, groups.get(g_name, []))

        # 그룹 단축키 툴팁 설정
        group_shortcuts = self.config.get_setting('group_shortcuts', {})
        for i in range(self.tab_bar.count()):
            g_name = self.tab_bar.tabText(i)
            if g_name in group_shortcuts:
                self.tab_bar.setTabToolTip(i, f"단축키: {group_shortcuts[g_name]}")

        if current_idx >= 0 and current_idx < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(current_idx)
            self.stacked_widget.setCurrentIndex(current_idx)
        else:
            self.tab_bar.setCurrentIndex(0)
            self.stacked_widget.setCurrentIndex(0)

    def add_page_content(self, group_name, app_list):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        QScroller.grabGesture(scroll.viewport(), QScroller.LeftMouseButtonGesture)
        scroller = QScroller.scroller(scroll.viewport())
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.OvershootDragResistanceFactor, 0.3) 
        props.setScrollMetric(QScrollerProperties.OvershootDragDistanceFactor, 0.5) 
        props.setScrollMetric(QScrollerProperties.OvershootScrollDistanceFactor, 0.5) 
        props.setScrollMetric(QScrollerProperties.OvershootScrollTime, 0.5)
        props.setScrollMetric(QScrollerProperties.DragStartDistance, 0.002)
        props.setScrollMetric(QScrollerProperties.DecelerationFactor, 0.7)
        scroller.setScrollerProperties(props)
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        
        layout = FlowLayout(container, margin=LAYOUT_MARGIN, h_spacing=LAYOUT_H_SPACING, v_spacing=LAYOUT_V_SPACING)
        layout.setContentsMargins(10, 5, 10, 10)
        
        for app in app_list:
            btn = AppButton(app)
            btn.edit_requested.connect(partial(self.edit_app, app))
            btn.delete_requested.connect(partial(self.delete_app, app))
            btn.copy_requested.connect(partial(self.copy_app, app))
            btn.reorder_requested.connect(partial(self.swap_apps, app))
            layout.addWidget(btn)
        
        add_btn = AddButton()
        add_btn.clicked.connect(partial(self.add_new_app_dialog, group_name))
        layout.addWidget(add_btn)
        
        scroll.setWidget(container)
        self.stacked_widget.addWidget(scroll)

    def on_tab_changed(self, index):
        if index >= 0 and index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
    
    def on_tab_moved(self, from_idx, to_idx):
        order = []
        for i in range(self.tab_bar.count()): order.append(self.tab_bar.tabText(i))
        self.config.set_setting('group_order', order)
        widget = self.stacked_widget.widget(from_idx)
        self.stacked_widget.removeWidget(widget)
        self.stacked_widget.insertWidget(to_idx, widget)
        self.stacked_widget.setCurrentIndex(self.tab_bar.currentIndex())

    def on_app_moved_to_tab(self, source_btn, target_tab_index):
        target_group = self.tab_bar.tabText(target_tab_index)
        app_data = source_btn.data
        
        # 현재 그룹과 같으면 이동 안함
        current_group = app_data.get('group', '홈') or '홈'
        if current_group == target_group: return

        apps = self.config.get_apps()
        if app_data in apps:
            idx = apps.index(app_data)
            apps[idx]['group'] = target_group
            self.config.set_apps(apps)
            self.reload_ui()
            # 이동한 탭으로 포커스 이동 (사용자 편의)
            self.tab_bar.setCurrentIndex(target_tab_index)
            self.stacked_widget.setCurrentIndex(target_tab_index)

    def on_tab_context_menu(self, point):
        idx = self.tab_bar.tabAt(point)
        if idx < 0: return
        menu = QMenu(self)
        menu.addAction("이름 변경", lambda: self.rename_group(idx))
        menu.addAction("그룹 단축키 설정", lambda: self.set_group_shortcut(idx))
        menu.addSeparator()
        menu.addAction("그룹 삭제", lambda: self.delete_group(idx))
        menu.exec(self.tab_bar.mapToGlobal(point))
    
    def get_all_shortcuts(self, exclude_app=None, exclude_group=None):
        occupied = {}
        # Apps
        for app in self.config.get_apps():
            if app is exclude_app: continue
            s = app.get('shortcut')
            if s: occupied[s] = f"앱: {app.get('name')}"
        # Groups
        g_shorts = self.config.get_setting('group_shortcuts', {})
        for g, s in g_shorts.items():
            if g == exclude_group: continue
            if s: occupied[s] = f"그룹: {g}"
        return occupied

    def claim_shortcut(self, shortcut):
        # 중복된 단축키가 있으면 해당 소유자의 단축키를 제거
        if not shortcut: return
        apps = self.config.get_apps()
        changed = False
        for app in apps:
            if app.get('shortcut') == shortcut:
                app['shortcut'] = ""
                changed = True
        if changed: self.config.set_apps(apps)
        
        g_shorts = self.config.get_setting('group_shortcuts', {})
        new_g = {}
        for g, s in g_shorts.items():
            if s == shortcut: changed = True 
            else: new_g[g] = s
        if changed: self.config.set_setting('group_shortcuts', new_g)

    def set_group_shortcut(self, idx):
        g_name = self.tab_bar.tabText(idx)
        g_shorts = self.config.get_setting('group_shortcuts', {})
        cur_short = g_shorts.get(g_name, "")
        
        # 제외 대상(자기 자신) 지정하여 목록 생성
        occupied = self.get_all_shortcuts(exclude_group=g_name)
        
        dialog = ShortcutDialog(g_name, cur_short, occupied, self)
        if dialog.exec() == QDialog.Accepted:
            new_s = dialog.get_shortcut()
            if new_s:
                self.claim_shortcut(new_s) # 덮어쓰기 실행
                g_shorts[g_name] = new_s
            else:
                if g_name in g_shorts: del g_shorts[g_name]
            
            self.config.set_setting('group_shortcuts', g_shorts)
            self.reload_ui()

    def add_new_group(self):
        name, ok = QInputDialog.getText(self, "새 그룹", "그룹 이름:")
        if ok and name:
            self.tab_bar.addTab(name)
            self.add_page_content(name, [])
            order = self.config.get_setting('group_order', [])
            if name not in order: order.append(name)
            self.config.set_setting('group_order', order)
            idx = self.tab_bar.count() - 1
            self.tab_bar.setCurrentIndex(idx)
            self.stacked_widget.setCurrentIndex(idx)

    def rename_group(self, idx):
        old_name = self.tab_bar.tabText(idx)
        new_name, ok = QInputDialog.getText(self, "이름 변경", "새 이름:", text=old_name)
        if ok and new_name and new_name != old_name:
            self.tab_bar.setTabText(idx, new_name)
            apps = self.config.get_apps()
            for app in apps:
                 if app.get('group') == old_name: app['group'] = new_name
            self.config.set_apps(apps)
            
            # 그룹 단축키 이름 업데이트
            g_shorts = self.config.get_setting('group_shortcuts', {})
            if old_name in g_shorts:
                g_shorts[new_name] = g_shorts.pop(old_name)
            self.config.set_setting('group_shortcuts', g_shorts)

            order = self.config.get_setting('group_order', [])
            if old_name in order: order[order.index(old_name)] = new_name
            self.config.set_setting('group_order', order)
            self.reload_ui()
            
    def delete_group(self, idx):
        group_name = self.tab_bar.tabText(idx)
        reply = QMessageBox.question(self, "그룹 삭제", f"'{group_name}' 그룹을 삭제하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            apps = self.config.get_apps()
            new_apps = [a for a in apps if a.get('group', '홈') != group_name]
            self.config.set_apps(new_apps)
            
            # 그룹 단축키 삭제
            g_shorts = self.config.get_setting('group_shortcuts', {})
            if group_name in g_shorts:
                del g_shorts[group_name]
            self.config.set_setting('group_shortcuts', g_shorts)
            
            order = self.config.get_setting('group_order', [])
            if group_name in order: order.remove(group_name)
            self.config.set_setting('group_order', order)
            self.reload_ui()

    def add_new_app_dialog(self, group_name):
        occupied = self.get_all_shortcuts()
        dialog = AppEditDialog(self, current_group=group_name, occupied_shortcuts=occupied)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data.get('shortcut'):
                self.claim_shortcut(new_data['shortcut']) # 덮어쓰기
            apps = self.config.get_apps()
            apps.append(new_data)
            self.config.set_apps(apps)
            self.reload_ui()
    def edit_app(self, app_data):
        apps = self.config.get_apps()
        if app_data in apps:
            idx = apps.index(app_data)
            occupied = self.get_all_shortcuts(exclude_app=app_data)
            dialog = AppEditDialog(self, app_data, occupied_shortcuts=occupied)
            if dialog.exec() == QDialog.Accepted:
                new_data = dialog.get_data()
                if new_data.get('shortcut'):
                    self.claim_shortcut(new_data['shortcut'])
                apps[idx] = new_data
                self.config.set_apps(apps)
                self.reload_ui()
    def delete_app(self, app_data):
        if QMessageBox.question(self, "삭제", "이 앱을 삭제하시겠습니까?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            apps = self.config.get_apps()
            if app_data in apps:
                del_icon = app_data.get('icon')
                apps.remove(app_data)
                self.config.set_apps(apps)
                
                # 삭제된 앱의 아이콘이 더 이상 사용되지 않으면 삭제
                if del_icon:
                    IconManager.delete_if_unused(del_icon, apps)
                    
                self.reload_ui()
    def copy_app(self, app_data):
        apps = self.config.get_apps()
        if app_data in apps:
            idx = apps.index(app_data)
            new_app = app_data.copy()
            new_app['name'] += " (복사)"
            new_app['shortcut'] = "" # 복사 시 단축키는 제거 (충돌 방지)
            apps.insert(idx + 1, new_app)
            self.config.set_apps(apps)
            self.reload_ui()
    def swap_apps(self, target_app_data, source_btn):
        source_data = source_btn.data
        if source_data == target_app_data: return
        apps = self.config.get_apps()
        try:
            idx1 = apps.index(source_data)
            idx2 = apps.index(target_app_data)
            apps[idx1], apps[idx2] = apps[idx2], apps[idx1]
            self.config.set_apps(apps)
            self.reload_ui()
        except: pass

    def show_main_context_menu(self, point):
        # 탭바나 다른 위젯 위가 아닌 경우에만 표시 (필요 시 로직 정교화)
        menu = QMenu(self)
        menu.addAction("프리셋 로드", self.load_preset)
        menu.exec(self.mapToGlobal(point))

    def load_preset(self):
        f, _ = QFileDialog.getOpenFileName(self, "프리셋(Config) 선택", "", "JSON Files (*.json)")
        if not f: return
        
        try:
            with open(f, 'r', encoding='utf-8') as json_file:
                new_data = json.load(json_file)
            
            # 유효성 검사 (간단)
            if 'apps' not in new_data and 'settings' not in new_data:
                QMessageBox.warning(self, "오류", "유효하지 않은 Bifrost 설정 파일입니다.")
                return
                
            # 안전 장치 1: 확인
            reply = QMessageBox.question(
                self, "프리셋 로드 확인", 
                "현재 설정이 선택한 프리셋으로 덮어씌워집니다.\n계속하시겠습니까?\n(현재 설정은 자동으로 백업됩니다)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No: return
            
            # 안전 장치 2: 자동 백업
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}.json"
            backup_path = os.path.join(BASE_DIR, backup_name)
            try:
                shutil.copy2(CONFIG_FILE, backup_path)
            except Exception as e:
                log_error(f"Backup failed: {e}")
                QMessageBox.critical(self, "오류", f"백업 생성에 실패했습니다. 작업을 중단합니다.\n{e}")
                return

            # 적용
            self.config.data = new_data
            self.config.save_config()
            self.reload_ui()
            QMessageBox.information(self, "완료", f"프리셋이 로드되었습니다.\n현재 설정은 '{backup_name}'에 백업되었습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"피리셋 로드 중 오류 발생:\n{e}")

if __name__ == "__main__":
    try:
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        import ctypes
        myappid = 'antigravity.bifrost.launcher.v0.3' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        
        icon_path_ico = os.path.join(ICON_DIR, "app_icon.ico")
        icon_path_png = os.path.join(ICON_DIR, "app_icon.png")

        if os.path.exists(icon_path_ico):
            app.setWindowIcon(QIcon(icon_path_ico))
        elif os.path.exists(icon_path_png):
            app.setWindowIcon(QIcon(icon_path_png))
        
        window = BifrostWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        log_error(f"Critical Error in main: {traceback.format_exc()}")
        try:
            tmp_app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Bifrost Error", f"실행 중 오류가 발생했습니다:\n{e}")
        except: pass