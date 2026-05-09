# PhantomSense 🛰️👤

**PhantomSense** is a privacy-first, "invisible" human tracking system. It utilizes **WiFi Channel State Information (CSI)** on the **ESP32-S3** to detect presence, posture, and movement without the use of cameras or microphones.

The system combines **Edge AI** for real-time signal classification and **Local LLMs** (via Ollama) for high-level contextual reasoning.

---

## 🚀 Overview
Traditional motion sensors (PIR) are binary and unreliable. Cameras are intrusive. **PhantomSense** fills the gap by treating WiFi signals as a "Software-Defined Radar."

### How it works:
1.  **Nodes:** Distributed ESP32-S3 units scan for subcarrier amplitude and phase disturbances caused by the human body.
2.  **Edge AI:** Local inference on the S3 classifies activities (Walking, Sitting, Falling) using TinyML.
3.  **LLM Reasoning:** Events are sent to a central hub where a Large Language Model interprets movement patterns into natural language insights.

---

## 🛠️ Hardware Stack
- **Primary MCU:** [Waveshare ESP32-S3-LCD-1.47](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-1.47)
  - **Chip:** ESP32-S3-R8 (Dual-core LX7 @ 240MHz)
  - **Memory:** 8MB PSRAM (Critical for CSI data buffering)
  - **Sensors:** Onboard 6-axis IMU for motion-compensation in handheld units.
  - **Display:** 1.47" IPS LCD (320×172) for real-time signal visualization.
- **Protocol:** ESP-CSI (802.11n HT20)

---

## 📂 Project Structure
- `/firmware`: ESP-IDF source code for CSI acquisition and signal processing.
- `/models`: Pre-trained TinyML models for activity recognition.
- `/hub`: MQTT bridge logic for local LLM (Ollama) integration.
- `/hardware`: 3D printable enclosures for handheld and room-mounted units.
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
- [ ] CSI Data Acquisition Firmware
- [ ] TinyML Model Training
- [ ] Multi-Node Mesh Networking
- [ ] Local LLM Reasoning Bridge

---

## 🤝 Collaboration
This project is an open exploration into privacy-preserving ambient intelligence. 
**Maintainer:** [Toootless](https://github.com/Toootless)
