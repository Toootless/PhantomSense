# ESP-IDF Build Configuration for PhantomSense

## Prerequisites

Before building, ensure you have:

1. **ESP-IDF v6.0.1 or later** installed
   ```bash
   git clone https://github.com/espressif/esp-idf.git
   cd esp-idf
   git checkout release/v6.0
   ./install.sh
   source ./export.sh
   ```

   **Note:** Earlier versions (v5.0) will not compile due to API changes in HTTP event handling, GPIO component paths, and event handler signatures.

2. **ESP32-S3 Toolchain** installed via IDF

3. **ESP32-S3-LCD-1.47 Board Support** (may need custom board definition)

## Quick Start

### 1. Configure for Your Unit

Edit `main/app_config.c` and update the configuration for your unit:

```c
// For Unit 1:
static unit_config_t unit_1_config = {
    .unit_id = UNIT_ID_1,
    .unit_name = "PhantomSense-Unit-1",
    .wifi = {
        .ssid = "DrWho",                        // WiFi SSID
        .password = "Mollymay2212",            // WiFi password (GITIGNORED)
        .max_retry = 5,
    },
    .http = {
        .hub_url = "http://172.31.175.241:5000",  // Hub server URL (WSL bridge IP)
        .update_endpoint = "/update",
    },
    .csi = {
        .sampling_rate_hz = 250,
        .buffer_size = 2048,
        .enable_filter = 1,
    },
    .display_refresh_rate_ms = 100,
};
```

**⚠️ IMPORTANT:** The `app_config.c` file is git-ignored for security. Copy from `app_config.c.example` if needed.

### 2. Select Unit for Build

Edit `main/include/app_config.h`:

```c
// Change this based on which unit you're building for
#define CURRENT_UNIT_ID UNIT_ID_1  // or UNIT_ID_2
```

### 3. Build the Firmware

```bash
# Set IDF target
idf.py set-target esp32s3

# Configure the build
idf.py menuconfig

# Build
idf.py build
```

### 4. Flash to Device

```bash
# Connect USB cable to ESP32-S3

# Flash the firmware
idf.py flash

# Monitor serial output
idf.py monitor
```

## Build System Notes (ESP-IDF v6.0.1)

### Component Changes in v6.0.1

- **GPIO component:** Now requires explicit `esp_driver_gpio` in CMakeLists.txt (not `driver/gpio.h`)
- **HTTP event types:** Expanded with `HTTP_EVENT_ON_HEADERS_COMPLETE`, `HTTP_EVENT_ON_STATUS_CODE`
- **Event handler API:** Requires explicit `(void*)` cast for const pointers in `esp_event_handler_instance_register()`

All compatibility fixes are already applied in the codebase.

### IDF menuconfig Options

Key settings:

- **Component Config → WiFi**
  - Enable WiFi
  - ⚠️ CSI currently DISABLED pending v6.0.1 API fix

- **Partition Table**
  - Use `partitions/partitions.csv`
  - Flash size: 8MB (sufficient for firmware size ~932KB)

- **Compiler Options**
  - Optimization: `-O2` (default)
  - Stack size: 4096 bytes (sufficient for HTTP tasks)

## Multi-Unit Deployment

### For Unit 1:
```bash
sed -i 's/#define CURRENT_UNIT_ID.*/#define CURRENT_UNIT_ID UNIT_ID_1/' main/include/app_config.h
idf.py build
idf.py flash
```

### For Unit 2:
```bash
sed -i 's/#define CURRENT_UNIT_ID.*/#define CURRENT_UNIT_ID UNIT_ID_2/' main/include/app_config.h
idf.py build
idf.py flash
```

## Project Structure

```
firmware/
├── main/
│   ├── main.c              # Application entry point
│   ├── app_config.c        # Unit configurations
│   ├── wifi_setup.c        # WiFi initialization
│   ├── mqtt_setup.c        # MQTT client setup
│   └── include/
│       ├── app_config.h
│       ├── wifi_setup.h
│       └── mqtt_setup.h
├── components/
│   ├── csi_driver/         # WiFi CSI data acquisition
│   ├── signal_processor/   # Signal processing & feature extraction
│   ├── display_driver/     # LCD output (WIP)
│   ├── mqtt_client/        # MQTT utilities (WIP)
│   └── inference/          # TinyML inference (WIP)
└── partitions/
    └── partitions.csv      # Flash partition table
```

## Device-to-Hub Communication (HTTP)

Each device sends HTTP POST requests to the hub server every 5 seconds:

**Endpoint:** `POST /update`  
**Host:** Hub server (configured in app_config.c)  
**Port:** 5000 (default)  
**Interval:** 5 seconds

**Payload:**
```json
{
  "unit_id": 1,
  "unit_name": "PhantomSense-Unit-1",
  "rssi": -45,
  "ip_address": "192.168.1.100",
  "csi_amplitude": -50.0,
  "noise_floor": -80.0,
  "timestamp_ms": 1715507000000
}
```

**⚠️ Network Issue (Current):** WiFi devices cannot reach WSL hub IP. See DEPLOYMENT_STATUS.md for workaround.

## Troubleshooting

### Build Fails: "Could not find CMakeLists.txt"
- Ensure you're in `firmware/` directory: `cd firmware/`
- Rebuild: `idf.py fullclean && idf.py build`

### Build Fails: "esp_driver_gpio not found"
- **Cause:** ESP-IDF version mismatch (old v5.0 CMakeLists.txt)
- **Fix:** Update `components/display_driver/CMakeLists.txt` to use v6.0.1 component names
- Already fixed in current codebase

### Flash Connection Issues
- Check USB cable and port: `COM?` (Windows, run `mode`)
- Reset device: Hold BOOT button, press RST, then release BOOT
- Device should enumerate as USB-JTAG serial port

### HTTP POST Fails: "Connection failed: 32774"
- **Cause:** Device cannot reach hub IP from WiFi subnet (WSL routing issue)
- **Solution:** Enable Windows port forwarding (see DEPLOYMENT_STATUS.md)
- Temporarily logs "ESP_ERR_HTTP_CONNECT" to serial; device continues running

### Device WiFi Connects But Hub Reports 0 Units
- Verify hub is running: `curl http://172.31.175.241:5000/status`
- Monitor device serial output for HTTP POST attempts
- Check Windows firewall allows port 5000
- Apply netsh port forwarding workaround (DEPLOYMENT_STATUS.md)

## Known Issues

- **CSI Driver Disabled** (v6.0.1 compatibility pending)
  - esp_wifi_set_csi_config() returns ESP_FAIL
  - CSI frame capture not available until fixed
  - Status: Marked as TODO in main.c lines 248-251

- **WiFi-to-Hub Routing**
  - Devices cannot reach WSL internal IP from WiFi subnet
  - Workaround: Windows netsh port forwarding (DEPLOYMENT_STATUS.md)

## Next Steps

- [ ] Fix CSI driver for ESP-IDF v6.0.1
- [ ] Implement WS2812B RMT driver for RGB LED status
- [ ] Enable device-to-hub HTTP communication (fix routing)
- [ ] Restore MQTT integration for multi-broker scenarios
- [ ] Integrate TensorFlow Lite for activity classification
