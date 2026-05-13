# PhantomSense Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- **Franklin WiFi Sensor** (`hub/franklin_sensor.py`) — NEW
  - Third sensor unit (Unit 3) running on the Franklin basestation itself
  - Polls Windows WLAN API (`wlanapi.dll`) via ctypes at 4 Hz — zero subprocess overhead
  - Falls back to `netsh wlan show interfaces` parsing if DLL is unavailable
  - Computes activity score from WiFi signal quality total variation (motion = more variance)
  - Derives `phase_velocity` (mean |Δquality| / sec) and rolling noise floor (10th-percentile)
  - POSTs to hub `/update` as Unit 3 every 5 s; fed into LLM reasoning pipeline alongside ESP32 units
  - CLI flags: `--hub`, `--unit-id`, `--interval`, `--debug`

- **SQLite Persistence** (`hub/phantomsense_hub/core/db.py`) — NEW
  - All activity data and LLM reasoning results persisted to `hub/data/phantomsense.db`
  - WAL journal mode + NORMAL sync for safe concurrent writes
  - Tables: `activities` (per-unit CSI/WiFi samples) and `llm_reasoning` (LLM results with confidence)
  - LLM cache restored from DB on hub startup — reasoning survives hub restarts
  - New API endpoints: `GET /history/{unit_id}/activities`, `GET /history/{unit_id}/reasoning`,
    `GET /history/units`, `POST /reprocess/{unit_id}`

- **LLM Status in GUI**
  - Real-time `llm_status` field (`waiting` / `processing` / `ready`) per unit in `/devices`
  - `is_reasoning` flag on `LLMReasoner` — set during active Ollama call
  - "🔄 Analyzing..." / "✅ Analysis ready" / "⏳ Waiting..." status labels with colour coding
  - "Last analysis: Xs ago" timer refreshed every second via `QTimer`
  - LLM reasoning snippet (up to 280 chars) displayed below confidence score

- **Multi-Unit GUI** (`hub/phantomsense_desktop.py`)
  - Upgraded from dual-unit to **three-unit** monitor panel (Units 1, 2, 3)
  - Unit 3 uses `📶` icon, "WiFi Signal Quality Trend" graph title, and "Signal Quality (%)" Y-axis
  - Unit 3 metrics show quality % and activity score (0–100), not dBm
  - Footer stats now show `Connected: X/N` where N is actual unit count from hub
  - Header updated to "Multi-Unit Monitor"

- **Firmware Frame Count Fix** (`firmware/main/main.c`)
  - Added `g_csi_frame_count` global — incremented in `csi_acquisition_task`
  - `signal_processing_task` now reads this counter instead of the always-zero `signal_processor_get_stats()`
  - Log line only emitted on real frame-count change at 100-frame intervals — eliminates spam

### Changed

- **`start_all.bat`** — now launches Franklin WiFi Sensor as a third window between hub start and GUI
  - Hub wait increased from 3 s → 4 s; sensor gets 2 s to register before GUI opens
  - Status banner lists all 4 components
- **`/devices` endpoint** — enriched with `llm_status`, `llm_reasoning`, `llm_timestamp`,
  activity `name` from LLM cache, and `confidence` as float 0–1
- **GUI** — migrated from PyQt6 to **PySide6** for Windows compatibility

### Fixed

- Unit 3 Signal/Noise/Graph all showing 0: `csi_amplitude` was set to `activity_score` which was 0
  at 100% stable WiFi; fixed by encoding real signal quality % as amplitude and deriving noise_floor
  such that `snr = activity_score` is preserved for the LLM pipeline
- History graph blank for Unit 3: append condition `if csi_mean and noise_floor` evaluated False
  when both were 0; now always appends for unit 3

### Known Limitations
- TinyML models not yet deployed on ESP32-S3
- Web dashboard not yet implemented
- Single-room coverage (mesh networking TODO)
- Unit 2 (COM8) still on pre-frame-count-fix firmware

### Testing Status
- ✅ GUI rendering — all three units visible with correct data
- ✅ Hub connectivity and data aggregation (3 units)
- ✅ LLM integration and activity analysis (all 3 units reasoned independently)
- ✅ SQLite persistence — activities and reasoning saved across hub restarts
- ✅ Franklin WiFi Sensor — wlanapi.dll polling, 4 Hz, HTTP 200 on every POST
- ✅ REST API endpoints including history and reprocess
- ⏳ Long-term data collection and pattern learning
- ⏳ TinyML edge inference deployment

---


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
