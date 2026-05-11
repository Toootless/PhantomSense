# PhantomSense Hub - Basestation for Franklin

## Overview

**PhantomSense Hub** is the central intelligence processor for the WiFi-based activity tracking system. It runs on **Franklin** (Ryzen 9 8945HS, 96GB RAM, dual GPU) and provides:

- **Real-time MQTT aggregation** from distributed ESP32-S3 sensor units
- **GPU-accelerated LLM reasoning** using Ollama (Llama2 on RTX 3060 + Llama2 on RX 7900 XTX)
- **Activity pattern analysis** with contextual interpretation
- **REST API** for data access and control
- **Web dashboard** for visualization and monitoring

## Architecture

```
Sensor Units (MQTT)
    ↓↓↓ (250Hz CSI data)
┌─────────────────────────────────────┐
│   PhantomSense Hub (Franklin)       │
│                                     │
│  ┌────────────────────────────────┐ │
│  │  MQTT Bridge                   │ │
│  │  - Async client listener       │ │
│  │  - Topic routing               │ │
│  │  - Unit management             │ │
│  └────────────────────────────────┘ │
│                 ↓                    │
│  ┌────────────────────────────────┐ │
│  │  Data Aggregator               │ │
│  │  - CSI processing              │ │
│  │  - Activity buffering          │ │
│  │  - Real-time statistics        │ │
│  └────────────────────────────────┘ │
│                 ↓                    │
│  ┌────────────────────────────────┐ │
│  │  LLM Reasoning (Ollama)        │ │
│  │  - GPU acceleration (dual GPU) │ │
│  │  - Context analysis            │ │
│  │  - Pattern recognition         │ │
│  └────────────────────────────────┘ │
│                 ↓                    │
│  ┌────────────────────────────────┐ │
│  │  REST API (FastAPI)            │ │
│  │  - /status, /units, /timeline  │ │
│  │  - /reasoning, /patterns       │ │
│  │  - /report, /metrics           │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Requirements

### Hardware (Franklin)
- **CPU:** AMD Ryzen 9 8945HS (8 cores, 16 threads)
- **RAM:** 96GB (76GB available after OS)
- **GPU:** NVIDIA RTX 3060 (12GB) + AMD RX 7900 XTX (24GB)
- **Storage:** SSD with ≥100GB free
- **OS:** Windows 11, Ubuntu 22.04, or macOS 13+

### Software
- **Python:** 3.10 or later
- **MQTT Broker:** Mosquitto or similar (can run locally)
- **Ollama:** Latest version with Llama2 or Mistral models

## Installation

### 1. Setup Python Environment

```bash
# Navigate to hub directory
cd hub

# Create virtual environment
python -m venv venv

# Activate venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install MQTT Broker

**Windows (using Mosquitto):**
```bash
# Download and install from https://mosquitto.org/download/
# Or use Windows package manager
choco install mosquitto
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

**macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

### 3. Install Ollama

**Windows/Mac/Linux:**
1. Download from https://ollama.ai
2. Install and run Ollama
3. Pull models:
```bash
ollama pull llama2:7b-chat
ollama pull mistral:7b
```

### 4. Configure Hub

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# - MQTT broker address (default: localhost:1883)
# - Ollama host (default: http://localhost:11434)
# - API port (default: 5000)
```

## Usage

### Start the Hub

```bash
# From hub directory (with venv activated)
python hub.py
```

Expected output:
```
============================================================
PhantomSense Hub Starting (Franklin)
============================================================
Configuration:
  CPU: 8 cores @ 16 threads
  RAM: 76GB available
  GPU: ['cuda:0', 'rocm:0']
  MQTT Broker: 127.0.0.1:1883
  Ollama: http://localhost:11434
  API: http://0.0.0.0:5000
============================================================
All components initialized successfully
Hub is ready to receive sensor data
REST API listening on http://0.0.0.0:5000
Hub ready!
```

### Monitor Hub Status

```bash
# In another terminal
curl http://localhost:5000/health
```

### Connect Sensor Units

1. **Configure firmware** on ESP32-S3 units:
   - Edit `firmware/main/app_config.c`
   - Set MQTT broker to Franklin's IP: `mqtt://192.168.x.x:1883`
   - Set unit MQTT topics: `/phantomsense/unit1`, `/phantomsense/unit2`

2. **Build and flash** each unit:
```bash
cd firmware
./build.sh -u 1 -a fullbuild
./build.sh -u 2 -a fullbuild
```

3. **Verify connection**:
```bash
# Monitor MQTT messages
mosquitto_sub -h localhost -t "/phantomsense/#"
```

## REST API Endpoints

### System Health

- `GET /health` - Health check
- `GET /status` - System status
- `GET /metrics` - Performance metrics

### Units

- `GET /units` - List all active units
- `GET /units/{unit_id}` - Get specific unit status
- `GET /data/latest` - Latest CSI data from all units

### Activity Data

- `GET /timeline/{unit_id}` - Activity timeline
- `GET /timeline/{unit_id}?max_items=100` - Last 100 activities

### LLM Reasoning

- `GET /reasoning/{unit_id}` - Get cached reasoning
- `POST /reasoning/{unit_id}/analyze` - Trigger new reasoning
- `GET /patterns?hours=1` - Analyze patterns (last N hours)

### Reporting

- `GET /report` - Aggregated system report

## Example: Complete Workflow

```python
import asyncio
import httpx

async def example():
    async with httpx.AsyncClient() as client:
        # 1. Check hub status
        response = await client.get("http://localhost:5000/health")
        print("Hub Status:", response.json())
        
        # 2. List active units
        response = await client.get("http://localhost:5000/units")
        print("Active Units:", response.json())
        
        # 3. Get unit status
        response = await client.get("http://localhost:5000/units/unit1")
        print("Unit 1 Status:", response.json())
        
        # 4. Get activity timeline
        response = await client.get("http://localhost:5000/timeline/unit1?max_items=10")
        print("Unit 1 Timeline:", response.json())
        
        # 5. Trigger LLM reasoning
        response = await client.post("http://localhost:5000/reasoning/unit1/analyze")
        print("Reasoning Result:", response.json())
        
        # 6. Get pattern analysis
        response = await client.get("http://localhost:5000/patterns?hours=1")
        print("Pattern Analysis:", response.json())

asyncio.run(example())
```

## Performance Optimization for Franklin

### GPU Utilization

The hub automatically detects and uses both GPUs:

1. **NVIDIA RTX 3060** (Primary)
   - Ollama Llama2 inference
   - Fast token generation

2. **AMD RX 7900 XTX** (Secondary)
   - Alternative model fallback
   - Parallel inference if needed

**Monitor GPU usage:**
```bash
# NVIDIA
nvidia-smi -l 1

# AMD (if supported)
rocm-smi --watch
```

### Memory Management

- **Total RAM:** 96GB
- **Reserved for system:** 20GB
- **Available for hub:** 76GB
- **MQTT buffer:** ~10-20GB typical
- **LLM context:** ~15-20GB (depends on model)

### Async Processing

- **Worker threads:** 8 (matching CPU cores)
- **MQTT queue:** Async with backpressure
- **Data aggregation:** Every 100ms
- **Reasoning loop:** Every 5 seconds (non-blocking)

## Troubleshooting

### MQTT Connection Failed
```bash
# Check broker is running
mosquitto_sub -h localhost -t "#"

# If not running:
mosquitto -d  # Start mosquitto daemon
```

### Ollama Not Available
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### High Memory Usage
- Check number of buffered activities: `GET /metrics`
- Reduce `BUFFER_SIZE` in config
- Clear old data: Adjust `DATA_RETENTION_DAYS`

### Slow Reasoning
- Check GPU utilization
- Verify Ollama is using GPU: `ollama list`
- Reduce model size or use Mistral instead of Llama2

## Configuration Reference

See [config.py](phantomsense_hub/core/config.py) for all available settings:

```python
class FranklinConfig:
    CPU_CORES: int = 8
    RAM_GB: int = 96
    GPU_DEVICES: list = ["cuda:0", "rocm:0"]
    WORKER_THREADS: int = 8

class MQTTConfig:
    BROKER_HOST: str = "127.0.0.1"
    BROKER_PORT: int = 1883
    KEEPALIVE: int = 60

class OllamaConfig:
    OLLAMA_HOST: str = "http://localhost:11434"
    PRIMARY_MODEL: str = "llama2:7b-chat"
    GPU_LAYERS: int = 32
```

## Development

### Run Tests
```bash
pytest tests/ -v
```

### Type Checking
```bash
mypy phantomsense_hub/
```

### Code Formatting
```bash
black phantomsense_hub/
isort phantomsense_hub/
```

## Next Steps

- [ ] Implement web dashboard (React/Vue.js)
- [ ] Add data export (CSV, JSON)
- [ ] Setup long-term database storage (PostgreSQL)
- [ ] Implement push notifications for alerts
- [ ] Add multi-language support for reasoning
- [ ] Performance benchmarking and tuning
