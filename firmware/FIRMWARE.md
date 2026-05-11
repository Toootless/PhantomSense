# PhantomSense Sensor Units - Firmware Documentation

## Overview

This is the firmware for PhantomSense sensor units running on **ESP32-S3-R8** microcontrollers. The system is designed to:

1. **Acquire WiFi CSI Data** - Capture channel state information at 250Hz
2. **Process Signals** - Apply filtering and feature extraction in real-time
3. **Classify Activities** - Use TinyML for edge inference (walking, sitting, falling, etc.)
4. **Report via MQTT** - Send results to the central basestation hub

## Multi-Unit Architecture

The firmware supports multiple sensor units in a single deployment:

- **Unit ID 1** - Primary unit (e.g., living room)
- **Unit ID 2** - Secondary unit (e.g., bedroom)
- **Extensible** - Add more units by extending `UNIT_ID` enum

Each unit:
- Has unique MQTT topic prefix
- Maintains independent CSI buffers
- Can be configured with different hyperparameters

## Hardware Requirements

- **Microcontroller:** Waveshare ESP32-S3-LCD-1.47
- **Chip:** ESP32-S3-R8 (240MHz dual-core, 8MB PSRAM)
- **Display:** 1.47" IPS LCD (320×172) for real-time visualization
- **Memory:** 8MB PSRAM is critical for CSI buffering
- **Antenna:** WiFi antenna (onboard)

## System Architecture

```
[CSI Driver]
    ↓
[WiFi Interface - 250Hz @ 48 subcarriers]
    ↓
[Signal Processor - Filtering & Feature Extraction]
    ↓
[Activity Classification - TinyML Model]
    ↓
[MQTT Publisher]
    ↓
[Central Hub - LLM Reasoning]
```

## Build & Deployment

### Setup ESP-IDF Environment

```bash
# Clone ESP-IDF
git clone https://github.com/espressif/esp-idf.git
cd esp-idf
git checkout release/v5.0
./install.sh

# Source the environment (do this in every terminal)
source ./export.sh
```

### Build for Unit 1

```bash
cd firmware

# Configure for Unit 1
sed -i 's/#define CURRENT_UNIT_ID.*/#define CURRENT_UNIT_ID UNIT_ID_1/' main/include/app_config.h

# Set target
idf.py set-target esp32s3

# Build
idf.py build

# Flash to device
idf.py flash

# Monitor output
idf.py monitor
```

### Build for Unit 2

```bash
cd firmware

# Configure for Unit 2
sed -i 's/#define CURRENT_UNIT_ID.*/#define CURRENT_UNIT_ID UNIT_ID_2/' main/include/app_config.h

# Rebuild
idf.py fullclean
idf.py build

# Flash to device (connect second ESP32-S3)
idf.py flash

# Monitor output
idf.py monitor
```

## Configuration Files

### `main/app_config.c` - Unit-specific configurations

Configure WiFi credentials, MQTT broker, and CSI parameters per unit:

```c
static unit_config_t unit_1_config = {
    .unit_id = UNIT_ID_1,
    .unit_name = "PhantomSense-Unit-1",
    .wifi = {
        .ssid = "YOUR_SSID",
        .password = "YOUR_PASSWORD",
        .max_retry = 5,
    },
    .mqtt = {
        .broker_uri = "mqtt://192.168.1.100:1883",
        .username = "phantomsense",
        .password = "phantom_pass",
        .topic_prefix = "/phantomsense/unit1",
        .keepalive = 60,
    },
    .csi = {
        .sampling_rate_hz = 250,
        .buffer_size = 2048,
        .enable_filter = 1,
    },
    .display_refresh_rate_ms = 100,
};
```

### `main/include/app_config.h` - Unit selection

Switch which unit to build for:

```c
#define CURRENT_UNIT_ID UNIT_ID_1  // Change to UNIT_ID_2 for second unit
```

## Components

### 1. **CSI Driver** (`components/csi_driver/`)
- WiFi CSI data acquisition
- 250Hz sampling rate
- Subcarrier extraction (48 subcarriers per frame)
- Circular buffer for frame queuing

**Key Functions:**
- `csi_driver_init()` - Initialize driver
- `csi_driver_start()` - Begin CSI acquisition
- `csi_driver_get_latest_frame()` - Retrieve frame from buffer

### 2. **Signal Processor** (`components/signal_processor/`)
- Noise filtering (median filter)
- Feature extraction
- Phase calibration
- Activity scoring

**Features Extracted:**
- `amplitude_mean` - Average amplitude across subcarriers
- `amplitude_std` - Standard deviation (variability)
- `amplitude_max` - Peak amplitude
- `phase_velocity` - Phase change rate
- `snr` - Signal-to-noise ratio
- `activity_score` - 0-1000 confidence in movement

### 3. **WiFi Setup** (`main/wifi_setup.c`)
- Station mode connection
- Automatic reconnection
- Event handling (connected, disconnected, got IP)

### 4. **MQTT Setup** (`main/mqtt_setup.c`)
- MQTT client initialization
- Topic publishing
- Connection management

## MQTT Topics

Each unit publishes to its configured prefix. Example for Unit 1:

```
/phantomsense/unit1/csi_data        ← Raw CSI statistics
/phantomsense/unit1/activity        ← Classification results
/phantomsense/unit1/status          ← System health
/phantomsense/unit1/stats           ← Performance metrics
```

### CSI Data Message Format

```json
{
  "timestamp_ms": 1234567890,
  "rssi": -45,
  "snr_db": 18.5,
  "amplitude_mean": 42.3,
  "amplitude_std": 8.7,
  "phase_velocity": 2.1,
  "activity_score": 567
}
```

## Task Scheduling

The firmware runs three main FreeRTOS tasks:

1. **Status Monitor** (Priority: +1)
   - Monitors WiFi and MQTT connections
   - Updates system status every 2 seconds

2. **CSI Acquisition** (Priority: +2)
   - Initializes CSI driver
   - Manages buffer

3. **Signal Processing** (Priority: +2)
   - Processes CSI frames
   - Publishes results via MQTT

## Debugging

### Serial Monitor

```bash
idf.py monitor
```

Expected output:
```
I (0) cpu_start: Starting scheduler on CPU0
I (245) MAIN: === PhantomSense Unit 1 Starting ===
I (245) WIFI_SETUP: WiFi Setup Starting
I (1023) WIFI_SETUP: got ip: 192.168.1.101
I (1025) MQTT_SETUP: MQTT Setup Starting
I (2045) MAIN: System Status: ✓ WiFi Connected | ✓ MQTT Connected
```

### Monitoring MQTT Messages

```bash
mosquitto_sub -h 192.168.1.100 -t "/phantomsense/unit1/#"
```

## Performance Specifications

| Metric | Value |
|--------|-------|
| CSI Sampling Rate | 250 Hz |
| Subcarriers | 48 (802.11n) |
| Feature Extraction Latency | ~15ms |
| MQTT Publish Rate | 10 Hz (configurable) |
| Memory Usage | ~3.5MB / 8MB PSRAM |
| Power Consumption | ~300mA @ 3.3V WiFi active |

## Next Steps

- [ ] Integrate TensorFlow Lite for activity classification
- [ ] Implement LCD visualization of CSI data
- [ ] Add over-the-air (OTA) firmware updates
- [ ] Mesh networking support for unit-to-unit communication
- [ ] Low-power modes for extended battery life

## Troubleshooting

**Issue:** WiFi connection fails
- Check SSID/password in `app_config.c`
- Ensure 2.4GHz network is available (5GHz not supported)
- Check signal strength (RSSI should be > -80 dBm)

**Issue:** CSI data not capturing
- Verify WiFi is connected
- Check that CSI is enabled in menuconfig
- Monitor serial for CSI events

**Issue:** MQTT connection fails
- Verify broker URI in `app_config.c`
- Ensure MQTT broker is running: `mosquitto -d`
- Check firewall allows port 1883

**Issue:** High memory usage
- Reduce `buffer_size` in CSI driver config
- Disable unused components

## References

- ESP-IDF Documentation: https://docs.espressif.com/projects/esp-idf/
- ESP32-S3 Datasheet: https://www.espressif.com/en/products/socs/esp32-s3
- WiFi CSI Guide: https://github.com/espressif/esp-idf/tree/master/examples/wifi/csi
- MQTT Protocol: https://mosquitto.org/man/mqtt-7.html
