# ESP-IDF Build Configuration for PhantomSense

## Prerequisites

Before building, ensure you have:

1. **ESP-IDF v5.0 or later** installed
   ```bash
   git clone https://github.com/espressif/esp-idf.git
   cd esp-idf
   git checkout release/v5.0
   ./install.sh
   source ./export.sh
   ```

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
        .ssid = "YOUR_SSID",
        .password = "YOUR_PASSWORD",
        .max_retry = 5,
    },
    .mqtt = {
        .broker_uri = "mqtt://192.168.1.X:1883",
        .username = "phantomsense",
        .password = "phantom_pass",
        .topic_prefix = "/phantomsense/unit1",
        .keepalive = 60,
    },
    // ... rest of config
};
```

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

## IDF menuconfig Options

Key settings in menuconfig:

- **Component Config → WiFi**
  - Enable WiFi
  - WiFi CSI (Channel State Information)

- **Component Config → MQTT**
  - Enable ESP-MQTT component
  - Configure broker URI (or use environment variable)

- **Partition Table**
  - Use `partitions/partitions.csv`
  - Flash size: 16MB (minimum for ESP32-S3-R8)

- **Compiler Options**
  - Optimization: `-O2` or `-Ofast` for edge inference

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

## MQTT Topics

Each unit publishes to its configured topic prefix:

- `/phantomsense/unit1/csi_data` - Raw CSI statistics
- `/phantomsense/unit1/activity` - Activity classification
- `/phantomsense/unit1/status` - System status
- `/phantomsense/unit1/stats` - Performance statistics

## Troubleshooting

### Build Fails
- Ensure `IDF_PATH` is set: `echo $IDF_PATH`
- Rebuild: `idf.py fullclean && idf.py build`

### Flash Connection Issues
- Check USB cable and port: `ls /dev/ttyUSB*` (Linux) or `COM?` (Windows)
- Reset device: Hold BOOT button while pressing RST

### CSI Data Not Captured
- Verify WiFi is connected to a 2.4GHz network (802.11n)
- Check RSSI is reasonable (not too weak)
- Monitor serial output for CSI events

## Next Steps

- [ ] Integrate TensorFlow Lite for activity classification
- [ ] Implement display rendering (LCD driver)
- [ ] Add over-the-air (OTA) update support
- [ ] Optimize memory usage for larger buffer sizes
