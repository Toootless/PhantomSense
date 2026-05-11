# Hub - Central Intelligence & LLM Reasoning

This directory contains the backend hub that aggregates sensor data from distributed ESP32-S3 nodes and interfaces with a local LLM (Ollama) for contextual reasoning.

## Components
- `mqtt_bridge.py` - MQTT subscriber for sensor events
- `llm_interface.py` - Integration with Ollama for natural language reasoning
- `data_aggregator.py` - Multi-node data fusion and timeline building
- `api_server.py` - REST API for querying results
- `requirements.txt` - Python dependencies

## Architecture
```
ESP32-S3 Nodes (MQTT) -> Hub (mqtt_bridge) -> LLM (Ollama) -> API
```

## Setup
```bash
pip install -r requirements.txt
ollama pull llama2  # or preferred model
python hub.py
```

## Environment Variables
- `MQTT_BROKER` - MQTT broker address (default: localhost:1883)
- `OLLAMA_HOST` - Ollama server address (default: http://localhost:11434)
- `HUB_PORT` - REST API port (default: 5000)

## API Endpoints
- `GET /health` - Health check
- `POST /event` - Receive sensor events
- `GET /timeline` - Query activity timeline
- `GET /summary` - Get LLM-generated summary
