# Heartbeat Test - Expected Output & Troubleshooting

## ✅ Successful Test Output

When you run the heartbeat test and everything works correctly, you should see output like this in the serial monitor:

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
I (7089) PhantomSense_Test: Heartbeat [3] - System Ready ✓
```

### What This Means:
- ✓ Device boots correctly
- ✓ 8MB PSRAM detected and working
- ✓ FreeRTOS scheduler running
- ✓ Logging system functional
- ✓ Heartbeat every ~2 seconds (2000ms)
- ✓ **Device is ready for CSI firmware deployment**

---

## ⚠️ Common Issues & Solutions

### Issue 1: "✗ PSRAM NOT FOUND!"

```
I (0) cpu_start: Starting scheduler on CPU0
I (40) PhantomSense_Test: ✗ PSRAM NOT FOUND! Check Octal RAM settings in menuconfig.
```

**Cause:** Octal RAM not enabled in firmware configuration.

**Solution:**
1. In VS Code, press `Ctrl + Shift + P`
2. Type: `ESP-IDF: SDK Configuration Editor`
3. Search for: **PSRAM** or **Octal RAM**
4. Enable:
   - ☑ **PSRAM (Octal RAM)** 
   - ☑ **Use Maximum PSRAM Memory**
5. Save (Ctrl+S) and exit
6. Clean project: `idf.py fullclean`
7. Rebuild and flash

---

### Issue 2: "✗ PSRAM write/read test failed"

```
I (51) PhantomSense_Test: ✓ PSRAM allocation successful
I (56) PhantomSense_Test: ✗ PSRAM write/read test failed
```

**Cause:** PSRAM memory corruption or defective chip.

**Solution:**
1. **Try different PSRAM configuration:**
   - In menuconfig: **Component Config → PSRAM**
   - Try different clock speeds (40MHz, 80MHz)
   - Test without cache
2. **Power cycle the device** - Hold RST for 2 seconds
3. **Check connections** - Reseat the board and USB cable
4. **Try a different USB port** - USB 2.0 vs 3.0 can matter

---

### Issue 3: Serial Monitor Shows Garbage

```
ÌEðEüŸEŒ•EÖê'þĄ
²žE­™EØŽEüð…}...
```

**Cause:** Baud rate mismatch.

**Solution:**
1. In VS Code serial monitor, find baud rate selector (usually bottom right)
2. Set to **115200** baud
3. Reset the device (press RST button)

---

### Issue 4: "Device or resource busy"

```
Error: Cannot open port /dev/ttyACM0 - [Errno 13]
```

**Cause:** Port already in use (old monitor still running).

**Solution:**
```bash
# Kill any existing serial connections
pkill -f "ttyACM0"
pkill -f "miniterm"

# Or close VS Code serial monitor first
```

---

### Issue 5: No Serial Output at All

**Checklist:**
- ☐ USB cable is **data cable** (not just charging)
- ☐ LED on board lights up (board is powered)
- ☐ Device appears in port list (`/dev/ttyACM0` or similar)
- ☐ Try different USB port
- ☐ Check device driver:
  - **Windows:** Device Manager → COM Ports
  - **Linux:** `lsusb` should show `1a86:7523` (CH340) or `10c4:ea60` (CP2102)

---

### Issue 6: Build Fails with "Error: Please check env python in idf_tools.env"

**Solution:**
```bash
# Reset IDF environment
idf.py clean
idf.py fullclean

# Or reconfigure extension
# VS Code: Ctrl+Shift+P → ESP-IDF: Configure ESP-IDF Extension
# Select: Express Install
```

---

### Issue 7: Compilation Errors (e.g., "undefined reference")

**Solution:**
1. Make sure you're using the right main.c:
   ```bash
   # Check which main.c is being used
   cat firmware/main/main.c | head -20
   
   # Should start with #include <stdio.h>
   ```

2. Verify CMakeLists.txt includes the file:
   ```bash
   grep "main.c" firmware/main/CMakeLists.txt
   ```

3. Clean and rebuild:
   ```bash
   idf.py fullclean
   idf.py build
   ```

---

## 📊 Performance Checklist After Successful Test

Once heartbeat is running smoothly, verify:

- ✅ Heartbeat counter increments every 2 seconds
- ✅ No error messages or warnings
- ✅ Consistent output (no crashes or reboots)
- ✅ CPU stable at 240MHz
- ✅ PSRAM allocated and functional
- ✅ Can restart monitor without issues

**If all checks pass**, you're ready to:
1. Swap in the real `main.c` (CSI firmware)
2. Build and flash Unit 1
3. Build and flash Unit 2

---

## 🔍 Advanced Diagnostics

### Check Memory Layout

```bash
# In VS Code terminal (firmware directory)
idf.py size
```

Expected output:
```
Total sizes:
DROM   : [==  ] 27.2% (used 1789476 / available 6553600)
IRAM   : [    ] 7.6% (used 39884 / available 514976)
Flash  : [==  ] 30.8% (used 2009109 / available 6510651)
Total  : [==  ] 25.9% (used 3838469 / available 14779227)
```

### Monitor CPU & Memory

```bash
# After monitoring starts, press Ctrl+T then Ctrl+D to enter internal CLI
# View memory: mem_print
# View tasks: tasks

# Or use tools like:
idf.py monitor --decode-coredump
```

### Reset to Factory Defaults

```bash
# Erase all flash memory
idf.py erase-flash

# Then rebuild and flash fresh
idf.py build
idf.py flash
```

---

## 🎯 Next Steps

### After Successful Heartbeat Test:

1. **Prepare for CSI Firmware**
   ```bash
   cd firmware
   cp main/main_heartbeat_test.c main/main_heartbeat_test.c.backup
   # Restore original main.c for CSI firmware
   ```

2. **Build CSI Firmware**
   ```bash
   idf.py fullclean
   idf.py build
   ```

3. **Flash Unit 1**
   ```bash
   # Configure for Unit 1
   idf.py set-target esp32s3
   idf.py build
   idf.py -p /dev/ttyACM0 flash
   idf.py -p /dev/ttyACM0 monitor
   ```

4. **Flash Unit 2**
   ```bash
   # Edit config to UNIT_ID_2
   # Repeat flash process with second device on different USB port
   ```

---

## 📞 Getting Help

If you're still stuck after trying these solutions:

1. **Save the serial output** - Copy/paste full error from monitor
2. **Check logs**: VS Code Output panel (Ctrl+Shift+U)
3. **Run diagnostics**: `./diagnose.sh` in firmware directory
4. **ESP-IDF Forum**: https://esp32.com/
5. **Reference**: https://docs.espressif.com/projects/esp-idf/

---

**You've got this!** 🚀 The heartbeat test validates everything needed for PhantomSense to work.
