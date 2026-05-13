# No Data in GUI - Troubleshooting Guide

## Problem
Hub and GUI are running but no device data appears in the GUI metrics.

## Root Cause
**MQTT Broker is not running.** Without it, the ESP32 units cannot send CSI data to the hub.

The data flow is:
```
ESP32 Units (MQTT Publisher)
    ↓
Mosquitto MQTT Broker (127.0.0.1:1883)
    ↓
Hub MQTT Bridge (subscribes and aggregates)
    ↓
Hub REST API
    ↓
GUI (displays metrics)
```

## Solution

### Option A: Run Mock Data Generator (Testing Only)
This demonstrates the GUI works without real hardware:

```bash
cd C:\Users\johnj\OneDrive\Documents\VS_projects\PhantomSense\hub
.\venv\Scripts\python test_data_generator.py
```

This generates simulated activity data and prints to console. However, **the GUI won't update** because data isn't flowing through the hub.

### Option B: Set Up Real MQTT Broker (Required for Production)

#### Step 1: Install Mosquitto via WSL
Since Windows installation is problematic, use WSL Ubuntu:

```bash
# From PowerShell as Administrator:
wsl --set-default Ubuntu-24.04
wsl -d Ubuntu-24.04 -- bash -c "sudo apt update && sudo apt install -y mosquitto mosquitto-clients" 
```

#### Step 2: Start Mosquitto in WSL
```bash
# Run in WSL Ubuntu (in separate terminal):
wsl -d Ubuntu-24.04 -- mosquitto -d  # Start as daemon

# Or for debugging (see connection logs):
wsl -d Ubuntu-24.04 -- mosquitto -v  # Verbose mode
```

#### Step 3: Enable WSL Network Bridge (if needed)
If ESP32 units can't connect to mosquitto at 127.0.0.1:1883, they need the WSL IP:

```bash
# From WSL terminal:
hostname -I
# Example output: 172.28.224.1

# Update ESP32 configuration with this IP
# Edit: firmware/main/app_config.c or ESP32 web interface
```

#### Step 4: Power On and Configure ESP32 Units
1. Connect dual ESP32-S3 units via USB to Franklin workstation
2. Access ESP32 web config (default: http://esp32.local)
3. Set MQTT broker: `127.0.0.1:1883` (or WSL IP if using WSL)
4. Units should auto-connect and start streaming CSI data

#### Step 5: Verify Connection
```bash
# Check hub logs:
# Hub console should show:
# "Connecting to MQTT broker: 127.0.0.1:1883"
# "MQTT bridge connected"
# "Received CSI from ESP32-01" (repeating)

# Or use mosquitto_sub to monitor:
mosquitto_sub -h 127.0.0.1 -t "phantomsense/#"
```

## Current Status
✅ Hub running on port 5000
✅ GUI running and connected to hub
⏳ **Missing: MQTT broker** 
⏳ **Missing: ESP32 units connection**

## Quick Test Checklist

- [ ] Mosquitto is running (`mosquitto_sub -h 127.0.0.1 -t test` works)
- [ ] ESP32 units are powered on
- [ ] ESP32 units can reach MQTT broker IP (ping from device)
- [ ] Hub logs show "MQTT bridge connected"
- [ ] GUI shows unit names and real-time metrics

## Common Issues

### "Connection refused" on hub startup
→ Mosquitto is not running. Start it with WSL or Chocolatey.

### ESP32 units don't connect to MQTT
→ Check broker IP and port (default 127.0.0.1:1883)
→ If using WSL, broker might only be accessible via WSL IP (172.x.x.x)
→ Firewall might block connections on port 1883

### GUI shows units but metrics are zero
→ MQTT connection is active but units not streaming
→ Check ESP32 CSI sampling is enabled
→ Verify MQTT topic names match config

## Next Steps
1. **For testing**: Run `test_data_generator.py` (shows console output)
2. **For production**: Set up Mosquitto + connect ESP32 units
3. **For debugging**: Enable verbose logging in hub (`config.LOG_LEVEL = "DEBUG"`)

---

**Document updated**: May 13, 2026
**Applies to**: PhantomSense Hub v1.0 + PyQt6 GUI
