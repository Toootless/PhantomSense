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
        cfg_layout = GUI_CONFIG.get('layout', {})
        left_min = cfg_layout.get('left_panel_min_width', 180)
        left_max = cfg_layout.get('left_panel_max_width', 250)
        spacing = cfg_layout.get('spacing', 10)
        margins = cfg_layout.get('margins', 8)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(margins, margins, margins, margins)
        main_layout.setSpacing(spacing)
        
        # Left side: Data panel
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Helper function to create consistent label fonts
        def create_label_font(size=10, bold=False):
            font = QFont()
            font.setPointSize(size)
            if bold:
                font.setBold(True)
            return font
        
        # Title
        icon = "📶" if self.unit_id == "3" else "📡"
        title_label = QLabel(f"{icon} {self.unit_name}")
        title_label.setFont(create_label_font(12, bold=True))
        title_label.setStyleSheet("color: #6bcf7f; padding: 4px;")
        left_layout.addWidget(title_label)
        
        # Status frame
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 4px; padding: 10px; }")
        status_layout = QGridLayout()
        status_layout.setSpacing(10)
        status_layout.setContentsMargins(10, 10, 10, 10)
        status_layout.setRowMinimumHeight(0, 25)
        status_layout.setRowMinimumHeight(1, 25)
        status_layout.setRowMinimumHeight(2, 25)
        
        status_label_title = QLabel("Status:")
        status_label_title.setFont(create_label_font(10))
        status_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        status_label_title.setMinimumWidth(50)
        self.status_label = QLabel("🔴 Disconnected")
        self.status_label.setFont(create_label_font(10, bold=True))
        self.status_label.setStyleSheet("color: #ff6b6b; padding: 2px;")
        self.status_label.setMinimumWidth(120)
        status_layout.addWidget(status_label_title, 0, 0)
        status_layout.addWidget(self.status_label, 0, 1)
        
        ip_label_title = QLabel("IP:")
        ip_label_title.setFont(create_label_font(10))
        ip_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        ip_label_title.setMinimumWidth(50)
        self.ip_label = QLabel("N/A")
        self.ip_label.setFont(create_label_font(10))
        self.ip_label.setStyleSheet("color: #a8e6cf; padding: 2px;")
        self.ip_label.setMinimumWidth(120)
        status_layout.addWidget(ip_label_title, 1, 0)
        status_layout.addWidget(self.ip_label, 1, 1)
        
        rssi_label_title = QLabel("WiFi:")
        rssi_label_title.setFont(create_label_font(10))
        rssi_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        rssi_label_title.setMinimumWidth(50)
        self.rssi_label = QLabel("N/A")
        self.rssi_label.setFont(create_label_font(10))
        self.rssi_label.setStyleSheet("color: #a8e6cf; padding: 2px;")
        self.rssi_label.setMinimumWidth(120)
        status_layout.addWidget(rssi_label_title, 2, 0)
        status_layout.addWidget(self.rssi_label, 2, 1)
        
        status_frame.setLayout(status_layout)
        status_frame.setMinimumHeight(100)
        left_layout.addWidget(status_frame)
        
        # Data metrics frame
        data_frame = QFrame()
        data_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 4px; padding: 10px; }")
        data_frame.setMinimumHeight(160)
        data_layout = QGridLayout()
        data_layout.setSpacing(10)
        data_layout.setContentsMargins(10, 10, 10, 10)
        data_layout.setRowMinimumHeight(0, 22)
        data_layout.setRowMinimumHeight(1, 22)
        data_layout.setRowMinimumHeight(2, 22)
        data_layout.setRowMinimumHeight(3, 22)
        data_layout.setRowMinimumHeight(4, 22)
        
        csi_label_text = "Signal:" if self.unit_id == "3" else "CSI Amp:"
        csi_label_title = QLabel(csi_label_text)
        csi_label_title.setFont(create_label_font(10))
        csi_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        csi_label_title.setMinimumWidth(70)
        self.csi_mean_label = QLabel("0.0")
        self.csi_mean_label.setFont(create_label_font(10))
        self.csi_mean_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        self.csi_mean_label.setMinimumWidth(90)
        data_layout.addWidget(csi_label_title, 0, 0)
        data_layout.addWidget(self.csi_mean_label, 0, 1)
        
        noise_label_text = "Baseline:" if self.unit_id == "3" else "Noise:"
        noise_label_title = QLabel(noise_label_text)
        noise_label_title.setFont(create_label_font(10))
        noise_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        noise_label_title.setMinimumWidth(70)
        self.noise_floor_label = QLabel("0")
        self.noise_floor_label.setFont(create_label_font(10))
        self.noise_floor_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        self.noise_floor_label.setMinimumWidth(90)
        data_layout.addWidget(noise_label_title, 1, 0)
        data_layout.addWidget(self.noise_floor_label, 1, 1)
        
        snr_label_text = "Activity:" if self.unit_id == "3" else "SNR:"
        snr_label_title = QLabel(snr_label_text)
        snr_label_title.setFont(create_label_font(10))
        snr_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        snr_label_title.setMinimumWidth(70)
        self.snr_label = QLabel("0.0")
        self.snr_label.setFont(create_label_font(10))
        self.snr_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        self.snr_label.setMinimumWidth(90)
        data_layout.addWidget(snr_label_title, 2, 0)
        data_layout.addWidget(self.snr_label, 2, 1)
        
        frame_label_title = QLabel("Frames:")
        frame_label_title.setFont(create_label_font(10))
        frame_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        frame_label_title.setMinimumWidth(70)
        self.frame_count_label = QLabel("0")
        self.frame_count_label.setFont(create_label_font(10))
        self.frame_count_label.setStyleSheet("color: #95e1d3; padding: 2px;")
        self.frame_count_label.setMinimumWidth(90)
        data_layout.addWidget(frame_label_title, 3, 0)
        data_layout.addWidget(self.frame_count_label, 3, 1)
        
        update_label_title = QLabel("Updated:")
        update_label_title.setFont(create_label_font(10))
        update_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        update_label_title.setMinimumWidth(70)
        self.last_update_label = QLabel("--:--:--")
        self.last_update_label.setFont(create_label_font(10))
        self.last_update_label.setStyleSheet("color: #95e1d3; padding: 2px;")
        self.last_update_label.setMinimumWidth(90)
        data_layout.addWidget(update_label_title, 4, 0)
        data_layout.addWidget(self.last_update_label, 4, 1)
        
        data_frame.setLayout(data_layout)
        left_layout.addWidget(data_frame)
        
        # LLM Analysis frame
        llm_frame = QFrame()
        llm_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 4px; padding: 10px; }")
        llm_layout = QVBoxLayout()
        llm_layout.setSpacing(5)
        llm_layout.setContentsMargins(10, 10, 10, 10)

        llm_title = QLabel("🤖 LLM Analysis")
        llm_title.setFont(create_label_font(11, bold=True))
        llm_title.setStyleSheet("color: #6bcf7f; padding: 4px;")
        llm_layout.addWidget(llm_title)

        self.llm_status_label = QLabel("⏳ Waiting for data...")
        self.llm_status_label.setFont(create_label_font(10, bold=True))
        self.llm_status_label.setStyleSheet("color: #95e1d3; padding: 2px;")
        llm_layout.addWidget(self.llm_status_label)

        self.llm_time_label = QLabel("")
        self.llm_time_label.setFont(create_label_font(9))
        self.llm_time_label.setStyleSheet("color: #666666; padding: 2px;")
        llm_layout.addWidget(self.llm_time_label)

        self.activity_label = QLabel("—")
        self.activity_label.setFont(create_label_font(10, bold=True))
        self.activity_label.setStyleSheet("color: #a8e6cf; padding: 2px;")
        self.activity_label.setWordWrap(True)
        llm_layout.addWidget(self.activity_label)

        self.confidence_label = QLabel("Confidence: N/A")
        self.confidence_label.setFont(create_label_font(10))
        self.confidence_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        llm_layout.addWidget(self.confidence_label)

        self.llm_reasoning_label = QLabel("")
        self.llm_reasoning_label.setFont(create_label_font(8))
        self.llm_reasoning_label.setStyleSheet("color: #777777; padding: 2px;")
        self.llm_reasoning_label.setWordWrap(True)
        self.llm_reasoning_label.setMaximumHeight(54)
        llm_layout.addWidget(self.llm_reasoning_label)

        llm_frame.setLayout(llm_layout)
        llm_frame.setMinimumHeight(160)
        left_layout.addWidget(llm_frame)
        
        left_layout.addStretch()
        
        # Right side: Graph
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        if self.unit_id == "3":
            graph_title_text = "📶 WiFi Signal Quality Trend"
        else:
            graph_title_text = "📊 CSI Data Trend"
        graph_title = QLabel(graph_title_text)
        graph_title.setFont(create_label_font(11, bold=True))
        graph_title.setStyleSheet("color: #6bcf7f; padding: 4px;")
        right_layout.addWidget(graph_title)
        
        # Graph display label
        cfg_graph = GUI_CONFIG.get('graph', {})
        graph_width = cfg_graph.get('width', 400)
        graph_height = cfg_graph.get('height', 250)
        
        self.graph_label = QLabel()
        self.graph_label.setStyleSheet("background-color: #2b2b2b; border: 1px solid #3a3a3a;")
        self.graph_label.setMinimumSize(graph_width, graph_height)
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.graph_label, 1)
        
        # Combine sides
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(left_max)
        left_widget.setMinimumWidth(left_min)
        
        main_layout.addWidget(left_widget, 0)
        main_layout.addLayout(right_layout, 1)
        
        self.setLayout(main_layout)
    
    def update_data(self, unit_data):
        """Update widget with data from hub"""
        if not unit_data:
            self.status_label.setText("🔴 Disconnected")
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            return
        
        # Status
        if unit_data.get("connected"):
            self.status_label.setText("🟢 Connected")
            self.status_label.setStyleSheet("color: #6bcf7f; font-weight: bold;")
        else:
            self.status_label.setText("🔴 Disconnected")
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        
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
            self.llm_status_label.setText(f"🔄 Analyzing{dots}")
            self.llm_status_label.setStyleSheet("color: #ffd93d; font-weight: bold; padding: 2px;")
        elif llm_status == "ready":
            self.llm_status_label.setText("✅ Analysis ready")
            self.llm_status_label.setStyleSheet("color: #6bcf7f; font-weight: bold; padding: 2px;")
        else:
            self.llm_status_label.setText("⏳ Waiting for data...")
            self.llm_status_label.setStyleSheet("color: #95e1d3; font-weight: bold; padding: 2px;")

        # Time since last analysis
        if llm_ts_str:
            try:
                self._llm_timestamp = datetime.fromisoformat(llm_ts_str)
            except Exception:
                self._llm_timestamp = None
        self._refresh_llm_time()

        self.activity_label.setText(activity_name)

        if confidence > 0:
            self.confidence_label.setText(f"Confidence: {confidence:.0%}")
            if confidence > 0.7:
                self.confidence_label.setStyleSheet("color: #6bcf7f; padding: 2px;")
            elif confidence > 0.4:
                self.confidence_label.setStyleSheet("color: #ffd93d; padding: 2px;")
            else:
                self.confidence_label.setStyleSheet("color: #ff6b6b; padding: 2px;")
        else:
            self.confidence_label.setText("Confidence: N/A")
            self.confidence_label.setStyleSheet("color: #888888; padding: 2px;")

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
            fig = plt.figure(figsize=(6.5, 4.0), dpi=120, facecolor='#1a1a1a')
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
                label_height = 250
            if label_width < 100:
                label_width = 400
            
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
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
            }
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #3a3a3a;
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
        header = QLabel("🌐 PhantomSense Hub - Multi-Unit Monitor")
        header_font = QFont()
        header_font.setPointSize(13)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("color: #6bcf7f;")
        main_layout.addWidget(header)
        
        # Hub status
        self.hub_status = QLabel("🔴 Connecting...")
        hub_status_font = QFont()
        hub_status_font.setPointSize(11)
        hub_status_font.setBold(True)
        self.hub_status.setFont(hub_status_font)
        self.hub_status.setStyleSheet("color: #ff6b6b; padding: 8px; background-color: #2b2b2b; border-radius: 3px;")
        main_layout.addWidget(self.hub_status)
        
        # Units container
        units_layout = QVBoxLayout()
        units_layout.setContentsMargins(0, 0, 0, 0)
        units_layout.setSpacing(spacing)
        
        # Unit 1
        unit_min_height = cfg_layout.get('unit_min_height', 300)
        self.unit1_widget = UnitDataWidget("1", "Unit 1 - PhantomSense-Unit-1")
        self.unit1_widget.setMinimumHeight(unit_min_height)
        units_layout.addWidget(self.unit1_widget)
        
        # Separator
        separator = QFrame()
        separator.setStyleSheet("QFrame { background-color: #3a3a3a; height: 1px; border: none; }")
        separator.setMaximumHeight(1)
        units_layout.addWidget(separator)
        
        # Unit 2
        self.unit2_widget = UnitDataWidget("2", "Unit 2 - PhantomSense-Unit-2")
        self.unit2_widget.setMinimumHeight(unit_min_height)
        units_layout.addWidget(self.unit2_widget)

        # Separator
        separator2 = QFrame()
        separator2.setStyleSheet("QFrame { background-color: #3a3a3a; height: 1px; border: none; }")
        separator2.setMaximumHeight(1)
        units_layout.addWidget(separator2)

        # Unit 3 - Franklin WiFi
        self.unit3_widget = UnitDataWidget("3", "Unit 3 - Franklin WiFi Sensor")
        self.unit3_widget.setMinimumHeight(unit_min_height)
        units_layout.addWidget(self.unit3_widget)
        
        main_layout.addLayout(units_layout, 1)
        
        # Footer stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 3px; padding: 8px; }")
        stats_frame.setMaximumHeight(35)
        stats_layout = QHBoxLayout()
        stats_layout.setContentsMargins(5, 5, 5, 5)
        
        self.stats_label = QLabel("Waiting for data...")
        stats_font = QFont()
        stats_font.setPointSize(9)
        self.stats_label.setFont(stats_font)
        self.stats_label.setStyleSheet("color: #95e1d3; padding: 4px;")
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
        self.hub_status.setText("🟢 Hub Connected")
        self.hub_status.setStyleSheet("color: #6bcf7f;")
        
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
        
        # Update stats
        total_frames = data.get("total_frames", 0)
        total_activities = data.get("total_activities", 0)
        connected = len([u for u in units.values() if u.get('connected')])
        total = len(units)
        self.stats_label.setText(
            f"📊 Total Frames: {total_frames} | Total Activities: {total_activities} | "
            f"Connected Units: {connected}/{total}"
        )
    
    def on_hub_error(self, error_msg):
        """Handle errors from hub"""
        self.hub_status.setText(f"🔴 Error: {error_msg}")
        self.hub_status.setStyleSheet("color: #ff6b6b;")
    
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
