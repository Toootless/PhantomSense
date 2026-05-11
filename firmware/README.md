# Firmware - ESP32-S3 CSI Data Acquisition

This directory contains the ESP-IDF firmware for CSI (Channel State Information) acquisition and signal processing on the Waveshare ESP32-S3-LCD-1.47.

## Prerequisites
- ESP-IDF v5.0+
- ESP32-S3-R8 with 8MB PSRAM
- Waveshare ESP32-S3-LCD-1.47

## Features
- **CSI Data Acquisition:** Real-time WiFi subcarrier extraction at 250Hz
- **Signal Processing:** Phase calibration and noise filtering
- **TinyML Integration:** Edge AI for activity classification
- **Display Output:** Real-time visualization on onboard LCD
- **MQTT Reporting:** Send results to central hub

## Build & Flash
```bash
idf.py build
idf.py flash
idf.py monitor
```

## Configuration
Edit `sdkconfig` for:
- WiFi SSID and password
- CSI sampling rate
- Model inference parameters
- MQTT broker address

## Architecture
- `main/` - Application entry point and task scheduler
- `components/csi_driver/` - Low-level CSI acquisition
- `components/signal_processor/` - Filtering and feature extraction
- `components/inference/` - TinyML model loader and executor
- `components/display/` - LCD rendering functions
