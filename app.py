import collections
import os
import sys
import time

import psutil
from PyQt6 import QtCore, QtGui, QtWidgets

# Safe NVIDIA NVML initialization
NVML_AVAILABLE = False
try:
    import pynvml

    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except Exception:
    NVML_AVAILABLE = False


def get_asset_path(filename):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


THEMES = {
    "Dark": {
        "bg": "#09090b",
        "card_bg": "#121215",
        "card_border": "#222227",
        "canvas_bg": "#0a0a0d",
        "grid_line": "#191922",
        "text_main": "#f8fafc",
        "text_title": "#f1f5f9",
        "text_sub": "#94a3b8",
        "btn_bg": "#18181b",
        "btn_hover": "#27272a",
    },
    "OLED Black": {
        "bg": "#000000",
        "card_bg": "#0a0a0a",
        "card_border": "#1a1a1a",
        "canvas_bg": "#000000",
        "grid_line": "#141414",
        "text_main": "#ffffff",
        "text_title": "#f5f5f5",
        "text_sub": "#a3a3a3",
        "btn_bg": "#121212",
        "btn_hover": "#222222",
    },
    "Light": {
        "bg": "#f4f4f5",
        "card_bg": "#ffffff",
        "card_border": "#e4e4e7",
        "canvas_bg": "#f8fafc",
        "grid_line": "#e2e8f0",
        "text_main": "#09090b",
        "text_title": "#1e293b",
        "text_sub": "#64748b",
        "btn_bg": "#e4e4e7",
        "btn_hover": "#d4d4d8",
    },
}


class AccurateWaveGraph(QtWidgets.QWidget):
    """
    Sub-pixel antialiased graph that keeps percentages on a true 0-100% scale
    and bounds process counts against a standard 1,000 PID ceiling.
    """

    def __init__(
        self,
        color_hex="#38bdf8",
        is_percentage=True,
        max_points=40,
        theme="Dark",
        parent=None,
    ):
        super().__init__(parent)
        self.color_hex = color_hex
        self.is_percentage = is_percentage
        self.theme = theme
        self.max_points = max_points
        self.history = collections.deque(maxlen=max_points)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.setMinimumHeight(80)

    def set_theme(self, theme_name):
        self.theme = theme_name
        self.update()

    def add_point(self, val):
        val = float(val)
        if len(self.history) == 0:
            for _ in range(self.max_points):
                self.history.append(val)
        else:
            self.history.append(val)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        if w < 10 or h < 10 or len(self.history) < 2:
            return

        t = THEMES[self.theme]

        # Background Plate
        plate = QtGui.QPainterPath()
        plate.addRoundedRect(0.0, 0.0, float(w), float(h), 8.0, 8.0)
        painter.fillPath(plate, QtGui.QColor(t["canvas_bg"]))

        # Grid lines
        pen_grid = QtGui.QPen(
            QtGui.QColor(t["grid_line"]), 1, QtCore.Qt.PenStyle.DashLine
        )
        painter.setPen(pen_grid)
        for ratio in [0.25, 0.50, 0.75]:
            gy = int(h * ratio)
            painter.drawLine(8, gy, w - 8, gy)

        pts = list(self.history)
        n = len(pts)

        # Scale determination
        if self.is_percentage:
            y_max = 100.0
        else:
            peak = max(pts)
            if peak > 50:
                # Kernel Concurrency grounded to 1,000 PIDs minimum
                y_max = max(peak * 1.4, 1000.0)
            else:
                # Network auto-scaling
                y_max = max(peak * 1.4, 1.0)

        pad_x = 8.0
        pad_y = 8.0
        draw_h = max(h - (pad_y * 2), 1)
        dx = (w - (pad_x * 2)) / (n - 1)

        curve_path = QtGui.QPainterPath()
        first_val = max(0.0, min(y_max, pts[0]))
        first_y = (h - pad_y) - (first_val / y_max) * draw_h
        curve_path.moveTo(pad_x, first_y)

        coords = [(pad_x, first_y)]
        for i in range(1, n):
            val = max(0.0, min(y_max, pts[i]))
            x = pad_x + (i * dx)
            y = (h - pad_y) - (val / y_max) * draw_h
            coords.append((x, y))

            prev_x, prev_y = coords[i - 1]
            c1_x = (prev_x + x) / 2
            c1_y = prev_y
            c2_x = (prev_x + x) / 2
            c2_y = y
            curve_path.cubicTo(c1_x, c1_y, c2_x, c2_y, x, y)

        # Gradient area fill
        fill_path = QtGui.QPainterPath(curve_path)
        fill_path.lineTo(w - pad_x, h - pad_y)
        fill_path.lineTo(pad_x, h - pad_y)
        fill_path.closeSubpath()

        grad = QtGui.QLinearGradient(0, 0, 0, h)
        primary = QtGui.QColor(self.color_hex)
        grad.setColorAt(
            0.0, QtGui.QColor(primary.red(), primary.green(), primary.blue(), 70)
        )
        grad.setColorAt(
            1.0, QtGui.QColor(primary.red(), primary.green(), primary.blue(), 0)
        )
        painter.fillPath(fill_path, grad)

        # Trendline stroke
        pen_line = QtGui.QPen(primary, 2.2)
        pen_line.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_line)
        painter.drawPath(curve_path)

        # Head indicator dot
        last_x, last_y = coords[-1]
        painter.setBrush(primary)
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 1.8))
        painter.drawEllipse(QtCore.QPointF(last_x, last_y), 4.0, 4.0)


class MetricCard(QtWidgets.QFrame):
    """Proportional telemetry card widget with strict typographic hierarchy."""

    def __init__(
        self, title, color_hex="#38bdf8", is_percentage=True, theme="Dark", parent=None
    ):
        super().__init__(parent)
        self.color_hex = color_hex
        self.current_theme = theme
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.setMinimumSize(280, 150)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(4)

        top_row = QtWidgets.QHBoxLayout()
        self.lbl_title = QtWidgets.QLabel(title)
        self.lbl_value = QtWidgets.QLabel("0%")

        top_row.addWidget(self.lbl_title)
        top_row.addStretch()
        top_row.addWidget(self.lbl_value)
        self.layout.addLayout(top_row)

        self.lbl_sub = QtWidgets.QLabel("Initializing...")
        self.layout.addWidget(self.lbl_sub)
        self.layout.addSpacing(4)

        self.graph = AccurateWaveGraph(
            color_hex=color_hex, is_percentage=is_percentage, theme=theme
        )
        self.layout.addWidget(self.graph)

        self.apply_theme(theme, base_font_size=11)

    def apply_theme(self, theme_name, base_font_size=11):
        self.current_theme = theme_name
        t = THEMES[theme_name]

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t["card_bg"]};
                border: 1px solid {t["card_border"]};
                border-radius: 12px;
            }}
        """)
        # 1. Main title: Clear, prominent, and distinct from the subtitles
        self.lbl_title.setStyleSheet(f"""
            border: none; 
            color: {t["text_title"]}; 
            font-size: {base_font_size + 2}px; 
            font-weight: 700; 
            letter-spacing: 0.6px;
        """)
        # 2. Main value metric
        self.lbl_value.setStyleSheet(f"""
            border: none; 
            color: {t["text_main"]}; 
            font-size: {base_font_size + 14}px; 
            font-weight: 800;
        """)
        # 3. Subtitles: Noticeably smaller and muted to create proper visual depth
        self.lbl_sub.setStyleSheet(f"""
            border: none; 
            color: {t["text_sub"]}; 
            font-size: {max(base_font_size - 1, 9)}px; 
            font-weight: 500;
        """)
        self.graph.set_theme(theme_name)

    def update_data(self, val, val_str, sub_str):
        self.lbl_value.setText(val_str)
        self.lbl_sub.setText(sub_str)
        self.graph.add_point(val)


class SimpleSettingsDialog(QtWidgets.QDialog):
    """Settings modal dialog with refresh rate options."""

    settings_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(380, 270)
        self.setModal(True)

        self.settings = QtCore.QSettings("PulseTelemetry", "PulseTelemetry")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_app = QtWidgets.QLabel("TELEMETRY SETTINGS")
        lbl_app.setStyleSheet("font-weight: 800; font-size: 11px; color: #818cf8;")
        layout.addWidget(lbl_app)

        form = QtWidgets.QFormLayout()
        form.setSpacing(12)

        # 1. Theme
        self.combo_theme = QtWidgets.QComboBox()
        self.combo_theme.addItems(["Dark", "OLED Black", "Light"])
        self.combo_theme.setCurrentText(self.settings.value("theme", "Dark"))
        form.addRow("Theme:", self.combo_theme)

        # 2. Font Slider
        self.slider_font = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider_font.setRange(10, 18)
        self.slider_font.setValue(int(self.settings.value("font_size", 12)))
        self.lbl_font_val = QtWidgets.QLabel(f"{self.slider_font.value()} pt")
        self.slider_font.valueChanged.connect(
            lambda v: self.lbl_font_val.setText(f"{v} pt")
        )

        font_row = QtWidgets.QHBoxLayout()
        font_row.addWidget(self.slider_font)
        font_row.addWidget(self.lbl_font_val)
        form.addRow("Font Scale:", font_row)

        # 3. Refresh Rate Selector
        self.combo_refresh = QtWidgets.QComboBox()
        self.combo_refresh.addItems(
            ["0.5s (High Speed)", "1.0s (Normal)", "2.0s (Battery Saver)"]
        )
        stored_refresh = self.settings.value("refresh_rate", "1.0s (Normal)")
        self.combo_refresh.setCurrentText(stored_refresh)
        form.addRow("Refresh Rate:", self.combo_refresh)

        layout.addLayout(form)
        layout.addStretch()

        btn_box = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("Apply")
        btn_save.setStyleSheet("""
            background-color: #3b82f6; color: #ffffff; font-weight: 700;
            padding: 8px 20px; border-radius: 6px;
        """)
        btn_save.clicked.connect(self.save_settings)

        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def save_settings(self):
        self.settings.setValue("theme", self.combo_theme.currentText())
        self.settings.setValue("font_size", self.slider_font.value())
        self.settings.setValue("refresh_rate", self.combo_refresh.currentText())
        self.settings_changed.emit()
        self.accept()


class PulseMonitorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.cached_gpu_name = None
        self.cached_vram_total = 0.0
        self.setWindowTitle("Pulse Telemetry")
        # Set Window and Taskbar Icon
        icon_path = get_asset_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        self.resize(1000, 700)
        self.setMinimumSize(850, 600)

        self.settings = QtCore.QSettings("PulseTelemetry", "PulseTelemetry")
        self._load_local_fonts()

        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()

        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)
        self.root_layout = QtWidgets.QVBoxLayout(self.central)
        self.root_layout.setContentsMargins(18, 14, 18, 14)
        self.root_layout.setSpacing(12)

        self._build_header()

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(12)
        self.root_layout.addLayout(self.grid)

        self.card_cpu = MetricCard(
            "CPU UTILIZATION", color_hex="#38bdf8", is_percentage=True
        )
        self.card_ram = MetricCard(
            "PHYSICAL MEMORY (RAM)", color_hex="#818cf8", is_percentage=True
        )
        self.card_gpu = MetricCard(
            "NVIDIA GPU CORE", color_hex="#4ade80", is_percentage=True
        )
        self.card_vram = MetricCard(
            "NVIDIA GPU MEMORY (VRAM)", color_hex="#22c55e", is_percentage=True
        )
        self.card_proc = MetricCard(
            "KERNEL CONCURRENCY", color_hex="#f472b6", is_percentage=False
        )
        self.card_net = MetricCard(
            "NETWORK BANDWIDTH", color_hex="#fbbf24", is_percentage=False
        )

        self.cards_list = [
            self.card_cpu,
            self.card_ram,
            self.card_gpu,
            self.card_vram,
            self.card_proc,
            self.card_net,
        ]

        # Row 0: CPU & RAM
        self.grid.addWidget(self.card_cpu, 0, 0)
        self.grid.addWidget(self.card_ram, 0, 1)

        # Row 1: GPU Core & GPU Memory
        self.grid.addWidget(self.card_gpu, 1, 0)
        self.grid.addWidget(self.card_vram, 1, 1)

        # Row 2: Concurrency & Network Bandwidth
        self.grid.addWidget(self.card_proc, 2, 0)
        self.grid.addWidget(self.card_net, 2, 1)

        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 1)
        self.grid.setRowStretch(2, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)

        self.apply_stored_configuration()

    def _load_local_fonts(self):
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        font_dir = os.path.join(base_dir, "Open_Sans", "static")
        loaded_family = None
        if os.path.exists(font_dir):
            for ttf in os.listdir(font_dir):
                if ttf.lower().endswith(".ttf"):
                    font_id = QtGui.QFontDatabase.addApplicationFont(
                        os.path.join(font_dir, ttf)
                    )
                    if font_id != -1 and not loaded_family:
                        families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
                        if families:
                            loaded_family = families[0]

        self.font_family = loaded_family if loaded_family else "Ubuntu"

    def _build_header(self):
        self.header = QtWidgets.QHBoxLayout()
        title_box = QtWidgets.QHBoxLayout()
        title_box.setSpacing(10)

        self.title = QtWidgets.QLabel("Pulse Telemetry")
        title_box.addWidget(self.title)

        self.badge = QtWidgets.QLabel("LIVE")
        self.badge.setStyleSheet("""
            background-color: #064e3b; color: #10b981;
            font-size: 10px; font-weight: 800;
            padding: 3px 8px; border-radius: 5px;
        """)
        title_box.addWidget(self.badge)
        self.header.addLayout(title_box)
        self.header.addStretch()

        self.btn_settings = QtWidgets.QPushButton("⚙")
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        self.header.addWidget(self.btn_settings)

        self.root_layout.addLayout(self.header)

    def open_settings(self):
        dialog = SimpleSettingsDialog(self)
        dialog.settings_changed.connect(self.apply_stored_configuration)
        dialog.exec()

    def apply_stored_configuration(self):
        theme_name = self.settings.value("theme", "Dark")
        font_size = int(self.settings.value("font_size", 12))
        refresh_str = self.settings.value("refresh_rate", "1.0s (Normal)")
        t = THEMES[theme_name]

        app_font = QtGui.QFont(self.font_family, font_size)
        app_font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
        QtWidgets.QApplication.setFont(app_font)

        self.setStyleSheet(f"QMainWindow {{ background-color: {t['bg']}; }}")
        self.title.setStyleSheet(
            f"color: {t['text_main']}; font-size: {font_size + 8}px; font-weight: 800; letter-spacing: 0.6px;"
        )
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background-color: {t["btn_bg"]}; color: {t["text_main"]};
                border: 1px solid {t["card_border"]}; border-radius: 16px;
                font-size: {font_size + 4}px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {t["btn_hover"]}; }}
        """)

        for card in self.cards_list:
            card.apply_theme(theme_name, base_font_size=font_size)

        if "0.5s" in refresh_str:
            interval_ms = 500
        elif "2.0s" in refresh_str:
            interval_ms = 2000
        else:
            interval_ms = 1000

        self.timer.stop()
        self.timer.start(interval_ms)

    def update_telemetry(self):
        # 1. CPU
        cpu = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
        cores = psutil.cpu_count(logical=True)
        self.card_cpu.update_data(
            cpu, f"{cpu:.1f}%", f"{cores} Logical Cores • {freq_str}"
        )

        # 2. RAM
        ram = psutil.virtual_memory()
        used_gb = ram.used / (1024**3)
        total_gb = ram.total / (1024**3)
        self.card_ram.update_data(
            ram.percent,
            f"{used_gb:.1f} GB ({ram.percent:.0f}%)",
            f"Active: {used_gb:.2f} GB of {total_gb:.2f} GB Total",
        )

        # 3 & 4. GPU NVML
        gpu_stats = {
            "active": False,
            "standby": False,
            "name": "NVIDIA Offline",
            "load": 0.0,
            "vram_pct": 0.0,
            "vram_used": 0.0,
            "vram_total": 0.0,
            "temp": None,
            "power": 0.0,
        }

        if NVML_AVAILABLE:
            try:
                if pynvml.nvmlDeviceGetCount() > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)

                    # Cache name and total VRAM once so sleep states don't clear them
                    if not self.cached_gpu_name:
                        raw_name = pynvml.nvmlDeviceGetName(handle)
                        self.cached_gpu_name = (
                            raw_name.decode("utf-8")
                            if isinstance(raw_name, bytes)
                            else str(raw_name)
                        )
                        try:
                            mem_init = pynvml.nvmlDeviceGetMemoryInfo(handle)
                            self.cached_vram_total = mem_init.total / (1024**3)
                        except Exception:
                            self.cached_vram_total = 4.0  # Fallback for GTX 1050 Ti

                    gpu_stats["active"] = True
                    gpu_stats["name"] = self.cached_gpu_name
                    gpu_stats["vram_total"] = self.cached_vram_total

                    # Read real-time telemetry (fails when GPU enters D3Cold sleep)
                    try:
                        rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        temp = pynvml.nvmlDeviceGetTemperature(
                            handle, pynvml.NVML_TEMPERATURE_GPU
                        )
                        try:
                            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                        except Exception:
                            power = 0.0

                        gpu_stats["load"] = float(rates.gpu)
                        gpu_stats["vram_pct"] = (mem.used / mem.total) * 100
                        gpu_stats["vram_used"] = mem.used / (1024**3)
                        gpu_stats["temp"] = temp
                        gpu_stats["power"] = power
                        gpu_stats["standby"] = False
                    except Exception:
                        # GPU is in D3Cold sleep mode: keep active, zero out telemetry
                        gpu_stats["standby"] = True
                        gpu_stats["load"] = 0.0
                        gpu_stats["vram_pct"] = 0.0
                        gpu_stats["vram_used"] = 0.0

            except Exception:
                gpu_stats["active"] = False

        if gpu_stats["active"]:
            if gpu_stats["standby"]:
                # Card is asleep in power-save mode
                self.card_gpu.update_data(0.0, "0%", f"{gpu_stats['name']} • Standby")
                self.card_vram.update_data(
                    0.0,
                    "0.00 GB (0%)",
                    f"Dedicated VRAM: 0.00 of {gpu_stats['vram_total']:.2f} GB",
                )
            else:
                # Card is actively running workloads
                temp_str = (
                    f"{gpu_stats['temp']}°C"
                    if gpu_stats["temp"] is not None
                    else "--°C"
                )
                self.card_gpu.update_data(
                    gpu_stats["load"],
                    f"{gpu_stats['load']:.0f}%",
                    f"{gpu_stats['name']} • {temp_str} • {gpu_stats['power']:.1f}W",
                )
                self.card_vram.update_data(
                    gpu_stats["vram_pct"],
                    f"{gpu_stats['vram_used']:.2f} GB ({gpu_stats['vram_pct']:.0f}%)",
                    f"Dedicated VRAM: {gpu_stats['vram_used']:.2f} of {gpu_stats['vram_total']:.2f} GB",
                )
        else:
            self.card_gpu.update_data(0, "OFFLINE", "No NVIDIA GPU detected")
            self.card_vram.update_data(0, "OFFLINE", "VRAM telemetry unlinked")

        # 5. Kernel Concurrency
        proc_count = len(psutil.pids())
        thread_count = 0
        try:
            for p in psutil.process_iter(["num_threads"]):
                thread_count += p.info.get("num_threads") or 0
        except Exception:
            pass
        self.card_proc.update_data(
            proc_count, f"{proc_count} PIDs", f"{thread_count:,} Active Kernel Threads"
        )

        # 6. Network Bandwidth
        curr_net = psutil.net_io_counters()
        now = time.time()
        elapsed = max(now - self.prev_time, 1e-6)
        down_mbps = (
            ((curr_net.bytes_recv - self.prev_net.bytes_recv) * 8) / (1024**2) / elapsed
        )
        up_mbps = (
            ((curr_net.bytes_sent - self.prev_net.bytes_sent) * 8) / (1024**2) / elapsed
        )
        self.prev_net = curr_net
        self.prev_time = now
        total_net = down_mbps + up_mbps
        self.card_net.update_data(
            total_net,
            f"↓{down_mbps:.2f} ↑{up_mbps:.2f} MB/s",
            f"Bandwidth: {total_net:.2f} Mbps",
        )

    def closeEvent(self, event):
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
        super().closeEvent(event)


if __name__ == "__main__":
    # 1. Enforce portal environment variable directly before any Qt modules load
    if sys.platform.startswith("linux"):
        os.environ["QT_NO_PORTAL"] = "1"

    # 2. Fix Windows taskbar grouping
    if sys.platform.startswith("win"):
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "pulse.telemetry.app.1.0"
        )

    # 3. Set desktop file name BEFORE QApplication instance creation
    #    (QGuiApplication.setDesktopFileName is static in Qt 6)
    if sys.platform.startswith("linux"):
        QtGui.QGuiApplication.setDesktopFileName("pulse-telemetry")

    # 4. Initialize QApplication
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("pulse-telemetry")

    # 5. Set global application icon
    icon_path = get_asset_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))

    window = PulseMonitorApp()
    window.show()
    sys.exit(app.exec())