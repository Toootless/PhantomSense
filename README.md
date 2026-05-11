# PhantomSense 🛰️👤

**PhantomSense** is a privacy-first, "invisible" human tracking system. It utilizes **WiFi Channel State Information (CSI)** on the **ESP32-S3** to detect presence, posture, and movement without the use of cameras or microphones.

The system combines **Edge AI** for real-time signal classification and **Local LLMs** (via Ollama) for high-level contextual reasoning.

---

## 🚀 Overview
Traditional motion sensors (PIR) are binary and unreliable. Cameras are intrusive. **PhantomSense** fills the gap by treating WiFi signals as a "Software-Defined Radar."

### How it works:
1.  **Nodes:** Distributed ESP32-S3 units scan for subcarrier amplitude and phase disturbances caused by the human body.
2.  **Edge AI:** Local inference on the S3 classifies activities (Walking, Sitting, Falling) using TinyML.
3.  **LLM Reasoning:** Events are sent to Franklin hub where a Large Language Model interprets movement patterns into natural language insights.

### Quick Start

**Sensor Units Setup:**
```bash
cd firmware
./build.sh -u 1 -a fullbuild  # Build Unit 1
./build.sh -u 2 -a fullbuild  # Build Unit 2
```

**Basestation Hub Setup (Franklin):**
```bash
cd hub
./setup.sh  # Linux/Mac
# or
setup.bat   # Windows

python hub.py  # Start the hub
```

Access the hub at: `http://localhost:5000`

---

## 🛠️ Hardware Stack
- **Primary MCU:** [Waveshare ESP32-S3-LCD-1.47](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-1.47)
  - **Chip:** ESP32-S3-R8 (Dual-core LX7 @ 240MHz)
  - **Memory:** 8MB PSRAM (Critical for CSI data buffering)
  - **Sensors:** Onboard 6-axis IMU for motion-compensation in handheld units.
  - **Display:** 1.47" IPS LCD (320×172) for real-time signal visualization.
- **Protocol:** ESP-CSI (802.11n HT20)

## 🖥️ Basestation (Franklin)
- **Processor:** AMD Ryzen 9 8945HS (8 cores, 16 threads @ 4.0GHz)
- **Memory:** 96GB RAM
- **GPUs:**
  - NVIDIA RTX 3060 (12GB VRAM) - Primary LLM inference
  - AMD RX 7900 XTX (24GB VRAM) - Secondary/fallback inference
- **Storage:** 3.64TB SSD
- **OS:** Windows 11 / Ubuntu / macOS
- **Software:**
  - Python 3.10+ with AsyncIO
  - FastAPI REST server
  - Ollama LLM engine
  - MQTT broker (Mosquitto)

---

## 📂 Project Structure
- `/firmware`: ESP-IDF source code for CSI acquisition and signal processing (ESP32-S3)
  - CSI driver for 250Hz WiFi signal capture
  - Signal processing with feature extraction
  - Multi-unit configuration (Unit 1 & Unit 2)
  - MQTT connectivity for basestation communication
  
- `/hub`: Basestation hub running on Franklin (Ryzen 9, 96GB RAM, dual GPU)
  - FastAPI REST server for data access
  - MQTT bridge for sensor communication
  - Ollama LLM integration for activity reasoning
  - Real-time data aggregation and buffering
  - GPU-accelerated inference (RTX 3060 + RX 7900 XTX)
  
- `/models`: TinyML training and inference models
  - Activity classification (walking, sitting, falling)
  - Model conversion for ESP32-S3 deployment
  
- `/hardware`: 3D printable enclosures and mounting designs
  - Handheld sensor units
  - Room-mounted fixed nodes
  - Antenna positioning fixtures
- `/docs`: Technical documentation and design notes.

---

## 📈 System Architecture
1. **Signal Layer:** WiFi CSI raw data extraction at 250Hz.
2. **Feature Layer:** Noise filtering (Sliding Median) and Phase Calibration.
3. **Inference Layer:** CNN-based classification running on S3 Vector Instructions.
4. **Logic Layer:** MQTT reporting to a local LLM for "Human-in-the-loop" summaries.

---

## 🚧 Development Status
- [x] Hardware Selection (ESP32-S3-R8)
- [x] CSI Data Acquisition Firmware (250Hz, 48 subcarriers)
- [x] Signal Processing & Feature Extraction
- [x] Multi-Unit Sensor Configuration
- [x] Basestation Hub Architecture (Franklin)
- [x] MQTT Bridge & Real-time Aggregation
- [x] Ollama LLM Integration
- [x] REST API Endpoints
- [ ] TinyML Model Training & Deployment
- [ ] Web Dashboard
- [ ] Long-term Data Storage (PostgreSQL)
- [ ] Mesh Networking Between Units
- [ ] Mobile App Interface
- [ ] Over-the-air Firmware Updates

---

## 🤝 Collaboration
This project is an open exploration into privacy-preserving ambient intelligence. 
**Maintainer:** [Toootless](https://github.com/Toootless)

## 📚 Documentation

- **[Firmware Guide](firmware/FIRMWARE.md)** - ESP32-S3 sensor firmware setup
- **[Firmware Build](firmware/BUILD.md)** - Build and deployment instructions
- **[Hub Guide](hub/HUB_README.md)** - Basestation hub on Franklin
- **[Project Architecture](docs/ARCHITECTURE.md)** - System design and data flow
