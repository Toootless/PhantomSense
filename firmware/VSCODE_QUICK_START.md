# ESP32-S3 Heartbeat Test - VS Code Setup Guide

## Quick Reference: Building & Flashing with VS Code

### Prerequisites
- **VS Code** with ESP-IDF extension installed
- **ESP-IDF tools** installed (managed by extension)
- **WSL** or native Linux/Windows environment
- **USB cable** connected to ESP32-S3 board
- **Device driver** installed (CH340 or similar)

---

## Step 1: Set the Target Device

1. Press **Ctrl + Shift + P** (open Command Palette)
2. Type: `ESP-IDF: Set Espressif Device Target`
3. Select **esp32s3** from the list
4. Choose **ESP32-S3** (Standard ESP32-S3 Chip)

**Expected:** VS Code status bar shows `[esp32s3]` at the bottom

---

## Step 2: Prepare the Test Code

The heartbeat test file is at: `firmware/main/main_heartbeat_test.c`

To use it, either:

### Option A: Replace current main.c (Temporary Test)
```bash
cd firmware
cp main/main_heartbeat_test.c main/main.c
```

### Option B: Symlink/Copy for VS Code
1. Open VS Code File Explorer
2. Navigate to `firmware/main/`
3. View `main_heartbeat_test.c`
4. Copy contents and paste into `main.c`

---

## Step 3: Configure Project

1. Press **Ctrl + Shift + P**
2. Type: `ESP-IDF: SDK Configuration Editor`
3. Look for these critical settings:

   **→ Compiler Options**
   - Optimization: `-O2` (recommended)
   
   **→ Component Config**
   - **PSRAM (Octal RAM)**
     - ✓ Enable Octal RAM Support
     - ✓ Use Maximum PSRAM Memory
   - **WiFi**
     - ✓ Enable WiFi
     - ✓ Enable WiFi CSI (if available)

4. **Save and Close**

---

## Step 4: Build the Project

Look at the **bottom status bar** of VS Code. You'll see a row of icons including:

- 🔨 Build icon (hammer) - Compiles code
- ⚡ Flame icon - Build, Flash & Monitor (all-in-one)
- 🗑️ Clean icon (trash)
- ⚙️ Settings icon

### Option A: Full Build + Flash + Monitor (Recommended for Testing)
**Click the ⚡ Flame icon** (rightmost icon, next to wrench)

### Option B: Build Only
**Click the 🔨 Hammer icon**

**Expected Output in Terminal:**
```
[1/5] Performing sanity check...
[2/5] Checking Python dependencies...
[3/5] Building targets
[4/5] Linking
[5/5] Creating binary files
Project build complete.
```

---

## Step 5: Flash & Monitor

### If you clicked the ⚡ Flame icon:
1. **Select Serial Port** when prompted
   - Default: `/dev/ttyACM0` (Linux/WSL)
   - Or: `COM3`, `COM4`, etc. (Windows)

2. **Automatic Flash & Monitor**
   - Code flashes to device
   - Serial monitor opens automatically
   - You should see output:

```
I (0) cpu_start: Starting scheduler on CPU0
I (31) esp_psram: This is Octal SPI PSRAM
I (31) esp_psram: octal psram init succeeded
I (40) PhantomSense_Test: ==========================================
I (41) PhantomSense_Test: PhantomSense Sensor Unit - Heartbeat Test
I (41) PhantomSense_Test: ==========================================
I (46) PhantomSense_Test: ✓ PSRAM Found: 8 MB
I (51) PhantomSense_Test: ✓ PSRAM allocation successful
I (56) PhantomSense_Test: ✓ PSRAM write/read test passed
I (61) PhantomSense_Test: 
I (61) PhantomSense_Test: System Status:
I (61) PhantomSense_Test: Chip: ESP32-S3-R8
I (66) PhantomSense_Test: CPU Cores: 2
I (71) PhantomSense_Test: CPU Frequency: 240 MHz
I (76) PhantomSense_Test: Revision: 0
I (81) PhantomSense_Test: 
I (81) PhantomSense_Test: Starting heartbeat loop...
I (86) PhantomSense_Test: 
I (86) PhantomSense_Test: Heartbeat [0] - System Ready ✓
I (3087) PhantomSense_Test: Heartbeat [1] - System Ready ✓
I (5088) PhantomSense_Test: Heartbeat [2] - System Ready ✓
```

### If you only did Build:
1. Click the **Flash** icon
2. Select port
3. Wait for flash to complete
4. Click **Monitor** icon to view serial output

---

## Troubleshooting

### "Command not found: idf.py"
**Solution:**
1. Press **Ctrl + Shift + P**
2. Type: `ESP-IDF: Configure ESP-IDF Extension`
3. Select **Express Install**
4. Wait for automatic setup
5. Try building again

### "Device not found / Port not available"
**Check connection:**
```bash
# Linux/WSL
ls /dev/ttyACM* /dev/ttyUSB*

# Windows PowerShell
Get-Content 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM' | ConvertFrom-StringData
```

**If no device:**
- Verify USB cable (data cable, not just power)
- Check device drivers (CH340, CP2102, etc.)
- Try different USB port
- Reset board: Hold BOOT, press RST, release BOOT

### "PSRAM NOT FOUND!"
**Solution:**
1. In menuconfig, enable:
   - **Component Config → PSRAM (Octal RAM)**
   - ✓ Enable Octal RAM Support
   - ✓ Use Maximum PSRAM Memory
2. Rebuild with `idf.py fullclean && idf.py build`

### Monitor shows garbage characters
**Fix baud rate:**
1. In monitor, press **Ctrl + T** then **Ctrl + A** to open menu
2. Set baud to `115200`
3. Or close and click the 🔧 settings to configure default

---

## VS Code Shortcuts

| Action | Shortcut |
|--------|----------|
| Command Palette | `Ctrl + Shift + P` |
| Toggle Terminal | `Ctrl + `` ` |
| Stop Monitor | `Ctrl + C` (in terminal) |
| Build | Click 🔨 |
| Flash + Monitor | Click ⚡ |
| Clean Project | Click 🗑️ |
| Settings | Click ⚙️ |

---

## What the Test Verifies

✅ **PSRAM Detection** - 8MB RAM accessible  
✅ **PSRAM Allocation** - Heap management working  
✅ **PSRAM Read/Write** - Data integrity OK  
✅ **FreeRTOS** - Scheduler running  
✅ **Logging** - Serial communication OK  
✅ **Clock** - CPU running at 240MHz  

**Next Steps After Successful Test:**
1. Swap `main_heartbeat_test.c` back to full `main.c`
2. Build the real CSI firmware
3. Flash to both Unit 1 and Unit 2

---

## Quick Commands (If Terminal Preferred)

```bash
# Navigate to firmware
cd firmware

# Set target
idf.py set-target esp32s3

# Configure (opens menuconfig)
idf.py menuconfig

# Build
idf.py build

# Flash (replace ttyACM0 with your port)
idf.py -p /dev/ttyACM0 flash

# Monitor
idf.py -p /dev/ttyACM0 monitor

# Build + Flash + Monitor
idf.py -p /dev/ttyACM0 build flash monitor
```

---

## Getting Help

If you're stuck:
1. **Check VS Code Output Panel** (`Ctrl + Shift + U`)
2. **View Extension Logs** - Right-click ESP-IDF extension → Extension Logs
3. **Full clean rebuild**: `idf.py fullclean && idf.py build`
4. **Check ESP-IDF documentation**: https://docs.espressif.com/projects/esp-idf/

---

**Ready? Click that ⚡ Flame icon and watch the magic happen!** ✨
