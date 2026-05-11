# PhantomSense - Heartbeat Test Quick Start

## 🚀 Run Test in 60 Seconds

### Step 1: Open Project (30 seconds)
```
1. Open VS Code
2. File → Open Folder → C:\Users\johnj\OneDrive\Documents\VS_projects\PhantomSense
3. Trust the workspace
4. Wait for ESP-IDF extension to initialize
```

### Step 2: Set Target (15 seconds)
```
1. Press Ctrl + Shift + P
2. Type: ESP-IDF: Set Espressif Device Target
3. Select: esp32s3
4. Confirm: "✓ [esp32s3]" appears in status bar (bottom)
```

### Step 3: Use Heartbeat Test (10 seconds)
```
1. Open: firmware/main/main.c
2. Select ALL (Ctrl+A)
3. Delete current content
4. Open: firmware/main/main_heartbeat_test.c
5. Copy ALL (Ctrl+A, Ctrl+C)
6. Paste into main.c (Ctrl+V)
7. Save main.c (Ctrl+S)
```

### Step 4: Build & Flash (5 seconds)
```
1. Look at VS Code bottom status bar
2. Find and click the ⚡ FLAME icon (rightmost)
3. Select port: /dev/ttyACM0
4. Wait for build to complete (~30s)
5. Watch serial monitor output appear
```

### Expected Output ✓
```
✓ PSRAM Found: 8 MB
✓ PSRAM allocation successful
✓ PSRAM write/read test passed
Heartbeat [0] - System Ready ✓
Heartbeat [1] - System Ready ✓
Heartbeat [2] - System Ready ✓
```

---

## 🎯 Status Indicators

| Icon | Meaning |
|------|---------|
| ⚡ | Build + Flash + Monitor (use this!) |
| 🔨 | Build only |
| 🗑️ | Clean project |
| ⚙️ | Settings |
| 🟢 | OK / Ready |
| 🔴 | Error / Failed |

---

## 📋 Minimal Checklist

- [ ] Device connected via USB (LED lights up)
- [ ] Port /dev/ttyACM0 appears in device list
- [ ] Target set to esp32s3 in status bar
- [ ] main_heartbeat_test.c code in main.c
- [ ] Flame icon clicked
- [ ] Serial shows "PSRAM Found: 8 MB"
- [ ] Heartbeat counter incrementing
- [ ] No error messages in output

---

## 🆘 Instant Fixes

**"Command not found"**
→ Press Ctrl+Shift+P → "ESP-IDF: Configure" → "Express Install"

**"Device not found"**
→ Check USB port: `ls /dev/ttyACM*`

**"PSRAM NOT FOUND"**
→ Ctrl+Shift+P → "SDK Configuration Editor" → Enable Octal RAM

**"Garbage in serial"**
→ Set baud to 115200 in monitor

---

## 📖 Full Documentation

- `VSCODE_QUICK_START.md` - Complete VS Code walkthrough
- `TEST_GUIDE.md` - Troubleshooting & expected outputs
- `diagnose.sh` - Run diagnostics on your setup

---

**Ready?** Click that ⚡ and watch your PhantomSense device come to life! 🎉
