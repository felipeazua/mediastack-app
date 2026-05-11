"""
MediaStack — DIT-style media management for film/audiovisual students
Interfaz gráfica completa con PySide6.

Uso: python mediastack_gui.py
O empaquetado: MediaStack.exe (doble click)
"""

import base64
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt, QObject, QThread, Signal, QSize, QTimer, QSettings, QUrl
)
from PySide6.QtGui import (
    QPixmap, QIcon, QAction, QFont, QColor, QPalette, QDesktopServices
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QSplitter, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QStyle, QStyledItemDelegate, QAbstractItemView, QMenu,
    QDialog, QDialogButtonBox, QFormLayout, QSpacerItem, QStatusBar
)

# ==================== CONSTANTS ====================

APP_NAME = "MediaStack"
APP_VERSION = "1.0"
ORG = "MediaStack"

VIDEO_EXTS = {
    '.mov', '.mp4', '.mxf', '.avi', '.mkv', '.m4v',
    '.braw', '.r3d', '.ari', '.arx', '.mts', '.m2ts',
    '.wav', '.aif', '.aiff', '.dpx', '.exr',
    '.tiff', '.tif', '.jpg', '.jpeg', '.cine', '.ocn'
}

CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB - good balance for SSDs and HDDs

APP_DATA = Path.home() / '.mediastack'
APP_DATA.mkdir(exist_ok=True)
THUMBS_DIR = APP_DATA / 'thumbnails'
THUMBS_DIR.mkdir(exist_ok=True)
LIBRARY_FILE = APP_DATA / 'library.json'
SESSIONS_FILE = APP_DATA / 'sessions.json'

# ==================== STYLING ====================

DARK_STYLE = """
QMainWindow, QWidget {
    background: #1a1a1a;
    color: #e8e8e8;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
}
QFrame#card {
    background: #232323;
    border: 1px solid #353535;
    border-radius: 6px;
}
QPushButton {
    background: #2a2a2a;
    border: 1px solid #353535;
    color: #e8e8e8;
    padding: 7px 14px;
    border-radius: 4px;
    min-height: 18px;
}
QPushButton:hover {
    background: #333;
    border-color: #454545;
}
QPushButton:pressed {
    background: #202020;
}
QPushButton:disabled {
    color: #555;
    background: #1f1f1f;
}
QPushButton#primary {
    background: #4a9eff;
    color: white;
    border-color: #4a9eff;
    font-weight: 500;
}
QPushButton#primary:hover {
    background: #5cabff;
}
QPushButton#primary:disabled {
    background: #2a3f5a;
    color: #888;
}
QPushButton#danger {
    background: #2a2a2a;
    color: #f87171;
    border-color: #353535;
}
QLineEdit, QComboBox {
    background: #232323;
    border: 1px solid #353535;
    color: #e8e8e8;
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 18px;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #4a9eff;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #232323;
    border: 1px solid #454545;
    selection-background-color: #4a9eff;
    color: #e8e8e8;
}
QTabWidget::pane {
    border: none;
    background: #1a1a1a;
}
QTabBar::tab {
    background: transparent;
    color: #999;
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:hover { color: #e8e8e8; }
QTabBar::tab:selected {
    color: #e8e8e8;
    border-bottom-color: #4a9eff;
}
QProgressBar {
    background: #2a2a2a;
    border: none;
    border-radius: 3px;
    text-align: center;
    color: #ccc;
    height: 8px;
}
QProgressBar::chunk {
    background: #4a9eff;
    border-radius: 3px;
}
QProgressBar#done::chunk { background: #4ade80; }
QProgressBar#error::chunk { background: #f87171; }
QHeaderView::section {
    background: #2a2a2a;
    color: #999;
    padding: 8px 12px;
    border: none;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
}
QTableWidget {
    background: #1a1a1a;
    border: 1px solid #353535;
    border-radius: 4px;
    gridline-color: #2a2a2a;
    selection-background-color: #2d4a6e;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2a2a2a;
}
QTableWidget::item:selected { background: #2d4a6e; }
QListWidget {
    background: #1a1a1a;
    border: 1px solid #353535;
    border-radius: 4px;
    outline: 0;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #454545;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #555; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QStatusBar {
    background: #232323;
    color: #999;
    border-top: 1px solid #353535;
}
QLabel#sectionTitle {
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLabel#brandTitle {
    font-size: 14px;
    font-weight: 500;
}
QLabel#brandSub {
    font-size: 11px;
    color: #999;
}
QLabel#statValue {
    font-size: 22px;
    font-weight: 500;
}
QLabel#statLabel {
    font-size: 11px;
    color: #999;
    text-transform: uppercase;
}
QLabel#statusPill {
    background: #1a2a1a;
    color: #4ade80;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
}
QLabel#statusPillActive {
    background: #1a2a4a;
    color: #4a9eff;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
}
"""

# ==================== HELPERS ====================

def fmt_bytes(b):
    if not b:
        return '0 B'
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    b = float(b)
    while b >= 1024 and i < len(units) - 1:
        b /= 1024
        i += 1
    if b >= 100:
        return f'{b:.0f} {units[i]}'
    if b >= 10:
        return f'{b:.1f} {units[i]}'
    return f'{b:.2f} {units[i]}'


def fmt_duration(seconds):
    if not seconds or seconds <= 0:
        return '—'
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f'{h:02d}:{m:02d}:{sec:02d}'
    return f'{m:02d}:{sec:02d}'


def fmt_speed(bytes_per_sec):
    if bytes_per_sec < 1024 * 1024:
        return f'{bytes_per_sec / 1024:.0f} KB/s'
    if bytes_per_sec < 1024 * 1024 * 1024:
        return f'{bytes_per_sec / 1024 / 1024:.1f} MB/s'
    return f'{bytes_per_sec / 1024 / 1024 / 1024:.2f} GB/s'


def find_ffmpeg():
    """Find ffmpeg/ffprobe. Check PATH and common bundled locations."""
    # Check if bundled with frozen executable
    if getattr(sys, 'frozen', False):
        bundle_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
        for name in ['ffmpeg.exe', 'ffmpeg']:
            p = bundle_dir / name
            if p.exists():
                return str(p), str(bundle_dir / ('ffprobe.exe' if name.endswith('.exe') else 'ffprobe'))

    # Check PATH
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    if ffmpeg and ffprobe:
        return ffmpeg, ffprobe
    return None, None


FFMPEG, FFPROBE = find_ffmpeg()


def scan_folder(path):
    files = []
    base = Path(path)
    if not base.exists():
        return files
    try:
        for p in base.rglob('*'):
            if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
                try:
                    files.append({
                        'name': p.name,
                        'path': str(p),
                        'size': p.stat().st_size,
                    })
                except OSError:
                    continue
    except (PermissionError, OSError):
        pass
    files.sort(key=lambda f: f['name'])
    return files


# ==================== CHECKSUM ====================
# Try fast native xxhash first; fall back to MD5 (which is C-native in hashlib).

try:
    import xxhash as _xxh
    HAS_FAST_XXHASH = True
except ImportError:
    HAS_FAST_XXHASH = False


def make_hasher(method):
    m = method.lower()
    if m in ('xxhash64', 'xxhash'):
        if HAS_FAST_XXHASH:
            return _xxh.xxh64()
        # Fallback: use MD5 (fast, native) silently. We tell the user in UI.
        return hashlib.md5()
    if m == 'md5':
        return hashlib.md5()
    if m == 'sha1':
        return hashlib.sha1()
    return hashlib.md5()


def hasher_label(method):
    """What we ACTUALLY use vs what user asked for."""
    m = method.lower()
    if m in ('xxhash64', 'xxhash'):
        return 'xxhash64' if HAS_FAST_XXHASH else 'md5'
    return m


# ==================== METADATA & THUMBNAILS ====================

def probe_clip(path):
    if not FFPROBE:
        return {}
    try:
        result = subprocess.run(
            [FFPROBE, '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height,r_frame_rate,codec_name:format=duration',
             '-of', 'json', str(path)],
            capture_output=True, text=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        if result.returncode != 0:
            return {}
        data = json.loads(result.stdout)
        stream = data.get('streams', [{}])[0] if data.get('streams') else {}
        fmt = data.get('format', {})
        meta = {}
        w, h = stream.get('width'), stream.get('height')
        if w and h:
            meta['resolution'] = f'{w}x{h}'
        if stream.get('codec_name'):
            meta['codec'] = stream['codec_name']
        if stream.get('r_frame_rate'):
            try:
                num, den = stream['r_frame_rate'].split('/')
                if int(den) > 0:
                    meta['fps'] = f'{int(num) / int(den):.3f}'
            except (ValueError, ZeroDivisionError):
                pass
        if fmt.get('duration'):
            try:
                meta['duration'] = float(fmt['duration'])
            except ValueError:
                pass
        return meta
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return {}


def generate_thumbnail(src_path, clip_id):
    if not FFMPEG:
        return None
    out = THUMBS_DIR / f'{clip_id}.jpg'
    if out.exists():
        return str(out)
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    try:
        # Try at 2 seconds first
        r = subprocess.run(
            [FFMPEG, '-y', '-loglevel', 'error', '-ss', '2', '-i', str(src_path),
             '-frames:v', '1', '-vf', 'scale=480:-2', '-q:v', '4', str(out)],
            capture_output=True, timeout=30, creationflags=flags
        )
        if r.returncode != 0 or not out.exists():
            # Fallback: first frame
            subprocess.run(
                [FFMPEG, '-y', '-loglevel', 'error', '-i', str(src_path),
                 '-frames:v', '1', '-vf', 'scale=480:-2', '-q:v', '4', str(out)],
                capture_output=True, timeout=30, creationflags=flags
            )
        return str(out) if out.exists() else None
    except (subprocess.TimeoutExpired, OSError):
        return None


# ==================== LIBRARY ====================

def load_library():
    if LIBRARY_FILE.exists():
        try:
            return json.loads(LIBRARY_FILE.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_library(clips):
    try:
        LIBRARY_FILE.write_text(json.dumps(clips, indent=2, ensure_ascii=False), encoding='utf-8')
    except OSError as e:
        print(f"Library save error: {e}")


def add_to_library(new_clips):
    lib = load_library()
    existing_hashes = {c.get('checksum') for c in lib if c.get('checksum')}
    for c in new_clips:
        if c.get('checksum') and c['checksum'] not in existing_hashes:
            lib.append(c)
            existing_hashes.add(c['checksum'])
    save_library(lib)
    return lib


def save_session(session):
    try:
        sessions = []
        if SESSIONS_FILE.exists():
            sessions = json.loads(SESSIONS_FILE.read_text(encoding='utf-8'))
        sessions.append(session)
        sessions = sessions[-50:]  # Keep last 50
        SESSIONS_FILE.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding='utf-8')
    except (OSError, json.JSONDecodeError):
        pass


# ==================== OFFLOAD WORKER (background thread) ====================

class OffloadWorker(QObject):
    """Runs the offload in a background thread so UI stays responsive."""

    file_started = Signal(str, int)  # name, total_bytes
    file_progress = Signal(str, int, int, str, float)  # name, done, total, stage, speed
    file_finished = Signal(str, bool, str)  # name, success, message
    clip_added = Signal(dict)  # clip dict for browser to update
    session_finished = Signal(dict)  # final session info
    log = Signal(str, str)  # level, message

    def __init__(self, source, destinations, checksum_method, parent=None):
        super().__init__(parent)
        self.source = source
        self.destinations = destinations
        self.checksum_method = checksum_method
        self.actual_method = hasher_label(checksum_method)
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        files = scan_folder(self.source)
        if not files:
            self.log.emit('warning', 'No se encontraron archivos de video en la carpeta origen.')
            self.session_finished.emit({'clips': [], 'errors': []})
            return

        total_size = sum(f['size'] for f in files)
        self.log.emit('info', f'Encontrados {len(files)} archivos ({fmt_bytes(total_size)})')

        # Make destinations
        for d in self.destinations:
            try:
                Path(d).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                self.log.emit('error', f'No se pudo crear destino {d}: {e}')
                self.session_finished.emit({'clips': [], 'errors': [str(e)]})
                return

        session_clips = []
        errors = []
        start = time.time()

        for file in files:
            if self._cancel:
                self.log.emit('info', 'Cancelado por el usuario.')
                break

            try:
                clip = self._process_file(file)
                if clip:
                    session_clips.append(clip)
                    self.clip_added.emit(clip)
            except Exception as e:
                errors.append(f'{file["name"]}: {e}')
                self.file_finished.emit(file['name'], False, str(e))
                self.log.emit('error', f'{file["name"]}: {e}')

        elapsed = time.time() - start
        if session_clips:
            add_to_library(session_clips)

        session = {
            'source': self.source,
            'destinations': self.destinations,
            'checksum_method': self.actual_method,
            'date': datetime.now().isoformat(),
            'clips': session_clips,
            'errors': errors,
            'elapsed_seconds': elapsed,
        }
        save_session(session)
        self.session_finished.emit(session)

    def _process_file(self, file):
        name = file['name']
        size = file['size']
        src = Path(file['path'])
        dests = [Path(d) / name for d in self.destinations]

        # Skip if all destinations already exist with matching size
        if all(p.exists() and p.stat().st_size == size for p in dests):
            self.file_finished.emit(name, True, 'Skipped (already exists)')
            return None

        self.file_started.emit(name, size)

        hasher = make_hasher(self.checksum_method)
        writers = []
        try:
            for dp in dests:
                writers.append(open(dp, 'wb'))

            done = 0
            t0 = time.time()
            last_emit = 0

            with open(src, 'rb') as f:
                while True:
                    if self._cancel:
                        # Clean up partial files
                        for w in writers:
                            w.close()
                        for dp in dests:
                            try:
                                if dp.exists():
                                    dp.unlink()
                            except OSError:
                                pass
                        raise InterruptedError('Cancelled')

                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    for w in writers:
                        w.write(chunk)
                    hasher.update(chunk)
                    done += len(chunk)

                    now = time.time()
                    if now - last_emit > 0.15:
                        speed = done / (now - t0) if now > t0 else 0
                        self.file_progress.emit(name, done, size, 'copying', speed)
                        last_emit = now

            for w in writers:
                w.flush()
                try:
                    os.fsync(w.fileno())
                except OSError:
                    pass
                w.close()
            writers = []

            source_hash = hasher.hexdigest()

            # Verify each destination
            for dp in dests:
                if self._cancel:
                    raise InterruptedError('Cancelled')
                h = make_hasher(self.checksum_method)
                vdone = 0
                vt0 = time.time()
                vlast = 0
                with open(dp, 'rb') as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        h.update(chunk)
                        vdone += len(chunk)
                        now = time.time()
                        if now - vlast > 0.15:
                            speed = vdone / (now - vt0) if now > vt0 else 0
                            self.file_progress.emit(name, vdone, size, 'verifying', speed)
                            vlast = now
                if h.hexdigest() != source_hash:
                    raise ValueError(f'Checksum mismatch on {dp.name}')

            # Build clip record
            clip_id = uuid.uuid4().hex[:12]
            meta = probe_clip(dests[0])
            thumb = generate_thumbnail(dests[0], clip_id)

            clip = {
                'id': clip_id,
                'name': name,
                'path': str(dests[0]),
                'all_paths': [str(p) for p in dests],
                'size_bytes': size,
                'checksum': source_hash,
                'checksum_method': self.actual_method,
                'thumbnail': thumb,
                'resolution': meta.get('resolution'),
                'codec': meta.get('codec'),
                'fps': meta.get('fps'),
                'duration': meta.get('duration', 0),
                'extension': src.suffix.lower().lstrip('.'),
                'added_at': datetime.now().isoformat(),
            }

            self.file_finished.emit(name, True, 'Verified')
            return clip

        except InterruptedError:
            raise
        except Exception as e:
            for w in writers:
                try:
                    w.close()
                except Exception:
                    pass
            raise


# ==================== CLIP CARD WIDGET ====================

class ClipCard(QFrame):
    """Single clip card for the grid view."""
    clicked = Signal(dict)

    def __init__(self, clip, thumb_size=180):
        super().__init__()
        self.clip = clip
        self.thumb_size = thumb_size
        self.setObjectName("clipCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#clipCard {
                background: #232323;
                border: 1px solid #353535;
                border-radius: 6px;
            }
            QFrame#clipCard:hover {
                border-color: #4a9eff;
            }
        """)
        self.setFixedWidth(thumb_size)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Thumbnail
        thumb_h = int(thumb_size * 9 / 16)
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(thumb_size, thumb_h)
        self.thumb_label.setStyleSheet("background: #000; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        self.thumb_label.setAlignment(Qt.AlignCenter)

        if clip.get('thumbnail') and Path(clip['thumbnail']).exists():
            pix = QPixmap(clip['thumbnail'])
            if not pix.isNull():
                pix = pix.scaled(thumb_size, thumb_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.thumb_label.setPixmap(pix)
        else:
            self.thumb_label.setText("No preview")
            self.thumb_label.setStyleSheet("background: #000; color: #555; font-size: 11px; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        v.addWidget(self.thumb_label)

        # Info
        info = QWidget()
        info_v = QVBoxLayout(info)
        info_v.setContentsMargins(10, 8, 10, 8)
        info_v.setSpacing(2)

        name_lbl = QLabel(clip['name'])
        name_lbl.setStyleSheet("font-size: 12px; font-weight: 500; color: #e8e8e8;")
        name_lbl.setWordWrap(False)
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(name_lbl.font())
        elided = fm.elidedText(clip['name'], Qt.ElideMiddle, thumb_size - 20)
        name_lbl.setText(elided)
        info_v.addWidget(name_lbl)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        ext = clip.get('extension', '').upper() or '—'
        res = clip.get('resolution') or fmt_duration(clip.get('duration', 0))
        meta1 = QLabel(f"{ext}  ·  {res}")
        meta1.setStyleSheet("font-size: 10px; color: #888;")
        meta_row.addWidget(meta1)
        meta_row.addStretch()
        size_lbl = QLabel(fmt_bytes(clip['size_bytes']))
        size_lbl.setStyleSheet("font-size: 10px; color: #888;")
        meta_row.addWidget(size_lbl)
        info_v.addLayout(meta_row)
        v.addWidget(info)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.clip)
        super().mousePressEvent(event)


# ==================== DETAIL DIALOG ====================

class ClipDetailDialog(QDialog):
    def __init__(self, clip, parent=None):
        super().__init__(parent)
        self.clip = clip
        self.setWindowTitle(clip['name'])
        self.setMinimumSize(720, 480)
        self.setStyleSheet(DARK_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Top: thumbnail + metadata
        top = QHBoxLayout()
        top.setSpacing(20)

        # Thumbnail
        thumb_lbl = QLabel()
        thumb_lbl.setFixedSize(360, 203)
        thumb_lbl.setStyleSheet("background: #000; border-radius: 6px;")
        thumb_lbl.setAlignment(Qt.AlignCenter)
        if clip.get('thumbnail') and Path(clip['thumbnail']).exists():
            pix = QPixmap(clip['thumbnail']).scaled(360, 203, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb_lbl.setPixmap(pix)
        else:
            thumb_lbl.setText("No preview available")
            thumb_lbl.setStyleSheet("background: #000; color: #555; border-radius: 6px;")
        top.addWidget(thumb_lbl)

        # Metadata
        meta_w = QWidget()
        meta_v = QVBoxLayout(meta_w)
        meta_v.setContentsMargins(0, 0, 0, 0)
        meta_v.setSpacing(8)

        title = QLabel(clip['name'])
        title.setStyleSheet("font-size: 16px; font-weight: 500;")
        title.setWordWrap(True)
        meta_v.addWidget(title)

        meta_v.addSpacing(8)

        def row(label, value):
            r = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet("color: #888; font-size: 11px; min-width: 100px;")
            v = QLabel(str(value) if value else '—')
            v.setStyleSheet("color: #e8e8e8; font-size: 12px;")
            v.setWordWrap(True)
            r.addWidget(l)
            r.addWidget(v, 1)
            return r

        meta_v.addLayout(row("Formato", clip.get('extension', '').upper()))
        meta_v.addLayout(row("Resolución", clip.get('resolution')))
        meta_v.addLayout(row("Codec", clip.get('codec')))
        meta_v.addLayout(row("FPS", clip.get('fps')))
        meta_v.addLayout(row("Duración", fmt_duration(clip.get('duration', 0))))
        meta_v.addLayout(row("Tamaño", fmt_bytes(clip.get('size_bytes', 0))))
        meta_v.addLayout(row(f"{clip.get('checksum_method', '').upper()}",
                              clip.get('checksum', '')[:16] + '...'))
        meta_v.addStretch()
        top.addWidget(meta_w, 1)
        layout.addLayout(top)

        # Path
        layout.addSpacing(12)
        path_lbl = QLabel("Ubicación")
        path_lbl.setObjectName("sectionTitle")
        layout.addWidget(path_lbl)
        path_val = QLabel(clip['path'])
        path_val.setStyleSheet("font-family: monospace; font-size: 11px; color: #ccc; padding: 6px; background: #1a1a1a; border: 1px solid #353535; border-radius: 4px;")
        path_val.setWordWrap(True)
        path_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(path_val)

        if len(clip.get('all_paths', [])) > 1:
            layout.addSpacing(8)
            backups_lbl = QLabel("Copias de respaldo")
            backups_lbl.setObjectName("sectionTitle")
            layout.addWidget(backups_lbl)
            for p in clip['all_paths'][1:]:
                pl = QLabel(p)
                pl.setStyleSheet("font-family: monospace; font-size: 10px; color: #999; padding: 4px;")
                pl.setWordWrap(True)
                layout.addWidget(pl)

        # Buttons
        layout.addSpacing(16)
        btns = QHBoxLayout()
        open_folder = QPushButton("Abrir carpeta")
        open_folder.clicked.connect(self._open_folder)
        play_btn = QPushButton("Reproducir con app del sistema")
        play_btn.clicked.connect(self._play)
        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(open_folder)
        btns.addWidget(play_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        layout.addLayout(btns)

    def _open_folder(self):
        folder = str(Path(self.clip['path']).parent)
        if sys.platform == 'win32':
            subprocess.Popen(['explorer', '/select,', self.clip['path']])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', self.clip['path']])
        else:
            subprocess.Popen(['xdg-open', folder])

    def _play(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.clip['path']))


# ==================== BROWSER TAB ====================

class BrowserTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clips = []
        self.filtered = []
        self.thumb_size = 180
        self._build()
        self.refresh()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por nombre de clip...")
        self.search.textChanged.connect(self._filter)
        toolbar.addWidget(self.search, 1)

        self.format_filter = QComboBox()
        self.format_filter.addItems(["Todos los formatos", "MOV", "MP4", "MXF", "BRAW", "R3D", "ARI"])
        self.format_filter.currentIndexChanged.connect(self._filter)
        toolbar.addWidget(self.format_filter)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)

        v.addLayout(toolbar)

        # Stats
        self.stats_lbl = QLabel("0 clips")
        self.stats_lbl.setStyleSheet("color: #888; font-size: 11px;")
        v.addWidget(self.stats_lbl)

        # Scroll area with grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.grid_container)
        v.addWidget(self.scroll, 1)

    def refresh(self):
        self.clips = load_library()
        self._filter()

    def _filter(self):
        q = self.search.text().lower().strip()
        fmt = self.format_filter.currentText()
        result = []
        for c in self.clips:
            if q and q not in c['name'].lower():
                continue
            if fmt != "Todos los formatos":
                if c.get('extension', '').upper() != fmt:
                    continue
            result.append(c)
        self.filtered = result
        self._render()

    def _render(self):
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Update stats
        total_size = sum(c.get('size_bytes', 0) for c in self.filtered)
        self.stats_lbl.setText(f"{len(self.filtered)} clips · {fmt_bytes(total_size)}")

        # Compute columns based on width
        viewport_width = self.scroll.viewport().width()
        cols = max(1, viewport_width // (self.thumb_size + 12))

        for i, clip in enumerate(self.filtered):
            r, c = divmod(i, cols)
            card = ClipCard(clip, self.thumb_size)
            card.clicked.connect(self._open_detail)
            self.grid_layout.addWidget(card, r, c)

    def _open_detail(self, clip):
        dialog = ClipDetailDialog(clip, self)
        dialog.exec()

    def add_clip(self, clip):
        self.clips.append(clip)
        self._filter()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'filtered'):
            self._render()


# ==================== OFFLOAD TAB ====================

class OffloadTab(QWidget):
    clip_added = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = ""
        self.destinations = []
        self.worker = None
        self.thread = None
        self.files_in_queue = []
        self.row_for_file = {}
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        # Source card
        src_card = QFrame()
        src_card.setObjectName("card")
        src_v = QVBoxLayout(src_card)
        src_v.setContentsMargins(14, 12, 14, 12)
        src_v.setSpacing(8)
        lbl = QLabel("ORIGEN")
        lbl.setObjectName("sectionTitle")
        src_v.addWidget(lbl)
        src_row = QHBoxLayout()
        self.src_display = QLabel("Ninguna carpeta seleccionada")
        self.src_display.setStyleSheet("color: #ccc; font-size: 12px;")
        self.src_display.setWordWrap(True)
        src_row.addWidget(self.src_display, 1)
        pick_src = QPushButton("Elegir carpeta origen...")
        pick_src.clicked.connect(self._pick_source)
        src_row.addWidget(pick_src)
        src_v.addLayout(src_row)
        self.src_info = QLabel("")
        self.src_info.setStyleSheet("color: #888; font-size: 11px;")
        src_v.addWidget(self.src_info)
        v.addWidget(src_card)

        # Destinations card
        dst_card = QFrame()
        dst_card.setObjectName("card")
        dst_v = QVBoxLayout(dst_card)
        dst_v.setContentsMargins(14, 12, 14, 12)
        dst_v.setSpacing(8)
        dst_lbl = QLabel("DESTINOS (COPIA EN CASCADA)")
        dst_lbl.setObjectName("sectionTitle")
        dst_v.addWidget(dst_lbl)
        self.dst_list = QVBoxLayout()
        self.dst_list.setSpacing(4)
        dst_v.addLayout(self.dst_list)
        add_dst = QPushButton("Agregar destino...")
        add_dst.clicked.connect(self._add_destination)
        dst_v.addWidget(add_dst, alignment=Qt.AlignLeft)
        v.addWidget(dst_card)
        self._render_destinations()

        # Action row
        actions = QHBoxLayout()
        self.start_btn = QPushButton("Iniciar offload")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._start)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setVisible(False)
        actions.addWidget(self.start_btn)
        actions.addWidget(self.cancel_btn)
        actions.addStretch()

        actions.addWidget(QLabel("Checksum:"))
        self.cs_combo = QComboBox()
        # Build options based on what's available
        if HAS_FAST_XXHASH:
            self.cs_combo.addItems(["xxHash64 (rápido, recomendado)", "MD5", "SHA1"])
        else:
            self.cs_combo.addItems(["MD5 (rápido, recomendado)", "SHA1"])
        actions.addWidget(self.cs_combo)
        v.addLayout(actions)

        # File list
        self.file_table = QTableWidget(0, 4)
        self.file_table.setHorizontalHeaderLabels(["Archivo", "Tamaño", "Progreso", "Estado"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.file_table.setColumnWidth(2, 200)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.file_table.setShowGrid(False)
        v.addWidget(self.file_table, 1)

    def _pick_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Elegir carpeta origen")
        if folder:
            self.source = folder
            self.src_display.setText(folder)
            self._scan_source()

    def _scan_source(self):
        files = scan_folder(self.source)
        self.files_in_queue = files
        total = sum(f['size'] for f in files)
        self.src_info.setText(f"{len(files)} archivos de video · {fmt_bytes(total)}")
        # Populate table
        self.file_table.setRowCount(0)
        self.row_for_file = {}
        for f in files:
            r = self.file_table.rowCount()
            self.file_table.insertRow(r)
            self.row_for_file[f['name']] = r
            self.file_table.setItem(r, 0, QTableWidgetItem(f['name']))
            sz = QTableWidgetItem(fmt_bytes(f['size']))
            sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.file_table.setItem(r, 1, sz)
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setValue(0)
            pb.setTextVisible(False)
            self.file_table.setCellWidget(r, 2, pb)
            self.file_table.setItem(r, 3, QTableWidgetItem("Pendiente"))

    def _add_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Elegir destino")
        if folder and folder not in self.destinations:
            self.destinations.append(folder)
            self._render_destinations()

    def _render_destinations(self):
        # Clear existing
        while self.dst_list.count():
            item = self.dst_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.destinations:
            empty = QLabel("Ningún destino agregado")
            empty.setStyleSheet("color: #888; font-size: 11px;")
            self.dst_list.addWidget(empty)
            return
        for i, d in enumerate(self.destinations):
            row = QWidget()
            r = QHBoxLayout(row)
            r.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(d)
            lbl.setStyleSheet("color: #ccc; font-size: 12px; font-family: monospace;")
            lbl.setWordWrap(True)
            r.addWidget(lbl, 1)
            rm = QPushButton("×")
            rm.setFixedSize(28, 28)
            rm.clicked.connect(lambda _, idx=i: self._remove_destination(idx))
            r.addWidget(rm)
            self.dst_list.addWidget(row)

    def _remove_destination(self, i):
        if 0 <= i < len(self.destinations):
            self.destinations.pop(i)
            self._render_destinations()

    def _start(self):
        if not self.source:
            QMessageBox.warning(self, "Falta origen", "Por favor selecciona una carpeta origen.")
            return
        if not self.destinations:
            QMessageBox.warning(self, "Faltan destinos", "Agrega al menos un destino.")
            return
        if not self.files_in_queue:
            QMessageBox.warning(self, "Sin archivos", "La carpeta origen no contiene archivos de video reconocidos.")
            return

        # Determine checksum method
        cs_text = self.cs_combo.currentText()
        if cs_text.startswith('xxHash'):
            method = 'xxhash64'
        elif cs_text.startswith('SHA'):
            method = 'sha1'
        else:
            method = 'md5'

        # Disable controls
        self.start_btn.setVisible(False)
        self.cancel_btn.setVisible(True)

        # Reset progress
        for name, row in self.row_for_file.items():
            pb = self.file_table.cellWidget(row, 2)
            if pb:
                pb.setValue(0)
                pb.setObjectName("")
                pb.setStyleSheet("")
            self.file_table.setItem(row, 3, QTableWidgetItem("Pendiente"))

        # Start worker
        self.thread = QThread()
        self.worker = OffloadWorker(self.source, list(self.destinations), method)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.file_started.connect(self._on_file_started)
        self.worker.file_progress.connect(self._on_file_progress)
        self.worker.file_finished.connect(self._on_file_finished)
        self.worker.clip_added.connect(self.clip_added.emit)
        self.worker.session_finished.connect(self._on_session_finished)
        self.worker.log.connect(self._on_log)
        self.thread.start()

    def _cancel(self):
        if self.worker:
            self.worker.cancel()
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelando...")

    def _on_file_started(self, name, total):
        row = self.row_for_file.get(name)
        if row is not None:
            self.file_table.setItem(row, 3, QTableWidgetItem("Copiando..."))

    def _on_file_progress(self, name, done, total, stage, speed):
        row = self.row_for_file.get(name)
        if row is None:
            return
        pb = self.file_table.cellWidget(row, 2)
        if pb and total > 0:
            pb.setValue(int(done * 100 / total))
        label = "Copiando" if stage == 'copying' else "Verificando"
        status = f"{label} · {fmt_speed(speed)}"
        self.file_table.setItem(row, 3, QTableWidgetItem(status))

    def _on_file_finished(self, name, success, message):
        row = self.row_for_file.get(name)
        if row is None:
            return
        pb = self.file_table.cellWidget(row, 2)
        if pb:
            pb.setValue(100)
            pb.setObjectName("done" if success else "error")
            pb.setStyleSheet("QProgressBar::chunk { background: " + ("#4ade80" if success else "#f87171") + "; }")
        item = QTableWidgetItem(("✓ " if success else "✗ ") + message)
        item.setForeground(QColor("#4ade80" if success else "#f87171"))
        self.file_table.setItem(row, 3, item)

    def _on_session_finished(self, session):
        self.start_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancelar")
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None

        clips = session.get('clips', [])
        errors = session.get('errors', [])
        if clips:
            msg = f"Offload completado.\n\n{len(clips)} clips copiados y verificados."
            if errors:
                msg += f"\n{len(errors)} errores."
            QMessageBox.information(self, "Listo", msg)

    def _on_log(self, level, message):
        # Could route to a log panel; for now just print
        print(f"[{level}] {message}")


# ==================== REPORTS TAB ====================

class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(16)

        # Stats row
        stats_row = QHBoxLayout()
        self.stat_clips = self._make_stat("CLIPS EN BIBLIOTECA", "0")
        self.stat_data = self._make_stat("DATOS RESPALDADOS", "0 GB")
        self.stat_sessions = self._make_stat("SESIONES DE OFFLOAD", "0")
        stats_row.addWidget(self.stat_clips)
        stats_row.addWidget(self.stat_data)
        stats_row.addWidget(self.stat_sessions)
        v.addLayout(stats_row)

        # Recent sessions
        sessions_card = QFrame()
        sessions_card.setObjectName("card")
        sc_v = QVBoxLayout(sessions_card)
        sc_v.setContentsMargins(14, 12, 14, 12)
        title = QLabel("Sesiones de offload recientes")
        title.setStyleSheet("font-size: 13px; font-weight: 500;")
        sc_v.addWidget(title)

        self.sessions_table = QTableWidget(0, 5)
        self.sessions_table.setHorizontalHeaderLabels(["Fecha", "Origen", "Clips", "Datos", "Acciones"])
        self.sessions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.sessions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.sessions_table.setColumnWidth(4, 340)
        self.sessions_table.verticalHeader().setVisible(False)
        self.sessions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sessions_table.setShowGrid(False)
        sc_v.addWidget(self.sessions_table)
        v.addWidget(sessions_card, 1)

        # Refresh button
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh)
        v.addWidget(refresh, alignment=Qt.AlignRight)

    def _make_stat(self, label, value):
        card = QFrame()
        card.setObjectName("card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(14, 12, 14, 12)
        cv.setSpacing(4)
        l = QLabel(label)
        l.setObjectName("statLabel")
        v = QLabel(value)
        v.setObjectName("statValue")
        cv.addWidget(l)
        cv.addWidget(v)
        card.value_label = v
        return card

    def refresh(self):
        lib = load_library()
        total = sum(c.get('size_bytes', 0) for c in lib)
        self.stat_clips.value_label.setText(str(len(lib)))
        self.stat_data.value_label.setText(fmt_bytes(total))

        sessions = []
        if SESSIONS_FILE.exists():
            try:
                sessions = json.loads(SESSIONS_FILE.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                sessions = []

        self.stat_sessions.value_label.setText(str(len(sessions)))

        self.sessions_table.setRowCount(0)
        for s in reversed(sessions):
            r = self.sessions_table.rowCount()
            self.sessions_table.insertRow(r)
            date = s.get('date', '')[:19].replace('T', ' ')
            self.sessions_table.setItem(r, 0, QTableWidgetItem(date))
            self.sessions_table.setItem(r, 1, QTableWidgetItem(Path(s.get('source', '')).name or s.get('source', '')))
            self.sessions_table.setItem(r, 2, QTableWidgetItem(str(len(s.get('clips', [])))))
            data_size = sum(c.get('size_bytes', 0) for c in s.get('clips', []))
            self.sessions_table.setItem(r, 3, QTableWidgetItem(fmt_bytes(data_size)))

            # Actions widget
            actions = QWidget()
            ah = QHBoxLayout(actions)
            ah.setContentsMargins(4, 2, 4, 2)
            ah.setSpacing(4)
            for kind, label in [('csv', 'CSV'), ('mhl', 'MHL'), ('html', 'HTML')]:
                btn = QPushButton(label)
                btn.setFixedHeight(26)
                btn.clicked.connect(lambda _, k=kind, sess=s: self._export(sess, k))
                ah.addWidget(btn)
            self.sessions_table.setCellWidget(r, 4, actions)
            self.sessions_table.setRowHeight(r, 36)

    def _export(self, session, kind):
        try:
            downloads = Path.home() / 'Downloads'
            if not downloads.exists():
                downloads = Path.home()
            ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')

            if kind == 'csv':
                path = downloads / f'MediaStack_{ts}.csv'
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(['Name', 'Size (bytes)', 'Resolution', 'Codec', 'FPS',
                                'Duration (s)', 'Checksum', 'Method', 'Path'])
                    for c in session['clips']:
                        w.writerow([
                            c['name'], c['size_bytes'], c.get('resolution', ''),
                            c.get('codec', ''), c.get('fps', ''), c.get('duration', 0),
                            c['checksum'], c['checksum_method'], c['path']
                        ])

            elif kind == 'mhl':
                path = downloads / f'MediaStack_{ts}.mhl'
                lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                         '<hashlist version="1.1">',
                         '  <creatorinfo>',
                         '    <name>MediaStack</name>',
                         f'    <creationdate>{session["date"]}</creationdate>',
                         '  </creatorinfo>']
                for c in session['clips']:
                    name = c['name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    lines.append('  <hash>')
                    lines.append(f'    <file>{name}</file>')
                    lines.append(f'    <size>{c["size_bytes"]}</size>')
                    lines.append(f'    <{c["checksum_method"]}>{c["checksum"]}</{c["checksum_method"]}>')
                    lines.append('  </hash>')
                lines.append('</hashlist>')
                path.write_text('\n'.join(lines), encoding='utf-8')

            elif kind == 'html':
                path = downloads / f'MediaStack_{ts}.html'
                rows = []
                for c in session['clips']:
                    thumb_html = '—'
                    if c.get('thumbnail') and Path(c['thumbnail']).exists():
                        try:
                            with open(c['thumbnail'], 'rb') as tf:
                                b64 = base64.b64encode(tf.read()).decode('ascii')
                            thumb_html = f'<img src="data:image/jpeg;base64,{b64}" style="width:120px;border-radius:4px;display:block;">'
                        except Exception:
                            pass
                    rows.append(f'''
                    <tr>
                      <td>{thumb_html}</td>
                      <td><strong>{c["name"]}</strong><br><span style="color:#888;font-size:11px;">{c["path"]}</span></td>
                      <td>{c.get("resolution", "—")}</td>
                      <td>{c.get("codec", "—")}</td>
                      <td>{fmt_duration(c.get("duration", 0))}</td>
                      <td style="text-align:right;">{fmt_bytes(c["size_bytes"])}</td>
                      <td style="font-family:monospace;font-size:10px;">{c["checksum"]}</td>
                    </tr>''')

                html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>MediaStack Report</title>
<style>body{{font-family:-apple-system,system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#222}}
h1{{font-size:24px}}.sub{{color:#888;margin-bottom:24px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}}
.stat{{background:#f4f4f4;padding:14px;border-radius:8px}}.stat .l{{font-size:11px;color:#888;text-transform:uppercase}}
.stat .v{{font-size:22px;font-weight:600;margin-top:4px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#f4f4f4;text-align:left;padding:10px;font-size:11px;text-transform:uppercase;color:#666}}
td{{padding:10px;border-bottom:1px solid #eee;vertical-align:middle}}</style></head><body>
<h1>MediaStack Offload Report</h1><div class="sub">{session["date"]}</div>
<div class="stats">
<div class="stat"><div class="l">Clips</div><div class="v">{len(session["clips"])}</div></div>
<div class="stat"><div class="l">Total data</div><div class="v">{fmt_bytes(sum(c["size_bytes"] for c in session["clips"]))}</div></div>
<div class="stat"><div class="l">Destinations</div><div class="v">{len(session["destinations"])}</div></div>
<div class="stat"><div class="l">Checksum</div><div class="v">{session["checksum_method"].upper()}</div></div>
</div>
<h3>Origen</h3><p style="font-family:monospace;font-size:12px;">{session["source"]}</p>
<h3>Destinos</h3><ul>{"".join(f'<li style="font-family:monospace;font-size:12px;">{d}</li>' for d in session["destinations"])}</ul>
<h3>Clips</h3><table><thead><tr><th>Preview</th><th>Name</th><th>Resolution</th><th>Codec</th><th>Duration</th>
<th style="text-align:right;">Size</th><th>Checksum</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
</body></html>'''
                path.write_text(html, encoding='utf-8')

            QMessageBox.information(self, "Exportado",
                                    f"Reporte guardado en:\n{path}\n\nAbriendo carpeta...")
            if sys.platform == 'win32':
                subprocess.Popen(['explorer', '/select,', str(path)])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-R', str(path)])
            else:
                subprocess.Popen(['xdg-open', str(path.parent)])

        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))


# ==================== MAIN WINDOW ====================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(DARK_STYLE)
        self._build()

    def _build(self):
        # Header
        header = QWidget()
        header.setStyleSheet("background: #232323; border-bottom: 1px solid #353535;")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 10, 16, 10)

        # Brand
        brand = QHBoxLayout()
        icon = QLabel("M")
        icon.setFixedSize(28, 28)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background: #4a9eff; color: white; border-radius: 6px; font-weight: 600; font-size: 14px;")
        brand.addWidget(icon)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel(APP_NAME)
        title.setObjectName("brandTitle")
        sub = QLabel("Gestión de medios para producción audiovisual")
        sub.setObjectName("brandSub")
        brand_text.addWidget(title)
        brand_text.addWidget(sub)
        brand.addLayout(brand_text)
        h.addLayout(brand)
        h.addStretch()

        # Status
        if not FFMPEG:
            warn = QLabel("⚠ FFmpeg no detectado — sin thumbnails/metadata")
            warn.setStyleSheet("color: #fbbf24; font-size: 11px;")
            h.addWidget(warn)
        if not HAS_FAST_XXHASH:
            info = QLabel("ℹ Usando MD5 (xxhash no instalado)")
            info.setStyleSheet("color: #888; font-size: 11px; margin-left: 10px;")
            h.addWidget(info)

        # Tabs
        self.tabs = QTabWidget()
        self.browser = BrowserTab()
        self.offload = OffloadTab()
        self.reports = ReportsTab()

        self.tabs.addTab(self.browser, "Biblioteca")
        self.tabs.addTab(self.offload, "Offload")
        self.tabs.addTab(self.reports, "Reportes")

        # Wire signals: when offload adds a clip, refresh browser
        self.offload.clip_added.connect(self.browser.add_clip)
        self.tabs.currentChanged.connect(self._tab_changed)

        # Layout
        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(header)
        v.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        # Status bar
        sb = QStatusBar()
        sb.showMessage(f"Datos en: {APP_DATA}")
        self.setStatusBar(sb)

    def _tab_changed(self, idx):
        if idx == 0:
            self.browser.refresh()
        elif idx == 2:
            self.reports.refresh()


# ==================== ENTRY ====================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG)
    app.setStyle('Fusion')

    # Dark palette as a baseline (stylesheet overrides most of it but this helps with native widgets)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(26, 26, 26))
    palette.setColor(QPalette.WindowText, QColor(232, 232, 232))
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.Text, QColor(232, 232, 232))
    palette.setColor(QPalette.Button, QColor(42, 42, 42))
    palette.setColor(QPalette.ButtonText, QColor(232, 232, 232))
    palette.setColor(QPalette.Highlight, QColor(74, 158, 255))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
