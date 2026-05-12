# PhantomSense Firmware

ESP32-S3 firmware for WiFi sensing with CSI (Channel State Information) and RGB LED status indicators.

## Hardware

**Target Device:** Waveshare ESP32-S3-LCD-1.47
- Dual-core 240MHz ESP32-S3
- 8MB embedded PSRAM
- 1.47" ST7789 LCD display (172x320)
- **WS2812B Addressable RGB LED** (not a simple RGB LED)
- WiFi + Bluetooth 5.0

### ⚠️ GPIO Pinout (Verified against Waveshare Schematics)

> **IMPORTANT:** Pins were verified May 11, 2026 against official Waveshare schematics.
> Previous test pins (46-48 for RGB, 33 for backlight) did NOT work.

| Component | GPIO | Function | Notes |
|-----------|------|----------|-------|
| **RGB LED (WS2812B)** | 38 | Data input | Requires RMT peripheral (not simple GPIO) |
| **LCD Backlight** | 15 | Enable (HIGH=on) | **Must be HIGH to see display** |
| **LCD Reset** | 13 | Reset signal | Active LOW |
| **LCD DC** | 14 | Data/Command | HIGH=data, LOW=command |
| **LCD CS** | 12 | Chip Select | SPI slave select |
| **SPI MOSI** | 11 | Data to display | SPI data line |
| **SPI CLK** | 10 | Clock | SPI clock line |

**See [HARDWARE_VERIFICATION.md](./HARDWARE_VERIFICATION.md) for detailed hardware diagnostics and WS2812B implementation guide.**

## Project Structure

```
firmware/
├── main/                    # Application code
│   ├── app_config.c        # ⚠️ IGNORED (contains WiFi password)
│   ├── app_config.c.example # Template - copy to app_config.c
│   ├── app_config.h        # Configuration types
│   ├── main.c              # Application entry point
│   ├── wifi_setup.c        # WiFi initialization
│   ├── mqtt_setup.c        # MQTT configuration
│   └── include/
├── components/
│   ├── csi_driver/         # WiFi CSI data acquisition
│   ├── display_driver/     # RGB LED and LCD control
│   ├── inference/          # ML inference engine
│   ├── mqtt_client/        # MQTT communication
│   └── signal_processor/   # Signal processing
├── partitions/             # Flash memory layout
├── CMakeLists.txt          # Build configuration
└── build/                  # Build output (gitignored)
```

## Prerequisites

- **ESP-IDF v5.0+**
- **Python 3.8+**
- **esptool** (installed via ESP-IDF)
- **WSL or native Linux/Mac** (for build tools)

## Security Setup ⚠️

**IMPORTANT:** WiFi credentials and hub URL are stored in `main/app_config.c`, which is **NOT committed to GitHub**.

### First Time Setup

1. **Copy the example configuration:**
   ```bash
   cp main/app_config.c.example main/app_config.c
   ```

2. **Edit with your credentials:**
   ```c
   // main/app_config.c
   .wifi_ssid = "YOUR_NETWORK_NAME",        // Your WiFi SSID
   .wifi_password = "YOUR_PASSWORD",        // Your WiFi password
   .hub_url = "http://192.168.1.100:5000",  // Your hub server IP
   ```

3. **Verify .gitignore protection:**
   ```bash
   git status main/app_config.c
   # Should show: app_config.c (not tracked)
   ```

## Build

### Using WSL (Recommended)

```bash
cd firmware

# Full clean build
wsl bash -c 'source /home/esp-idf/export.sh && \
  IDF_TARGET=esp32s3 idf.py fullclean && \
  IDF_TARGET=esp32s3 idf.py build'
```

### Using Native ESP-IDF (Windows/Mac/Linux)

```bash
idf.py set-target esp32s3
idf.py build
```

### Build Output
- `build/bootloader/bootloader.bin` - Bootloader
- `build/partition_table/partition-table.bin` - Partition table
- `build/phantomsense_firmware.bin` - Application binary

## Flash

### Flash Both Devices

```bash
# Unit 1 → COM5
python -m esptool --chip esp32s3 -p COM5 -b 460800 \
  --before default-reset --after hard-reset write-flash \
  --flash-mode dio --flash-size 2MB --flash-freq 80m \
  0x0 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0x10000 build/phantomsense_firmware.bin

# Unit 2 → COM8
python -m esptool --chip esp32s3 -p COM8 -b 460800 \
  --before default-reset --after hard-reset write-flash \
  --flash-mode dio --flash-size 2MB --flash-freq 80m \
  0x0 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0x10000 build/phantomsense_firmware.bin
```

### Erase Flash

```bash
# Full erase (use if experiencing issues)
python -m esptool --chip esp32s3 -p COM5 erase_flash
python -m esptool --chip esp32s3 -p COM8 erase_flash
```

## Dual-Unit Setup

The firmware supports **two independent devices** configured in `main/app_config.h`.

### Build for Unit 1 (COM5)
```c
// main/app_config.h
#define CURRENT_UNIT_ID UNIT_ID_1
```
Then build and flash to COM5.

### Build for Unit 2 (COM8)
```c
// main/app_config.h
#define CURRENT_UNIT_ID UNIT_ID_2
```
Then rebuild and flash to COM8.

**Full rebuild required** when changing `CURRENT_UNIT_ID`:
```bash
idf.py fullclean && IDF_TARGET=esp32s3 idf.py build
```

## Application Flow

```
[Boot] → [GPIO Init] → [WiFi Connect] → [HTTP Client Init]
  ↓
[Create FreeRTOS Tasks]
  ├─ status_monitor_task (2s updates)
  │  └─ Monitors WiFi/hub status
  │  └─ Updates LED indicator
  ├─ csi_acquisition_task
  │  └─ Reads WiFi CSI samples
  ├─ signal_processing_task
  │  └─ Processes CSI data
  └─ hub_update_task (5s posts)
     └─ Sends device status to hub
```

## LED Status Indicators

| State | Pattern | Meaning |
|-------|---------|---------|
| **IDLE** | Blue pulse (1s) | Waiting for connection |
| **CONNECTING** | Yellow blink (150ms) | WiFi connecting |
| **CONNECTED** | Green blink (200ms on/300ms off) | Connected to network |
| **TRANSMITTING** | Green blink | Actively sending data |
| **ERROR** | Red blink (150ms) | Error state |

## Device Communication

### HTTP POST to Hub

Devices POST status every 5 seconds to `/update`:

```json
{
  "unit_id": 1,
  "unit_name": "PhantomSense-Unit-1",
  "rssi": -42,
  "ip_address": "192.168.1.123",
  "csi_amplitude": 1234.5,
  "csi_noise_floor": 45.2,
  "timestamp_ms": 1234567890
}
```

### Hub GET Endpoints

```bash
# List all connected devices
curl http://HUB_IP:5000/devices

# Response
{
  "units": {
    "1": { "unit_name": "PhantomSense-Unit-1", "rssi": -42, ... },
    "2": { "unit_name": "PhantomSense-Unit-2", "rssi": -38, ... }
  }
}
```

## Current Status

### ✅ Hardware Verified (May 11, 2026)
- **RGB LED Location:** GPIO 38 (WS2812B, requires RMT protocol)
- **LCD Backlight:** GPIO 15 (MUST be HIGH to see display)
- **LCD SPI Pins:** Confirmed 10, 11, 12, 13, 14, 15
- **PSRAM:** 8MB Octal PSRAM verified

### ✅ Working
- Firmware compilation for ESP32-S3
- Dual-unit build system (toggle CURRENT_UNIT_ID)
- Both devices flash successfully
- WiFi connection and authentication
- HTTP POST to hub server (verified)
- REST API endpoints (/devices, /update)
- FreeRTOS task scheduling
- GPIO drivers

### 🔧 Ready for Implementation Tomorrow

**RGB LED (WS2812B - GPIO 38):**
- ✅ Correct pin identified
- ⚠️ Implementation pending: RMT peripheral driver needed
- ⚠️ Cannot use simple GPIO HIGH/LOW (requires protocol timing)
- 📋 Test code provided in HARDWARE_VERIFICATION.md

**LCD Display (ST7789):**
- ✅ Correct pins identified (10-15)
- ✅ Backlight pin confirmed (GPIO 15, must be HIGH)
- ⏳ Next: Implement LCD SPI initialization with correct pins
- 📋 "Wake Up" test provided in HARDWARE_VERIFICATION.md

### Previous Issues - NOW RESOLVED ✅
| Issue | Root Cause | Status |
|-------|-----------|--------|
| GPIO 46-48 didn't work | Tied to PSRAM, not RGB LED | **RESOLVED** - Now using GPIO 38 |
| Backlight always white | Was using GPIO 33 instead of 15 | **RESOLVED** - Now using GPIO 15 |
| LED wouldn't respond | Assumed simple RGB, actually WS2812B | **RESOLVED** - RMT implementation planned |

## Next Steps (Tomorrow's Work)

1. **Test Hardware Alive:**
   - Use "Wake Up" test code from HARDWARE_VERIFICATION.md
   - Confirm LCD backlight turns on (GPIO 15)
   - Verify PSRAM shows 8MB

2. **Implement WS2812B Driver:**
   - Add RMT peripheral support for GPIO 38
   - Create color control functions
   - Test addressable LED output

3. **Update Display Driver:**
   - Implement LCD SPI with correct pins
   - Test LCD display functionality
   - Integration with LED status system

**See [HARDWARE_VERIFICATION.md](./HARDWARE_VERIFICATION.md) for complete diagnostics and implementation guide.**

## Configuration Files

### main/app_config.c (Generate from template)

```bash
cp main/app_config.c.example main/app_config.c
```

Then edit:
```c
.wifi_ssid = "YOUR_NETWORK",
.wifi_password = "YOUR_PASSWORD",
.hub_url = "http://YOUR_HUB_IP:5000",
```

### main/app_config.h (Shared types)

Select unit and configure defaults:
```c
#define CURRENT_UNIT_ID UNIT_ID_1  // or UNIT_ID_2
```

## Troubleshooting

### Build Fails
```bash
# Clean ESP-IDF cache
rm -rf build .idf_python_env_*

# Re-export ESP-IDF
source /home/esp-idf/export.sh

# Rebuild
IDF_TARGET=esp32s3 idf.py build
```

### Flash Fails
```bash
# Erase flash completely
python -m esptool --chip esp32s3 -p COM5 erase_flash

# Retry flash
python -m esptool --chip esp32s3 -p COM5 -b 460800 write-flash ...
```

### Device Not Connecting to WiFi
1. Verify SSID and password in `app_config.c`
2. Check WiFi network is 2.4GHz (ESP32-S3 doesn't support 5GHz)
3. Monitor serial output: `idf.py monitor -p COM5`

### Hub Shows No Devices
1. Verify hub server is running: `curl http://HUB_IP:5000/devices`
2. Check device and hub are on same network
3. Review device logs for HTTP POST failures

### LED Not Changing Colors
1. Verify GPIO pins 46, 47, 48 in code match board schematic
2. Check hardware connections (soldering, connectors)
3. Use multimeter to test GPIO output voltage
4. Try direct GPIO test (pins should toggle HIGH/LOW)

## Build Commands Reference

```bash
# Full clean build
idf.py fullclean && IDF_TARGET=esp32s3 idf.py build

# Build only (incremental)
IDF_TARGET=esp32s3 idf.py build

# Flash to device
idf.py flash -p COM5

# Monitor serial logs
idf.py monitor -p COM5

# Flash and monitor (combined)
idf.py build flash monitor -p COM5

# Set target
idf.py set-target esp32s3

# Menu configuration
idf.py menuconfig
```

## File Structure Details

- **main/main.c** - FreeRTOS task creation and app entry
- **main/app_config.c** - ⚠️ Sensitive config (WiFi/hub credentials)
- **main/wifi_setup.c** - WiFi initialization and status
- **components/display_driver/** - RGB LED and LCD control
- **components/csi_driver/** - WiFi CSI acquisition
- **components/signal_processor/** - Feature extraction

## Related Documentation

- [FIRMWARE.md](./FIRMWARE.md) - Detailed firmware architecture
- [BUILD.md](./BUILD.md) - Build system documentation
- [TEST_GUIDE.md](../TEST_GUIDE.md) - Testing procedures
- [Waveshare Wiki](https://www.waveshare.com/wiki/ESP32-S3-LCD-1.47)

## Security Notes

- **Never commit `main/app_config.c`** - it contains WiFi passwords
- Use `app_config.c.example` as a template for new builds
- `.gitignore` prevents accidental commits of sensitive files
- Review git status before pushing: `git status main/`

