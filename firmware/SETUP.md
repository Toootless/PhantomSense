# PhantomSense Firmware - Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/YOUR_ORG/PhantomSense.git
cd PhantomSense/firmware
```

## 2. Configure Credentials

```bash
# Copy the example configuration
cp main/app_config.c.example main/app_config.c

# Edit with YOUR credentials
code main/app_config.c
```

**Edit these values:**
```c
// Line 18-20
.wifi_ssid = "YOUR_NETWORK_NAME",       // Your WiFi SSID
.wifi_password = "YOUR_PASSWORD",        // Your WiFi password

// Line 26
.hub_url = "http://192.168.1.100:5000",  // Your hub server IP
```

## 3. Install ESP-IDF (if not already installed)

### Windows/WSL Option (Recommended)

```bash
# In WSL
sudo apt-get update
sudo apt-get install -y git wget flex bison gperf python3 python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0

# Install ESP-IDF
mkdir -p ~
cd ~
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
source export.sh
```

### macOS
```bash
brew install cmake ninja dfu-util libusb
git clone --recursive https://github.com/espressif/esp-idf.git ~/esp-idf
cd ~/esp-idf
./install.sh esp32s3
source export.sh
```

### Linux
```bash
# Follow WSL instructions above
```

## 4. Build Firmware

```bash
cd ~/PhantomSense/firmware

# Set up ESP-IDF environment (do this each terminal session)
source /home/esp-idf/export.sh  # WSL/Linux
# or
export IDF_PATH=~/esp-idf       # macOS
source ~/esp-idf/export.sh

# Build for target
IDF_TARGET=esp32s3 idf.py build
```

**Output:** `build/phantomsense_firmware.bin` (~530KB)

## 5. Flash to Device

### Identify USB Port

```bash
# List serial ports
# Windows: Check Device Manager or use:
# powershell: Get-SerialPort

# Linux/macOS:
ls /dev/ttyUSB* /dev/ttyACM*
```

### Flash Commands

**Unit 1 (COM5 on Windows, /dev/ttyUSB0 on Linux):**
```bash
python -m esptool --chip esp32s3 -p COM5 -b 460800 \
  --before default-reset --after hard-reset write-flash \
  --flash-mode dio --flash-size 2MB --flash-freq 80m \
  0x0 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0x10000 build/phantomsense_firmware.bin
```

**Unit 2 (COM8 on Windows):**
```bash
# First, update main/app_config.h:
# #define CURRENT_UNIT_ID UNIT_ID_2

# Rebuild
IDF_TARGET=esp32s3 idf.py fullclean && IDF_TARGET=esp32s3 idf.py build

# Then flash
python -m esptool --chip esp32s3 -p COM8 -b 460800 ...
```

## 6. Monitor Serial Output

```bash
idf.py monitor -p COM5
```

**Expected output:**
```
I (123) wifi: WiFi connection established
I (456) HTTP: POST /update successful
I (789) DISPLAY: LED: GREEN
```

Press `Ctrl+]` to exit.

## 7. Verify Hub Connection

```bash
# Test hub API (from another terminal)
curl http://192.168.1.100:5000/devices

# Expected output:
# {"units": {"1": {"unit_name": "PhantomSense-Unit-1", ...}}}
```

## Troubleshooting

### Build fails: "esp_idf not found"
```bash
source /home/esp-idf/export.sh
```

### Flash fails: Permission denied
```bash
# Linux/WSL: Add user to dialout group
sudo usermod -a -G dialout $USER
newgrp dialout
```

### Device not connecting to WiFi
1. Check SSID/password in `app_config.c`
2. Ensure WiFi is **2.4GHz** (ESP32-S3 limitation)
3. Look at serial logs: `idf.py monitor`

### No devices showing in hub
- Verify hub is running: `curl http://HUB_IP:5000/devices`
- Check both devices are on same network
- Review device logs for HTTP errors

## Next Steps

1. ✅ **Setup complete** - You can now build and flash!
2. 📱 **Configure Desktop App** - See `/hub/README.md`
3. 🧪 **Run Tests** - See `TEST_GUIDE.md`
4. 🔬 **Debug Hardware** - See `README.md` "Hardware Diagnostics"

## Repository Security

⚠️ **IMPORTANT:** Your WiFi credentials are in `main/app_config.c`, which is **NOT tracked by git**.

```bash
# Verify git ignores your config
git status main/app_config.c
# Output: On branch main
#         nothing to commit, working tree clean
```

Never manually add `main/app_config.c` to git:
```bash
# WRONG - DO NOT DO THIS
git add main/app_config.c
git commit -m "Add config"

# OK - Always use the example
git add main/app_config.c.example
git commit -m "Update config template"
```

## Development Workflow

```bash
# Make changes
code main/main.c

# Rebuild
idf.py build

# Flash and monitor
idf.py build flash monitor -p COM5

# Stop monitoring: Ctrl+]
```

## File Protection

Your `app_config.c` is protected by:
- `.gitignore` - Prevents accidental commits
- `app_config.c.example` - Template for team collaboration
- This `SETUP.md` - Reminds you not to commit secrets

## Support

- 📖 Full docs: [README.md](./README.md)
- 🔧 Build details: [BUILD.md](./BUILD.md)
- 🧪 Testing: [TEST_GUIDE.md](../TEST_GUIDE.md)
- 🎯 Architecture: [FIRMWARE.md](./FIRMWARE.md)
- 📡 Hub docs: [../hub/README.md](../hub/README.md)
