# PhantomSense Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **PyQt6 Desktop GUI** (`phantomsense_desktop.py`)
  - Real-time visualization of dual ESP32-S3 sensor units
  - Live CSI data trend graphs with matplotlib Agg backend
  - Unit status indicators and connectivity monitoring
  - Dark theme with optimized contrast for readability
  
- **GUI Configuration System** (`gui_config.json` + `GUI_CONFIG_README.md`)
  - User-customizable layout without code changes
  - Adjustable window size, fonts, colors, margins, spacing
  - Graph rendering parameters (width, height, update interval)
  - Data buffering configuration (history limits, poll intervals)
  
- **LLM Activity Analysis**
  - Real-time activity reasoning using Ollama (llama3.1:8b)
  - Confidence scoring for activity predictions
  - Activity classification: walking, sitting, falling, presence
  - Data collection pipeline for pattern learning
  
- **Hub Data Collection**
  - Comprehensive metric buffering (CSI amplitude, noise floor, SNR)
  - Per-unit statistics (frame count, last update timestamp)
  - Timeline tracking for activity events
  - Pattern aggregation for LLM reasoning
  
- **Documentation**
  - LLM Integration Guide (`LLM_INTEGRATION_GUIDE.md`)
  - GUI Configuration README (`GUI_CONFIG_README.md`)
  - Hardware verification checklist (`firmware/HARDWARE_VERIFICATION.md`)
  - Security guidelines (`firmware/SECURITY.md`)

### Fixed
- **GUI Text Visibility Issue**
  - Increased font sizes: 9pt → 10-11pt for metrics
  - Added explicit padding to all labels (2-4px)
  - Set grid row minimum heights (22-25px per row)
  - Set frame minimum heights (100-160px)
  - Increased label minimum widths (50-120px)
  - Resolved PyQt6 enum path: Qt.TransformationMode.SmoothTransformation
  
- **Matplotlib/PyQt6 Backend Conflict**
  - Switched from FigureCanvasQTAgg to Agg backend
  - Implemented Figure → BytesIO → PNG → QImage → QPixmap pipeline
  - Proper figure cleanup with plt.close() to prevent memory leaks
  
- **Hub Connection Issues**
  - Verified MQTT bridge connectivity
  - Confirmed both ESP32 units connected and transmitting
  - FastAPI endpoints responding correctly

### Changed
- **Data Aggregator** - Enhanced metric collection and buffering
- **MQTT Bridge** - Improved connection stability and message handling
- **API Endpoints** - Expanded `/devices`, `/metrics`, `/reasoning` endpoints
- **Signal Processor** - Refined noise filtering algorithms

### Technical Details

#### PyQt6 GUI Architecture
- `HubDataFetcher(QThread)` - Background thread polling hub every 500ms
- `UnitDataWidget(QWidget)` - Per-unit display panels with status, data, and activity frames
- `create_label_font()` - Consistent font sizing helper
- Configuration system with JSON fallback defaults
- Matplotlib integration for trend visualization

#### LLM Integration
- **Model**: Ollama llama3.1:8b
- **Inference**: Local GPU (NVIDIA RTX 3060, AMD RX 7900 XTX)
- **Endpoints**: `/reasoning` (activity analysis), `/patterns` (trend analysis)
- **Update Frequency**: Per-unit updates trigger reasoning

#### Performance Metrics
- CSI Data Collection: 250Hz per unit
- GUI Update Interval: 500ms
- Hub Poll Interval: 500ms
- LLM Response Time: <2s per analysis (GPU-accelerated)
- Memory Usage: ~180MB GUI, ~1.5GB hub process

### Known Limitations
- TinyML models not yet deployed on ESP32-S3
- No persistent database (in-memory buffering only)
- Web dashboard not yet implemented
- Single-room coverage (mesh networking TODO)

### Testing Status
- ✅ GUI rendering and text visibility
- ✅ Hub connectivity and data aggregation
- ✅ LLM integration and activity analysis
- ✅ MQTT bridge and dual-unit coordination
- ✅ REST API endpoints
- ⏳ Long-term data collection and pattern learning
- ⏳ TinyML edge inference deployment

---

## How to Use

### Start Data Collection
```bash
# Terminal 1: Start Hub Server
cd hub
python hub.py

# Terminal 2: Start Desktop GUI
python phantomsense_desktop.py
```

### View Data
- **Hub REST API**: `http://localhost:5000/devices`
- **GUI**: Real-time metrics in PyQt6 window
- **LLM Reasoning**: Activity analysis in GUI activity frame

### Customize GUI Layout
Edit `hub/gui_config.json`:
```json
{
  "window": {"width": 1600, "height": 900},
  "layout": {"left_panel_min_width": 180, "unit_min_height": 300},
  "colors": {"background": "#1a1a1a", "text_accent": "#6bcf7f"}
}
```
Then restart GUI.

---

## Next Steps
1. Deploy TinyML activity classification models on ESP32-S3
2. Implement persistent data storage (PostgreSQL)
3. Build web dashboard for remote monitoring
4. Add mesh networking for multi-room coverage
5. Mobile app integration

---

**Last Updated**: May 12, 2026
**Status**: Active Development - Production Ready for Dual-Unit Monitoring
