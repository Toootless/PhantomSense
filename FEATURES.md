# PhantomSense Real-Time Monitoring Features

## Feature 1: ESP32-S3 Status Display

### Overview
Each ESP32-S3 device now has a real-time status indicator using GPIO-based LED control.

### Status Indicators
- 🔴 **LED OFF (Dark)**: Device idle or disconnected
- 🟡 **Fast Blink (100ms)**: Connecting to WiFi network
- 🟢 **Slow Blink (500ms on, 2s off)**: Connected and communicating with basestation
- 🟢 **Rapid Blink (200ms)**: Actively transmitting data to hub

### Hardware Setup
- **GPIO Pin**: GPIO 46 (configurable in `display_driver.c`)
- **LED Connection**: GPIO 46 → 1kΩ resistor → LED anode → LED cathode → GND

### Files Modified
- `components/display_driver/display_driver.h` - API definitions
- `components/display_driver/display_driver.c` - LED control implementation
- `components/display_driver/CMakeLists.txt` - Build configuration
- `main/main.c` - Integration and status monitoring
- `main/CMakeLists.txt` - Component dependency

### Code Integration
The display status is automatically managed by the `status_monitor_task()` in main.c:
- Monitors WiFi connection status
- Monitors MQTT connection status
- Updates LED status every 2 seconds

No additional code needed—it's automatic!

---

## Feature 2: Desktop Application for Data Visualization

### Overview
A desktop PyQt6 application that displays real-time data from both ESP32-S3 units, with LLM-calculated activity analysis.

### Features
✅ Real-time dual-unit data display  
✅ CSI amplitude and noise floor visualization  
✅ WiFi signal strength (RSSI) monitoring  
✅ LLM activity classification with confidence scores  
✅ Dark theme for extended viewing  
✅ Auto-connecting to hub (localhost:5000)

### Installation & Launch

#### Option 1: Quick Launch (Automatic Dependency Installation)
```bash
cd c:\Users\johnj\OneDrive\Documents\VS_projects\PhantomSense\hub
python launch_desktop.py
```

#### Option 2: Manual Installation
```bash
# Install PyQt6
pip install PyQt6

# Run the app
python phantomsense_desktop.py
```

### Running the Application
1. **Hub Server must be running** on Franklin:
   ```bash
   cd hub
   python hub.py
   ```

2. **Launch Desktop App** (from hub directory):
   ```bash
   python launch_desktop.py
   # or
   python phantomsense_desktop.py
   ```

3. **View Data**:
   - Left panel: Unit 1 (PhantomSense-Unit-1)
   - Right panel: Unit 2 (PhantomSense-Unit-2)
   - Each shows:
     - Connection status (🟢 Connected / 🔴 Disconnected)
     - IP address & WiFi signal strength
     - CSI amplitude (wireless signal strength)
     - Noise floor
     - LLM-calculated activity with confidence
     - Last update timestamp

### API Endpoints Used

The desktop app connects to these hub REST endpoints:

**Get All Devices**
```
GET http://localhost:5000/api/devices
```
Response:
```json
{
  "units": {
    "unit1": {
      "connected": true,
      "ip_address": "192.168.1.50",
      "rssi": -65,
      "latest_csi": {"amplitude_mean": 125.4, "noise_floor": -80},
      "latest_activity": {"name": "Sitting", "confidence": 0.92}
    },
    "unit2": { ... }
  },
  "total_frames": 5234,
  "total_activities": 142
}
```

**Get Device Data Stream**
```
GET http://localhost:5000/api/devices/{unit_id}/stream
```

### Data Flow
```
ESP32-S3 (COM5/COM8)
    ↓ (WiFi + MQTT)
Franklin Hub (hub.py)
    ↓ (REST API)
Desktop App (phantomsense_desktop.py)
    ↓ (PyQt6 UI)
Display
```

### Screen Layout
```
┌─────────────────────────────────────────────────────────┐
│ 🌐 PhantomSense Hub - Dual Unit Monitor                 │
│ 🟢 Hub Connected                                        │
├──────────────────────┬──────────────────────────────────┤
│ 📡 Unit 1            │ 📡 Unit 2                        │
│ PhantomSense-Unit-1  │ PhantomSense-Unit-2              │
│                      │                                  │
│ Status: 🟢 Connected │ Status: 🟢 Connected             │
│ IP: 192.168.1.50     │ IP: 192.168.1.51                 │
│ WiFi: -65 dBm        │ WiFi: -62 dBm                    │
│                      │                                  │
│ CSI: 125.4           │ CSI: 118.2                       │
│ Noise: -80 dBm       │ Noise: -80 dBm                   │
│ Last: 15:06:32       │ Last: 15:06:31                   │
│                      │                                  │
│ 🤖 LLM Analysis:     │ 🤖 LLM Analysis:                 │
│ Sitting              │ Walking                          │
│ Confidence: 92%      │ Confidence: 87%                  │
│                      │                                  │
└──────────────────────┴──────────────────────────────────┘
│ 📊 Total Frames: 5234 | Total Activities: 142           │
└─────────────────────────────────────────────────────────┘
```

### Troubleshooting

**"Cannot connect to hub"**
- Ensure hub is running: `python hub.py`
- Check hub is on port 5000: `netstat -ano | findstr 5000`
- Verify Franklin IP/DNS resolution

**"No data showing"**
- Check devices are flashed and powered on
- Verify WiFi credentials (DrWho/Mollymay2212)
- Check hub logs for MQTT connection issues
- Devices may take 30s to connect on first boot

**"PyQt6 import error"**
- Run: `pip install PyQt6`
- Or use launcher: `python launch_desktop.py`

### Customization

**Change Hub URL**
Edit line 18 in `phantomsense_desktop.py`:
```python
HUB_URL = "http://your-ip:5000"
```

**Change Update Frequency**
Edit line 19:
```python
UPDATE_INTERVAL = 500  # milliseconds (lower = more frequent)
```

**Change Theme Colors**
Edit colors in `UnitDataWidget.setup_ui()` and `PhantomSenseApp.setup_ui()`

---

## Next Steps

1. ✅ ESP32 display driver: **DONE**
2. ✅ Desktop app visualization: **DONE**
3. 🔄 Rebuild firmware with display driver
4. 🔄 Reflash both devices
5. 🔄 Start hub server
6. 🔄 Launch desktop app
7. 🔄 Verify dual-unit data stream

---

## Summary

| Component | Status | Location |
|-----------|--------|----------|
| Display Driver | ✅ Created | `components/display_driver/` |
| Main Integration | ✅ Updated | `main/main.c` |
| Desktop App | ✅ Created | `hub/phantomsense_desktop.py` |
| API Endpoints | ✅ Added | `hub/phantomsense_hub/api/__init__.py` |
| Launcher Script | ✅ Created | `hub/launch_desktop.py` |

Both features are **ready to deploy**! 🚀
