# PhantomSense Deployment Status (May 12, 2026)

## Current State

### ✅ **OPERATIONAL: Unit 2 (COM8)**

- **Hardware:** Waveshare ESP32-S3-LCD-1.47, MAC 48:ca:43:a3:f9:e0
- **Firmware:** UNIT_ID_2 deployed (build 5/12/2026)
- **Boot Status:** ✅ Successful
- **WiFi:** ✅ Connected to "DrWho" network
- **LCD Display:** ✅ Rendering status screen
- **Hub Connectivity:** ⚠️ **BLOCKED** - HTTP POST connection fails with error 32774

### ❌ **NON-OPERATIONAL: Unit 1 (COM5)**

- **Hardware:** Waveshare ESP32-S3-LCD-1.47, MAC 80:b5:4e:db:2d:2c
- **Flash Status:** **CORRUPTED** - Persistent 0xffffffff boot headers
- **Boot Behavior:** Loops "invalid header: 0xffffffff" → watchdog reset
- **Action Required:** Device replacement or deep flash chip inspection likely needed

## Architecture Change: MQTT → HTTP (Temporary)

The current firmware uses **HTTP POST** instead of MQTT for device-to-hub communication:

```
Device (Unit 2) 
  ↓ WiFi
  ↓ HTTP POST every 5 seconds
Hub Server (172.31.175.241:5000/update)
```

**Reason:** Hub server implemented as FastAPI web service; MQTT not yet set up.

**Payload Format:**
```json
{
  "unit_id": 2,
  "unit_name": "PhantomSense-Unit-2",
  "rssi": -45,
  "ip_address": "192.168.1.X",
  "csi_amplitude": -50.0,
  "noise_floor": -80.0,
  "timestamp_ms": 1715507000000
}
```

## Build System: ESP-IDF v6.0.1

**Upgraded from:** ESP-IDF v5.0  
**Reason:** Improved stability, updated component APIs, better PSRAM handling

### Compatibility Fixes Applied

1. **GPIO Component Path** (ESP-IDF v6.0.1)
   - Previous: `driver/gpio.h`
   - Current: Explicit `esp_driver_gpio` component in CMakeLists.txt
   - File: `components/display_driver/CMakeLists.txt` (updated)

2. **HTTP Event Types** (v6.0.1 extended enum)
   - Added handlers for: `HTTP_EVENT_ON_HEADERS_COMPLETE`, `HTTP_EVENT_ON_STATUS_CODE`
   - File: `main/http_client.c` (updated)

3. **Event Handler API Strictness** (v6.0.1)
   - Requires explicit `(void*)` cast for const pointers in `esp_event_handler_instance_register()`
   - File: `main/wifi_setup.c` (line 64, 69 - updated)

4. **CSI Driver Compatibility** ⚠️
   - `esp_wifi_set_csi_config()` returns `ESP_FAIL` in v6.0.1
   - **Status:** DISABLED in current build (lines 248-251 in main.c commented)
   - **TODO:** Investigate v6.0.1 CSI API changes and fix

### Build Verification

```bash
# Latest build result:
cd firmware
idf.py build

# Output: Clean compilation, 932592 bytes total (18% partition free)
# Binary: phantomsense_firmware.bin
```

## Device Differentiation Mechanism

**File:** `firmware/main/include/app_config.h`

```c
#define CURRENT_UNIT_ID UNIT_ID_1  // Toggle between UNIT_ID_1 and UNIT_ID_2
```

**Workflow:**
1. Edit `app_config.h` and set `CURRENT_UNIT_ID` to desired unit
2. Run `idf.py build`
3. Flash to device using `idf.py flash` or esptool
4. Device loads corresponding config from `app_config.c`

**Current Repository State:** `CURRENT_UNIT_ID = UNIT_ID_1` (default, for git stability)

## Network Connectivity Issue: Device ↔ Hub

### Problem
- Unit 2 boots successfully ✅
- WiFi connects to "DrWho" network ✅
- HTTP POST fails: `ESP_ERR_HTTP_CONNECT` with esp-tls error 32774 ❌

### Root Cause Identified
- Hub runs inside **WSL (Windows Subsystem for Linux)** on IP 172.31.175.241:5000
- WiFi devices cannot route to WSL internal IP from WiFi subnet
- Windows host IP (10.0.0.84:5000) also unreachable from WiFi devices
- Attempted firewall exceptions and route modifications unsuccessful

### Current Hub Status
- ✅ Listening on 172.31.175.241:5000 (WSL bridge IP)
- ✅ Accessible from Windows via `curl http://172.31.175.241:5000/status`
- ❌ NOT accessible from WiFi subnet (routing/isolation issue)

### Solution: Windows Port Forwarding

**Step 1:** Enable port forwarding on Windows (PowerShell as Admin):
```powershell
netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=172.31.175.241

# Verify:
netsh interface portproxy show v4tov4
```

**Step 2:** Identify Windows WiFi adapter IP:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like "*WiFi*"}
```

**Step 3:** Update firmware hub_url in `main/app_config.c`:
```c
.http = {
    .hub_url = "http://[WINDOWS_WIFI_IP]:5000",  // e.g., 192.168.1.100:5000
    .update_endpoint = "/update",
}
```

**Step 4:** Rebuild and reflash Unit 2 (or both units)

## Multi-Unit Build Workflow

### For Unit 1:
```bash
# Update header
echo "#define CURRENT_UNIT_ID UNIT_ID_1" > main/include/app_config.h

# Build
idf.py build

# Flash to COM5
idf.py -p COM5 flash
```

### For Unit 2:
```bash
# Update header
echo "#define CURRENT_UNIT_ID UNIT_ID_2" > main/include/app_config.h

# Build  
idf.py build

# Flash to COM8
idf.py -p COM8 flash
```

### Using VS Code ESP-IDF Extension
1. Click "Device Selection" button → choose COM5 or COM8
2. Edit `app_config.h` CURRENT_UNIT_ID
3. Click "Build" button
4. Click "Flash" button

## Next Steps (Priority Order)

1. **Fix Device ↔ Hub Connectivity** (CRITICAL)
   - Apply Windows netsh port forwarding (Step 1 above)
   - Identify Windows WiFi adapter IP (Step 2)
   - Update app_config.c with accessible IP
   - Rebuild and reflash Unit 2
   - Monitor COM8 for successful HTTP POST

2. **Unit 1 Hardware Recovery** (HIGH)
   - Power cycle COM5 device
   - Attempt fresh erase/reflash
   - If still corrupted: order replacement device

3. **Dual-Unit Deployment** (HIGH)
   - After COM5 recovery, deploy Unit 1 firmware
   - Verify hub /devices endpoint shows both units
   - Monitor simultaneous device reports

4. **CSI Driver Debugging** (MEDIUM)
   - Research ESP-IDF v6.0.1 `esp_wifi_set_csi_config()` API
   - Fix csi_driver.c for v6.0.1 compatibility
   - Re-enable csi_acquisition_task() in main.c

5. **WS2812B RGB LED Implementation** (MEDIUM)
   - Implement RMT-based driver for GPIO 38
   - Add status color indicators: Green=Connected, Yellow=Connecting, Red=Error
   - Integrate with display_set_status() function

## Files Modified This Session

- `firmware/main/include/app_config.h` - CURRENT_UNIT_ID toggling
- `firmware/main/app_config.c` - Hub URL correction (172.31.175.241:5000)
- `firmware/main/wifi_setup.c` - ESP-IDF v6.0.1 const cast fix
- `firmware/main/http_client.c` - HTTP event handler expansion
- `firmware/components/display_driver/CMakeLists.txt` - ESP-IDF v6.0.1 component list
- `firmware/main/main.c` - CSI driver disabled (commented task creation)

## Verification Commands

### Check Hub Connectivity
```bash
# From Windows PowerShell:
curl http://172.31.175.241:5000/status

# Expected response:
# {"units":0,"active_units":0,"buffered_activities":0,"is_running":true,...}
```

### Monitor Device Serial Output
```bash
# From Windows PowerShell:
python -c "
import serial
ser = serial.Serial('COM8', 115200, timeout=None)
while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if 'HTTP' in line or 'WiFi' in line or 'POST' in line:
        print(line)
"
```

### List Available Firmware Binaries
```bash
ls -la firmware/build/
# Output: bootloader.bin, partition-table.bin, phantomsense_firmware.bin
```

## Contact & Support

**Project:** PhantomSense Multi-Unit WiFi Sensing  
**Last Updated:** May 12, 2026  
**Maintainer:** See repository contributors
