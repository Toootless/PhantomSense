# PhantomSense Heartbeat Test - Complete Setup Summary

**Status:** ✅ **Ready to Test**  
**Date Prepared:** May 11, 2026  
**Target:** ESP32-S3-R8 PSRAM and FreeRTOS Validation

---

## 📦 What's Been Prepared

### 1. Test Files (in `firmware/main/`)
- **main_heartbeat_test.c** - Complete heartbeat test with:
  - PSRAM detection and size reporting
  - PSRAM allocation test
  - PSRAM read/write validation
  - 2-second heartbeat counter loop
  - System info (CPU cores, clock frequency, chip revision)

### 2. Documentation Guides
| File | Purpose |
|------|---------|
| `QUICK_TEST.md` | 60-second quick start guide |
| `VSCODE_QUICK_START.md` | Detailed VS Code step-by-step |
| `TEST_GUIDE.md` | Expected outputs + troubleshooting |
| `firmware/BUILD.md` | Original build instructions |
| `firmware/FIRMWARE.md` | Architecture documentation |

### 3. Helper Scripts (in `firmware/`)
- **setup_wsl.sh** - Configure WSL environment
- **diagnose.sh** - Verify ESP-IDF setup

---

## 🎯 What This Test Validates

✅ **PSRAM (8MB)** - Critical for CSI buffer storage  
✅ **FreeRTOS** - Real-time task scheduler  
✅ **Serial Communication** - USB connection working  
✅ **ESP32-S3 Hardware** - Chip is functional  
✅ **Build System** - ESP-IDF compilation works  
✅ **Logging Framework** - Debug output functional  

**If test passes → Device is ready for CSI firmware**

---

## 🚀 Quick Start (3 Steps)

### Step 1: Set Target
```bash
VS Code: Ctrl+Shift+P → "ESP-IDF: Set Espressif Device Target" → esp32s3
```

### Step 2: Use Test Code
```bash
Copy firmware/main/main_heartbeat_test.c → firmware/main/main.c
```

### Step 3: Build & Flash
```bash
Click ⚡ Flame icon at bottom of VS Code
Select port: /dev/ttyACM0
```

---

## ✨ Expected Success Output

```
I (40) PhantomSense_Test: ✓ PSRAM Found: 8 MB
I (51) PhantomSense_Test: ✓ PSRAM allocation successful
I (56) PhantomSense_Test: ✓ PSRAM write/read test passed

I (86) PhantomSense_Test: Heartbeat [0] - System Ready ✓
I (3087) PhantomSense_Test: Heartbeat [1] - System Ready ✓
I (5088) PhantomSense_Test: Heartbeat [2] - System Ready ✓
```

**Heartbeat increments every ~2 seconds = ✅ SUCCESS**

---

## 📊 Files Location Reference

```
C:\Users\johnj\OneDrive\Documents\VS_projects\PhantomSense\
├── QUICK_TEST.md                      ← Start here for 60-second walkthrough
├── TEST_PREPARATION_COMPLETE.md       ← You are here
├── firmware/
│   ├── main/
│   │   ├── main.c                     ← Original (will replace with test)
│   │   └── main_heartbeat_test.c      ← 👈 Copy this to main.c
│   ├── VSCODE_QUICK_START.md          ← Detailed guide with screenshots
│   ├── TEST_GUIDE.md                  ← Troubleshooting & expected outputs
│   ├── FIRMWARE.md                    ← Architecture documentation
│   ├── BUILD.md                       ← Build commands reference
│   ├── setup_wsl.sh                   ← WSL environment helper
│   └── diagnose.sh                    ← Diagnostics script
├── hub/
│   ├── hub.py                         ← Hub entry point (ready to run)
│   └── ...
└── docs/
    └── ARCHITECTURE.md                ← System design overview
```

---

## 🔄 After Successful Test

Once heartbeat test completes successfully with all checks passing:

### Phase 1: Unit 1 Firmware Build
```bash
cd firmware
idf.py fullclean
idf.py build
# Output: build/main/main.bin (Unit 1 firmware)
```

### Phase 2: Unit 2 Firmware Build
```bash
# Edit app_config.h: change CURRENT_UNIT_ID to 2
idf.py fullclean
idf.py build
# Output: build/main/main.bin (Unit 2 firmware)
```

### Phase 3: Flash Both Units
```bash
# Device 1 on /dev/ttyACM0
idf.py -p /dev/ttyACM0 flash

# Device 2 on /dev/ttyACM1 (or different USB port)
idf.py -p /dev/ttyACM1 flash
```

### Phase 4: Hub Integration
```bash
cd hub
python hub.py
# Ollama + MQTT aggregator running on Franklin
```

---

## 🎓 Project Architecture Reminder

```
Sensor Unit 1 (ESP32-S3)
    ↓ WiFi CSI 250Hz
Sensor Unit 2 (ESP32-S3)
    ↓ WiFi CSI 250Hz
    
MQTT Bridge (127.0.0.1:1883)
    ↓ JSON messages
    
Franklin Hub (AMD Ryzen 9, 96GB, dual GPU)
├── Data Aggregator (100ms loop)
├── LLM Reasoning (Ollama, 5s loop)
└── REST API (FastAPI, 5000)
    ↓ JSON endpoints
    
Client Applications (Visualization, Analysis)
```

---

## 📈 Performance Expectations

| Component | Expected Performance |
|-----------|---------------------|
| PSRAM | 8 MB allocated, 100+ MB/s throughput |
| CSI Sampling | 250 Hz (1 frame every 4ms) |
| MQTT Publish | <50ms latency to hub |
| Aggregation | 100ms batch processing |
| LLM Reasoning | 5-10s per analysis (Llama2 7B) |
| REST API Response | <200ms (p95) |

---

## 🛠️ Troubleshooting Quick Links

- **Port not found?** → Check `ls /dev/ttyACM*`
- **PSRAM error?** → See TEST_GUIDE.md "Issue 1"
- **Build fails?** → See TEST_GUIDE.md "Issue 6"
- **Garbage output?** → See TEST_GUIDE.md "Issue 3"
- **Device busy?** → See TEST_GUIDE.md "Issue 4"

---

## ✅ Verification Checklist

Before running test, verify:
- [ ] USB cable is data cable (not just power)
- [ ] Device LED lights up
- [ ] VS Code with ESP-IDF extension installed
- [ ] WSL or native Linux environment
- [ ] `idf.py --version` works in terminal
- [ ] `/dev/ttyACM0` appears when device connected

---

## 📞 Resources

- **Official ESP32-S3 Docs**: https://docs.espressif.com/projects/esp-idf/
- **PhantomSense GitHub**: https://github.com/Toootless/PhantomSense.git
- **Ollama Docs**: https://github.com/ollama/ollama
- **MQTT Protocol**: https://mqtt.org/
- **FastAPI**: https://fastapi.tiangolo.com/

---

## 🎉 You're Ready!

All tools, documentation, and code are prepared. The heartbeat test will validate your ESP32-S3 hardware and ESP-IDF environment in ~90 seconds.

**Next Step:** Open VS Code, follow QUICK_TEST.md, and hit that ⚡ Flame button!

---

*PhantomSense: Privacy-First WiFi CSI Human Activity Tracking System*  
*Version 1.0 | Ready for Field Deployment Testing*
