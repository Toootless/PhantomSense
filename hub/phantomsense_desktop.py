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

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QFrame, QGridLayout, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QColor, QPalette, QPixmap, QImage, QFont

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
    
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
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
        title_label = QLabel(f"📡 {self.unit_name}")
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
        
        csi_label_title = QLabel("CSI Amp:")
        csi_label_title.setFont(create_label_font(10))
        csi_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        csi_label_title.setMinimumWidth(70)
        self.csi_mean_label = QLabel("0.0")
        self.csi_mean_label.setFont(create_label_font(10))
        self.csi_mean_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        self.csi_mean_label.setMinimumWidth(90)
        data_layout.addWidget(csi_label_title, 0, 0)
        data_layout.addWidget(self.csi_mean_label, 0, 1)
        
        noise_label_title = QLabel("Noise:")
        noise_label_title.setFont(create_label_font(10))
        noise_label_title.setStyleSheet("color: #95e1d3; padding: 2px;")
        noise_label_title.setMinimumWidth(70)
        self.noise_floor_label = QLabel("0")
        self.noise_floor_label.setFont(create_label_font(10))
        self.noise_floor_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        self.noise_floor_label.setMinimumWidth(90)
        data_layout.addWidget(noise_label_title, 1, 0)
        data_layout.addWidget(self.noise_floor_label, 1, 1)
        
        snr_label_title = QLabel("SNR:")
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
        
        # Activity frame
        activity_frame = QFrame()
        activity_frame.setStyleSheet("QFrame { background-color: #2b2b2b; border-radius: 4px; padding: 10px; }")
        activity_frame.setMinimumHeight(100)
        activity_layout = QVBoxLayout()
        activity_layout.setSpacing(8)
        activity_layout.setContentsMargins(10, 10, 10, 10)
        
        activity_title = QLabel("🤖 Activity")
        activity_title.setFont(create_label_font(11, bold=True))
        activity_title.setStyleSheet("color: #6bcf7f; padding: 4px;")
        activity_layout.addWidget(activity_title)
        
        self.activity_label = QLabel("Waiting...")
        self.activity_label.setFont(create_label_font(10))
        self.activity_label.setStyleSheet("color: #a8e6cf; padding: 2px;")
        self.activity_label.setWordWrap(True)
        self.activity_label.setMinimumHeight(20)
        activity_layout.addWidget(self.activity_label)
        
        self.confidence_label = QLabel("Confidence: N/A")
        self.confidence_label.setFont(create_label_font(10, bold=True))
        self.confidence_label.setStyleSheet("color: #ffd93d; padding: 2px;")
        self.confidence_label.setMinimumHeight(20)
        activity_layout.addWidget(self.confidence_label)
        
        activity_frame.setLayout(activity_layout)
        activity_frame.setMinimumHeight(80)
        left_layout.addWidget(activity_frame)
        
        left_layout.addStretch()
        
        # Right side: Graph
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        graph_title = QLabel("📊 CSI Data Trend")
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
        self.csi_mean_label.setText(f"{csi_mean:.2f} dBm")
        
        noise_floor = csi_data.get("noise_floor", 0)
        self.noise_floor_label.setText(f"{noise_floor} dBm")
        
        # Calculate SNR
        snr = csi_mean - noise_floor if csi_mean and noise_floor else 0
        self.snr_label.setText(f"{snr:.1f} dB")
        
        # Update counters
        frame_count = unit_data.get("frame_count", 0)
        self.frame_count_label.setText(str(frame_count))
        
        # Update timestamp
        self.last_update_label.setText(datetime.now().strftime("%H:%M:%S"))
        
        # Store in history for graphing
        if csi_mean and noise_floor:
            self.amplitude_history.append(csi_mean)
            self.noise_history.append(noise_floor)
        
        # Activity analysis
        activity = unit_data.get("latest_activity", {})
        activity_name = activity.get("name", "Unknown")
        confidence = activity.get("confidence", 0)
        
        self.activity_label.setText(activity_name)
        self.confidence_label.setText(f"Confidence: {confidence:.1%}")
        
        # Color code confidence
        if confidence > 0.7:
            self.confidence_label.setStyleSheet("color: #6bcf7f;")  # Green
        elif confidence > 0.4:
            self.confidence_label.setStyleSheet("color: #ffd93d;")  # Yellow
        else:
            self.confidence_label.setStyleSheet("color: #ff6b6b;")  # Red
        
        # Update graph
        self.update_graph()
    
    def update_graph(self):
        """Update CSI trend graph and display as image"""
        try:
            # Close all previous figures to avoid memory leak
            plt.close('all')
            
            # Create a new matplotlib figure for rendering
            fig = plt.figure(figsize=(5, 3.5), dpi=80, facecolor='#1a1a1a')
            ax = fig.add_subplot(111)
            
            # Plot data if available
            if self.amplitude_history and self.noise_history:
                x_axis = list(range(len(self.amplitude_history)))
                ax.plot(x_axis, list(self.amplitude_history), color='#6bcf7f', marker='o', 
                           linewidth=2, markersize=4, label='CSI Amplitude', alpha=0.8)
                ax.plot(x_axis, list(self.noise_history), color='#ff6b6b', marker='s', 
                           linewidth=2, markersize=4, label='Noise Floor', alpha=0.8)
                ax.legend(loc='upper left', fontsize=8, framealpha=0.9, 
                         facecolor='#2b2b2b', edgecolor='#3a3a3a', labelcolor='#a8e6cf')
            
            # Style the plot
            ax.set_facecolor('#2b2b2b')
            ax.grid(True, alpha=0.2, color='white')
            ax.set_xlabel('Sample', color='#a8e6cf', fontsize=9)
            ax.set_ylabel('dBm', color='#a8e6cf', fontsize=9)
            ax.tick_params(colors='#a8e6cf', labelsize=8)
            ax.spines['bottom'].set_color('#3a3a3a')
            ax.spines['left'].set_color('#3a3a3a')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
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
        header = QLabel("🌐 PhantomSense Hub - Dual Unit Monitor")
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
    
    def on_hub_data(self, data):
        """Handle data from hub"""
        # Update hub status
        self.hub_status.setText("🟢 Hub Connected")
        self.hub_status.setStyleSheet("color: #6bcf7f;")
        
        # Extract unit data
        units = data.get("units", {})
        
        # Update Unit 1 (hub stores as string key "1")
        if "1" in units:
            self.unit1_widget.update_data(units["1"])
        else:
            self.unit1_widget.update_data(None)
        
        # Update Unit 2 (hub stores as string key "2")
        if "2" in units:
            self.unit2_widget.update_data(units["2"])
        else:
            self.unit2_widget.update_data(None)
        
        # Update stats
        total_frames = data.get("total_frames", 0)
        total_activities = data.get("total_activities", 0)
        self.stats_label.setText(
            f"📊 Total Frames: {total_frames} | Total Activities: {total_activities} | "
            f"Connected Units: {len([u for u in units.values() if u.get('connected')])}/2"
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
