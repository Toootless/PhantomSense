"""
PhantomSense Desktop Application
Real-time visualization of CSI data and LLM-calculated activity from both ESP32-S3 units
"""

import sys
import json
import asyncio
import os
from datetime import datetime
from collections import deque
from io import BytesIO

import requests

# Set matplotlib backend BEFORE importing pyplot
import matplotlib
matplotlib.use('Agg')
# Suppress warnings and increase figure limit
matplotlib.rcParams['figure.max_open_warning'] = 50
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QFrame, QGridLayout, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QColor, QPalette, QPixmap, QImage, QFont

# Load GUI configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'gui_config.json')
def load_gui_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load gui_config.json: {e}")
        return {}

GUI_CONFIG = load_gui_config()

# Configuration
HUB_URL = "http://localhost:5000"
UPDATE_INTERVAL = 500  # ms


class HubDataFetcher(QThread):
    """Background thread for fetching data from hub"""
    
    data_updated = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
    
    def run(self):
        while self.running:
            try:
                # Fetch device status
                response = requests.get(f"{HUB_URL}/devices", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.data_updated.emit(data)
                else:
                    self.error_occurred.emit(f"Hub returned {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.error_occurred.emit("Cannot connect to hub")
            except Exception as e:
                self.error_occurred.emit(str(e))
            
            self.msleep(UPDATE_INTERVAL)
    
    def stop(self):
        self.running = False


class UnitDataWidget(QWidget):
    """Widget to display data for a single ESP32 unit"""
    
    def __init__(self, unit_id, unit_name):
        super().__init__()
        self.unit_id = unit_id
        self.unit_name = unit_name
        self.csi_history = deque(maxlen=50)
        self.amplitude_history = deque(maxlen=50)
        self.noise_history = deque(maxlen=50)
        self._llm_timestamp = None  # datetime of last LLM analysis
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # ── helpers ────────────────────────────────────────────────────────
        def lbl(text, size=11, bold=False, color="#ffffff"):
            w = QLabel(text)
            f = QFont()
            f.setPointSize(size)
            if bold:
                f.setBold(True)
            w.setFont(f)
            w.setStyleSheet(f"color: {color};")
            return w

        def key_lbl(text):
            """Dim key label on the left."""
            return lbl(text, size=10, color="#7a8fa6")

        def val_lbl(text="—", color="#e8eaf0"):
            """Bright value label on the right, slightly larger."""
            w = lbl(text, size=11, bold=True, color=color)
            w.setStyleSheet(
                f"color: {color}; background-color: #1e2535; "
                f"border-radius: 4px; padding: 3px 8px;"
            )
            return w

        def section_title(text, color="#6bcf7f"):
            w = lbl(text, size=10, bold=True, color=color)
            w.setStyleSheet(
                f"color: {color}; background-color: #1a2030; "
                f"border-radius: 3px; padding: 4px 8px; letter-spacing: 1px;"
            )
            return w

        def add_row(grid, row, key, val_widget):
            k = key_lbl(key)
            k.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(k, row, 0)
            grid.addWidget(val_widget, row, 1)

        # ── Left panel ─────────────────────────────────────────────────────
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(8)

        # Unit title bar
        icon = "📶" if self.unit_id == "3" else "📡"
        title = lbl(f"{icon}  {self.unit_name}", size=12, bold=True, color="#6bcf7f")
        title.setWordWrap(True)
        title.setStyleSheet(
            "color: #6bcf7f; background-color: #1a2030; "
            "border-radius: 5px; padding: 6px 10px;"
        )
        left.addWidget(title)

        # ── Connection card ─────────────────────────────────────────────────
        conn_frame = QFrame()
        conn_frame.setStyleSheet(
            "QFrame { background-color: #1e2535; border: 1px solid #2d3a50; "
            "border-radius: 6px; }"
        )
        conn_layout = QVBoxLayout(conn_frame)
        conn_layout.setContentsMargins(10, 8, 10, 8)
        conn_layout.setSpacing(4)
        conn_layout.addWidget(section_title("CONNECTION"))

        conn_grid = QGridLayout()
        conn_grid.setContentsMargins(0, 4, 0, 0)
        conn_grid.setSpacing(6)
        conn_grid.setColumnStretch(1, 1)
        conn_grid.setColumnMinimumWidth(0, 65)

        self.status_label = val_lbl("🔴  Disconnected", color="#ff6b6b")
        self.ip_label     = val_lbl("N/A",              color="#a8e6cf")
        self.rssi_label   = val_lbl("N/A",              color="#a8e6cf")
        add_row(conn_grid, 0, "Status", self.status_label)
        add_row(conn_grid, 1, "IP",     self.ip_label)
        add_row(conn_grid, 2, "RSSI",   self.rssi_label)
        conn_layout.addLayout(conn_grid)
        left.addWidget(conn_frame)

        # ── Signal metrics card ─────────────────────────────────────────────
        sig_frame = QFrame()
        sig_frame.setStyleSheet(
            "QFrame { background-color: #1e2535; border: 1px solid #2d3a50; "
            "border-radius: 6px; }"
        )
        sig_layout = QVBoxLayout(sig_frame)
        sig_layout.setContentsMargins(10, 8, 10, 8)
        sig_layout.setSpacing(4)
        csi_title_text = "WIFI SIGNAL" if self.unit_id == "3" else "CSI METRICS"
        sig_layout.addWidget(section_title(csi_title_text, color="#ffd93d"))

        sig_grid = QGridLayout()
        sig_grid.setContentsMargins(0, 4, 0, 0)
        sig_grid.setSpacing(6)
        sig_grid.setColumnStretch(1, 1)
        sig_grid.setColumnMinimumWidth(0, 65)

        csi_key   = "Quality"  if self.unit_id == "3" else "Amplitude"
        noise_key = "Activity" if self.unit_id == "3" else "Noise"
        snr_key   = "Score"    if self.unit_id == "3" else "SNR"

        self.csi_mean_label    = val_lbl("—", color="#ffd93d")
        self.noise_floor_label = val_lbl("—", color="#ffd93d")
        self.snr_label         = val_lbl("—", color="#ffd93d")
        self.frame_count_label = val_lbl("0", color="#95e1d3")
        self.last_update_label = val_lbl("--:--:--", color="#95e1d3")

        add_row(sig_grid, 0, csi_key,    self.csi_mean_label)
        add_row(sig_grid, 1, noise_key,  self.noise_floor_label)
        add_row(sig_grid, 2, snr_key,    self.snr_label)
        add_row(sig_grid, 3, "Frames",   self.frame_count_label)
        add_row(sig_grid, 4, "Updated",  self.last_update_label)
        sig_layout.addLayout(sig_grid)
        left.addWidget(sig_frame)

        # ── LLM Analysis card ───────────────────────────────────────────────
        llm_frame = QFrame()
        llm_frame.setStyleSheet(
            "QFrame { background-color: #1e2535; border: 1px solid #2d3a50; "
            "border-radius: 6px; }"
        )
        llm_layout = QVBoxLayout(llm_frame)
        llm_layout.setContentsMargins(10, 8, 10, 8)
        llm_layout.setSpacing(5)
        llm_layout.addWidget(section_title("🤖 LLM ANALYSIS", color="#b39ddb"))

        self.llm_status_label = val_lbl("⏳  Waiting for data...", color="#95e1d3")
        self.llm_status_label.setStyleSheet(
            "color: #95e1d3; background-color: #151e2e; "
            "border-radius: 4px; padding: 4px 8px; font-weight: bold;"
        )
        llm_layout.addWidget(self.llm_status_label)

        self.llm_time_label = lbl("", size=9, color="#4a5a70")
        self.llm_time_label.setStyleSheet("color: #4a5a70; padding: 0px 2px;")
        llm_layout.addWidget(self.llm_time_label)

        # Activity name — first sentence only, word-wrapped
        self.activity_label = QLabel("—")
        af = QFont(); af.setPointSize(10); af.setBold(True)
        self.activity_label.setFont(af)
        self.activity_label.setStyleSheet(
            "color: #a8e6cf; background-color: #151e2e; "
            "border-radius: 4px; padding: 5px 8px;"
        )
        self.activity_label.setWordWrap(True)
        llm_layout.addWidget(self.activity_label)

        self.confidence_label = lbl("Confidence: N/A", size=10, color="#888888")
        self.confidence_label.setStyleSheet(
            "color: #888888; padding: 2px 4px;"
        )
        llm_layout.addWidget(self.confidence_label)

        # Reasoning snippet
        self.llm_reasoning_label = QLabel("")
        rf = QFont(); rf.setPointSize(9)
        self.llm_reasoning_label.setFont(rf)
        self.llm_reasoning_label.setStyleSheet(
            "color: #5a6a80; padding: 4px 6px; "
            "background-color: #151e2e; border-radius: 3px;"
        )
        self.llm_reasoning_label.setWordWrap(True)
        self.llm_reasoning_label.setMaximumHeight(66)
        llm_layout.addWidget(self.llm_reasoning_label)

        left.addWidget(llm_frame)
        left.addStretch()

        # ── Right: graph ────────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(6)

        graph_title_text = "📶  WiFi Signal Quality Trend" if self.unit_id == "3" else "📊  CSI Data Trend"
        gt = lbl(graph_title_text, size=11, bold=True, color="#6bcf7f")
        gt.setStyleSheet(
            "color: #6bcf7f; background-color: #1a2030; "
            "border-radius: 4px; padding: 5px 10px;"
        )
        right.addWidget(gt)

        self.graph_label = QLabel()
        self.graph_label.setStyleSheet(
            "background-color: #141922; border: 1px solid #2d3a50; border-radius: 4px;"
        )
        self.graph_label.setMinimumSize(300, 160)
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.graph_label, 1)

        # ── Assemble ────────────────────────────────────────────────────────
        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMinimumWidth(380)
        left_widget.setMaximumWidth(460)

        main_layout.addWidget(left_widget, 0)
        main_layout.addLayout(right, 1)
        self.setLayout(main_layout)

    
    def update_data(self, unit_data):
        """Update widget with data from hub"""
        if not unit_data:
            self.status_label.setText("🔴 Disconnected")
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            return
        
        # Status
        if unit_data.get("connected"):
            self.status_label.setText("🟢  Connected")
            self.status_label.setStyleSheet(
                "color: #6bcf7f; background-color: #1e2535; "
                "border-radius: 4px; padding: 3px 8px; font-weight: bold;"
            )
        else:
            self.status_label.setText("🔴  Disconnected")
            self.status_label.setStyleSheet(
                "color: #ff6b6b; background-color: #1e2535; "
                "border-radius: 4px; padding: 3px 8px; font-weight: bold;"
            )
        
        # Network info
        ip = unit_data.get("ip_address", "N/A")
        self.ip_label.setText(ip)
        
        rssi = unit_data.get("rssi", 0)
        self.rssi_label.setText(f"{rssi} dBm")
        
        # CSI data
        csi_data = unit_data.get("latest_csi", {})
        csi_mean = csi_data.get("amplitude_mean", 0)
        noise_floor = csi_data.get("noise_floor", 0)
        snr = round(csi_mean - noise_floor, 1)

        if self.unit_id == "3":
            self.csi_mean_label.setText(f"{csi_mean:.0f}%")
            self.noise_floor_label.setText("—")
            self.snr_label.setText(f"{int(snr)} / 100")
        else:
            self.csi_mean_label.setText(f"{csi_mean:.2f} dBm")
            self.noise_floor_label.setText(f"{noise_floor} dBm")
            self.snr_label.setText(f"{snr:.1f} dB")
        
        # Update counters
        frame_count = unit_data.get("frame_count", 0)
        self.frame_count_label.setText(str(frame_count))
        
        # Update timestamp
        self.last_update_label.setText(datetime.now().strftime("%H:%M:%S"))
        
        # Store in history for graphing
        # Unit 3 (Franklin WiFi) always appends since amplitude is quality % (can be 100.0)
        if self.unit_id == "3" or (csi_mean and noise_floor):
            self.amplitude_history.append(csi_mean)
            self.noise_history.append(noise_floor)
        
        # Activity analysis
        activity = unit_data.get("latest_activity", {})
        activity_name = activity.get("name", "—")
        confidence = activity.get("confidence", 0)

        # LLM status
        llm_status = unit_data.get("llm_status", "waiting")
        llm_ts_str = unit_data.get("llm_timestamp", "")
        llm_reasoning_text = unit_data.get("llm_reasoning", "")

        if llm_status == "processing":
            dots = "." * ((int(datetime.now().timestamp()) % 3) + 1)
            self.llm_status_label.setText(f"🔄  Analyzing{dots}")
            self.llm_status_label.setStyleSheet(
                "color: #ffd93d; background-color: #151e2e; "
                "border-radius: 4px; padding: 4px 8px; font-weight: bold;"
            )
        elif llm_status == "ready":
            self.llm_status_label.setText("✅  Analysis ready")
            self.llm_status_label.setStyleSheet(
                "color: #6bcf7f; background-color: #151e2e; "
                "border-radius: 4px; padding: 4px 8px; font-weight: bold;"
            )
        else:
            self.llm_status_label.setText("⏳  Waiting for data...")
            self.llm_status_label.setStyleSheet(
                "color: #95e1d3; background-color: #151e2e; "
                "border-radius: 4px; padding: 4px 8px; font-weight: bold;"
            )

        # Time since last analysis
        if llm_ts_str:
            try:
                self._llm_timestamp = datetime.fromisoformat(llm_ts_str)
            except Exception:
                self._llm_timestamp = None
        self._refresh_llm_time()

        # Activity: show only the first clean sentence from the LLM summary
        raw_name = activity_name.strip()
        # Strip leading markdown bold markers
        raw_name = raw_name.lstrip("*# ").strip()
        # Take up to the first sentence boundary
        for sep in ('. ', '! ', '\n', ':'):
            idx = raw_name.find(sep)
            if 0 < idx < 120:
                raw_name = raw_name[:idx + 1].strip()
                break
        self.activity_label.setText(raw_name[:120] if raw_name else "—")

        if confidence > 0:
            self.confidence_label.setText(f"Confidence: {confidence:.0%}")
            if confidence > 0.7:
                self.confidence_label.setStyleSheet("color: #6bcf7f; padding: 2px 4px;")
            elif confidence > 0.4:
                self.confidence_label.setStyleSheet("color: #ffd93d; padding: 2px 4px;")
            else:
                self.confidence_label.setStyleSheet("color: #ff6b6b; padding: 2px 4px;")
        else:
            self.confidence_label.setText("Confidence: N/A")
            self.confidence_label.setStyleSheet("color: #888888; padding: 2px 4px;")

        # Reasoning snippet
        if llm_reasoning_text:
            clean = llm_reasoning_text.replace('\n', ' ').strip()
            self.llm_reasoning_label.setText(clean[:280] + ("..." if len(clean) > 280 else ""))
        else:
            self.llm_reasoning_label.setText("")
        
        # Update graph
        self.update_graph()
    
    def _refresh_llm_time(self):
        """Update the 'last analysis X ago' label from cached timestamp."""
        if self._llm_timestamp:
            elapsed = int((datetime.now() - self._llm_timestamp).total_seconds())
            if elapsed < 60:
                self.llm_time_label.setText(f"Last analysis: {elapsed}s ago")
            else:
                self.llm_time_label.setText(f"Last analysis: {elapsed // 60}m ago")
        else:
            self.llm_time_label.setText("")

    def update_graph(self):
        """Update CSI trend graph and display as image with premium aesthetics"""
        try:
            # Close all previous figures to avoid memory leak
            plt.close('all')
            
            # Create a new matplotlib figure for rendering with high resolution
            fig = plt.figure(figsize=(4.8, 2.8), dpi=110, facecolor='#1a1a1a')
            ax1 = fig.add_subplot(111)
            
            # Style the background
            ax1.set_facecolor('#242424')
            ax1.grid(True, linestyle='--', alpha=0.25, color='#aaaaaa')
            
            # Plot data if available using twin axes for maximum visibility of variations
            if self.unit_id == "3":
                # Franklin WiFi: single-axis signal quality % trend
                if self.amplitude_history:
                    x_axis = list(range(len(self.amplitude_history)))
                    amp_list = list(self.amplitude_history)
                    min_amp = min(amp_list)
                    max_amp = max(amp_list)
                    pad_a = max(2.0, (max_amp - min_amp) * 0.3)
                    base_y = max(0.0, min_amp - pad_a)
                    top_y  = min(105.0, max_amp + pad_a)
                    line1 = ax1.plot(x_axis, amp_list, color='#95e1d3', marker='o',
                                     linewidth=2.5, markersize=4, label='Signal Quality', alpha=0.95)
                    ax1.fill_between(x_axis, amp_list, base_y, color='#95e1d3', alpha=0.15)
                    ax1.set_ylim(base_y, top_y)
                    ax1.legend(loc='lower left', fontsize=8, framealpha=0.9,
                               facecolor='#1e1e1e', edgecolor='#333333', labelcolor='#ffffff')
                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
                ax1.spines['bottom'].set_color('#333333')
                ax1.spines['left'].set_color('#95e1d3')
                ax1.set_xlabel('Sample History', color='#cccccc', fontsize=9)
                ax1.set_ylabel('Signal Quality (%)', color='#95e1d3', fontsize=9, fontweight='bold')
                ax1.tick_params(axis='x', colors='#cccccc', labelsize=8)
                ax1.tick_params(axis='y', colors='#95e1d3', labelsize=8)
            else:
                if self.amplitude_history and self.noise_history:
                    x_axis = list(range(len(self.amplitude_history)))
                    amp_list = list(self.amplitude_history)
                    noise_list = list(self.noise_history)

                    # Secondary axis for Noise Floor
                    ax2 = ax1.twinx()

                    # Plot Noise Floor on secondary axis
                    line2 = ax2.plot(x_axis, noise_list, color='#ff6b6b', marker='s',
                                     linewidth=1.5, markersize=3, label='Noise Floor', alpha=0.7)
                    ax2.set_ylabel('Noise (dBm)', color='#ff6b6b', fontsize=9, fontweight='bold')
                    ax2.tick_params(axis='y', colors='#ff6b6b', labelsize=8)

                    # Auto-scale Noise Floor axis with padding
                    min_noise = min(noise_list)
                    max_noise = max(noise_list)
                    if max_noise - min_noise < 5:
                        ax2.set_ylim(min_noise - 5, max_noise + 5)
                    else:
                        pad_n = (max_noise - min_noise) * 0.2
                        ax2.set_ylim(min_noise - pad_n, max_noise + pad_n)

                    # Plot CSI Amplitude on primary axis with fill gradient
                    line1 = ax1.plot(x_axis, amp_list, color='#00ffcc', marker='o',
                                     linewidth=2.5, markersize=4, label='CSI Amplitude', alpha=0.95)

                    # Add elegant filled area underneath the primary CSI curve
                    min_amp = min(amp_list)
                    max_amp = max(amp_list)
                    pad_a = max(2.0, (max_amp - min_amp) * 0.2)
                    base_y = min_amp - pad_a
                    ax1.fill_between(x_axis, amp_list, base_y, color='#00ffcc', alpha=0.15)

                    ax1.set_ylim(base_y, max_amp + pad_a)

                    # Combine legends beautifully
                    lines = line1 + line2
                    labels = [l.get_label() for l in lines]
                    ax1.legend(lines, labels, loc='upper left', fontsize=8, framealpha=0.9,
                               facecolor='#1e1e1e', edgecolor='#333333', labelcolor='#ffffff')

                    ax2.spines['top'].set_visible(False)
                    ax2.spines['bottom'].set_color('#333333')
                    ax2.spines['left'].set_color('#00ffcc')
                    ax2.spines['right'].set_color('#ff6b6b')
                else:
                    ax1.spines['top'].set_visible(False)
                    ax1.spines['right'].set_visible(False)
                    ax1.spines['bottom'].set_color('#333333')
                    ax1.spines['left'].set_color('#333333')

                ax1.set_xlabel('Sample History', color='#cccccc', fontsize=9)
                ax1.set_ylabel('CSI Amplitude (dBm)', color='#00ffcc', fontsize=9, fontweight='bold')
                ax1.tick_params(axis='x', colors='#cccccc', labelsize=8)
                ax1.tick_params(axis='y', colors='#00ffcc', labelsize=8)
            
            fig.tight_layout()
            
            # Render to PNG bytes
            buf = BytesIO()
            fig.savefig(buf, format='png', facecolor='#1a1a1a', edgecolor='none')
            buf.seek(0)
            
            # Convert to QPixmap and display
            image = QImage()
            image.loadFromData(buf.getvalue())
            
            # Scale pixmap to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(image)
            label_height = self.graph_label.height()
            label_width = self.graph_label.width()
            
            # Use sensible defaults if widget hasn't been rendered yet
            if label_height < 100:
                label_height = 200
            if label_width < 100:
                label_width = 300
            
            # Scale to fit available space
            max_height = label_height - 10
            max_width = label_width - 10
            
            if max_height > max_width:
                scaled_pixmap = pixmap.scaledToWidth(
                    max_width,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled_pixmap = pixmap.scaledToHeight(
                    max_height,
                    Qt.TransformationMode.SmoothTransformation
                )
            
            self.graph_label.setPixmap(scaled_pixmap)
            
            # Clean up figure and buffer
            buf.close()
            plt.close(fig)
        except Exception as e:
            self.graph_label.setText(f"Graph Error: {str(e)}")


class PhantomSenseApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        cfg = GUI_CONFIG.get('window', {})
        
        self.setWindowTitle(cfg.get('title', "PhantomSense - Real-time Data Monitor with LLM Analysis"))
        self.setGeometry(
            cfg.get('x', 50), 
            cfg.get('y', 50), 
            cfg.get('width', 1600), 
            cfg.get('height', 900)
        )
        self.setMinimumSize(
            cfg.get('min_width', 1000),
            cfg.get('min_height', 700)
        )
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1520;
            }
            QWidget {
                background-color: #0f1520;
                color: #e8eaf0;
            }
            QLabel {
                color: #e8eaf0;
            }
            QFrame {
                background-color: #1e2535;
                border: 1px solid #2d3a50;
            }
            QScrollArea {
                border: none;
            }
        """)
        
        # Data fetcher thread
        self.fetcher = HubDataFetcher()
        self.fetcher.data_updated.connect(self.on_hub_data)
        self.fetcher.error_occurred.connect(self.on_hub_error)
        self.fetcher.start()

        # Timer to refresh "X ago" labels every second
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick_llm_times)
        self._tick_timer.start(1000)
        
        # Setup UI
        self.setup_ui()
        self.show()
    
    def setup_ui(self):
        """Setup main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        cfg_layout = GUI_CONFIG.get('layout', {})
        margins = cfg_layout.get('margins', 12)
        spacing = cfg_layout.get('spacing', 12)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(margins, margins, margins, margins)
        main_layout.setSpacing(spacing)
        
        # Header
        header = QLabel("🌐  PhantomSense Hub — Multi-Unit Monitor")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet(
            "color: #6bcf7f; background-color: #1a2030; "
            "border-radius: 5px; padding: 8px 14px;"
        )
        main_layout.addWidget(header)
        
        # Hub status
        self.hub_status = QLabel("🔴  Connecting...")
        hub_status_font = QFont()
        hub_status_font.setPointSize(11)
        hub_status_font.setBold(True)
        self.hub_status.setFont(hub_status_font)
        self.hub_status.setStyleSheet(
            "color: #ff6b6b; padding: 6px 12px; "
            "background-color: #1a2030; border-radius: 4px;"
        )
        main_layout.addWidget(self.hub_status)
        
        # Units container
        units_layout = QVBoxLayout()
        units_layout.setContentsMargins(0, 0, 0, 0)
        units_layout.setSpacing(spacing)
        
        # Unit 1
        unit_min_height = cfg_layout.get('unit_min_height', 310)
        self.unit1_widget = UnitDataWidget("1", "Unit 1 - PhantomSense-Unit-1")
        self.unit1_widget.setMinimumHeight(unit_min_height)
        units_layout.addWidget(self.unit1_widget)
        
        # Separator
        separator = QFrame()
        separator.setStyleSheet("QFrame { background-color: #2d3a50; height: 1px; border: none; }")
        separator.setMaximumHeight(1)
        units_layout.addWidget(separator)

        # Unit 2
        self.unit2_widget = UnitDataWidget("2", "Unit 2 - PhantomSense-Unit-2")
        self.unit2_widget.setMinimumHeight(unit_min_height)
        units_layout.addWidget(self.unit2_widget)

        # Separator
        separator2 = QFrame()
        separator2.setStyleSheet("QFrame { background-color: #2d3a50; height: 1px; border: none; }")
        units_layout.addWidget(separator2)

        # Unit 3 - Franklin WiFi
        self.unit3_widget = UnitDataWidget("3", "Unit 3 - Franklin WiFi Sensor")
        self.unit3_widget.setMinimumHeight(unit_min_height)
        units_layout.addWidget(self.unit3_widget)

        units_layout.addStretch()

        # Wrap units in a scroll area so all 3 panels are reachable
        units_container = QWidget()
        units_container.setLayout(units_layout)
        scroll = QScrollArea()
        scroll.setWidget(units_container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background-color: #0f1520; }"
            "QScrollBar:vertical { background: #1a2030; width: 8px; border-radius: 4px; }"
            "QScrollBar::handle:vertical { background: #3a4a60; border-radius: 4px; min-height: 20px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )
        main_layout.addWidget(scroll, 1)
        
        # Footer stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            "QFrame { background-color: #1a2030; border-radius: 4px; "
            "border: 1px solid #2d3a50; padding: 4px; }"
        )
        stats_frame.setMaximumHeight(50)
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(5, 5, 5, 5)
        
        self.stats_label = QLabel("Waiting for data...")
        stats_font = QFont()
        stats_font.setPointSize(11)
        self.stats_label.setFont(stats_font)
        self.stats_label.setStyleSheet("color: #a8c0d0; padding: 4px 8px;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        stats_frame.setLayout(stats_layout)
        main_layout.addWidget(stats_frame)
        
        central_widget.setLayout(main_layout)
    
    def _tick_llm_times(self):
        """Refresh 'last analysis X ago' labels every second."""
        self.unit1_widget._refresh_llm_time()
        self.unit2_widget._refresh_llm_time()
        self.unit3_widget._refresh_llm_time()

    def on_hub_data(self, data):
        """Handle data from hub"""
        # Update hub status
        self.hub_status.setText("🟢  Hub Connected")
        self.hub_status.setStyleSheet(
            "color: #6bcf7f; padding: 6px 12px; "
            "background-color: #1a2030; border-radius: 4px; font-weight: bold;"
        )
        
        # Extract unit data
        units = data.get("units", {})
        
        # Update Unit 1 (hub stores as string key "1" or "unit1")
        unit1_data = units.get("1") or units.get("unit1")
        self.unit1_widget.update_data(unit1_data)
        
        # Update Unit 2 (hub stores as string key "2" or "unit2")
        unit2_data = units.get("2") or units.get("unit2")
        self.unit2_widget.update_data(unit2_data)

        # Update Unit 3 - Franklin WiFi sensor
        unit3_data = units.get("3") or units.get("unit3")
        self.unit3_widget.update_data(unit3_data)
        
        # Update stats — sum frame/activity counts from each unit (no top-level field in API)
        total_frames = sum(u.get("frame_count", 0) for u in units.values())
        total_activities = sum(u.get("activity_count", 0) for u in units.values())
        connected = len([u for u in units.values() if u.get('connected')])
        total = len(units)
        self.stats_label.setText(
            f"📊 Total Frames: {total_frames} | Total Activities: {total_activities} | "
            f"Connected Units: {connected}/{total}"
        )
    
    def on_hub_error(self, error_msg):
        """Handle errors from hub"""
        self.hub_status.setText(f"🔴  Error: {error_msg}")
        self.hub_status.setStyleSheet(
            "color: #ff6b6b; padding: 6px 12px; "
            "background-color: #1a2030; border-radius: 4px;"
        )
    
    def closeEvent(self, event):
        """Cleanup on close"""
        self.fetcher.stop()
        self.fetcher.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = PhantomSenseApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
