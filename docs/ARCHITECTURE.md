# PhantomSense System Architecture

## High-Level Overview

PhantomSense is a privacy-first activity tracking system that uses WiFi Channel State Information (CSI) to detect and classify human activities without cameras or microphones.

## System Layers

### Layer 1: Sensor Nodes (ESP32-S3)

**Location:** Distributed around monitored space (e.g., living room, bedroom)  
**Quantity:** 2+ units  
**Function:** CSI data acquisition and edge inference

**Data Flow:**
```
WiFi Channel → CSI Extraction (250Hz) → Signal Processing → Activity Classification
                        ↓                        ↓                      ↓
                  48 subcarriers         Amplitude/Phase         Activity Score
                  Amplitude & Phase      Feature extraction      (0-1000)
                  RSSI, SNR              Noise filtering
                                        Phase calibration
```

**Key Specifications:**
- Sampling Rate: 250Hz per CSI frame
- Subcarriers: 48 (802.11n HT20)
- Output: Activity score, SNR, phase velocity
- Protocol: MQTT over WiFi
- Power: ~300mA @ 3.3V continuous

### Layer 2: Network Bridge (WiFi + MQTT)

**Protocol:** MQTT (Message Queueing Telemetry Transport)  
**QoS:** At-least-once delivery (QoS=1)  
**Topics:**
- `/phantomsense/unit1/csi_data` - Raw CSI statistics
- `/phantomsense/unit1/activity` - Activity classifications
- `/phantomsense/unit1/status` - Unit health
- `/phantomsense/inference/*` - Hub inference results
- `/phantomsense/reasoning/*` - LLM reasoning outputs

**Message Format (JSON):**
```json
{
  "timestamp_ms": 1234567890,
  "rssi": -45,
  "snr_db": 18.5,
  "amplitude_mean": 42.3,
  "amplitude_std": 8.7,
  "phase_velocity": 2.1,
  "activity_score": 567
}
```

### Layer 3: Basestation Hub (Franklin)

**Hardware:**
- Ryzen 9 8945HS (8 cores, 16 threads)
- 96GB RAM (76GB available)
- NVIDIA RTX 3060 (12GB)
- AMD RX 7900 XTX (24GB)

**Components:**

#### 3.1 MQTT Bridge
- Async MQTT client (aiomqtt)
- Topic subscription and routing
- Message buffering and flow control
- Auto-reconnection logic

**Responsibilities:**
- Connect to MQTT broker (local or remote)
- Subscribe to sensor topics
- Route messages to appropriate handlers
- Publish reasoning results back to sensors

#### 3.2 Data Aggregator
- Processes incoming CSI data
- Maintains activity buffers per unit
- Computes statistics and summaries
- Manages time-series data

**Processing Loop (100ms interval):**
1. Process raw CSI frames
2. Update per-unit statistics
3. Manage activity buffer (max 10,000 entries)
4. Generate aggregated reports

#### 3.3 LLM Reasoning Engine
- Ollama integration for local LLM inference
- GPU-accelerated (NVIDIA + AMD)
- Context-aware activity interpretation
- Pattern analysis and anomaly detection

**Models:**
- Primary: Llama2 7B Chat (12GB on RTX 3060)
- Secondary: Mistral 7B (backup on RX 7900 XTX)

**Processing:**
```
Activity History → LLM Prompt → Ollama Inference → Structured Reasoning
    ↓                  ↓             ↓                    ↓
Last 10 activities   Context +   GPU acceleration   Natural language
Per unit            temporal    + cache             interpretation
Timeline           signal
                   features
```

#### 3.4 REST API (FastAPI)
- Async HTTP endpoints
- Swagger/OpenAPI documentation
- Response caching
- Rate limiting

**Endpoint Categories:**
- System: `/health`, `/status`, `/metrics`
- Units: `/units`, `/units/{id}`
- Data: `/timeline/{id}`, `/data/latest`
- Reasoning: `/reasoning/{id}`, `/patterns`
- Admin: `/report`, `/health`

#### 3.5 Database (SQLite)
- Activity logs with timestamps
- Unit metadata
- Reasoning cache
- Statistics snapshots
- 30-day retention policy

### Layer 4: Client Applications

**Web Dashboard:**
- Real-time unit status
- Activity timelines
- LLM reasoning display
- Pattern visualization
- Alert notifications

**External APIs:**
- JSON REST interface
- Webhooks for events
- Time-series queries
- Export capabilities

## Data Flow Example

### Scenario: Detecting Morning Activity Pattern

**Time: 7:00 AM - Unit 1 in Bedroom**

```
1. CSI Acquisition (ESP32-S3 Unit 1)
   ├─ WiFi signal + human body disturbance
   ├─ Extract 48 subcarrier phases
   └─ Compute: amplitude_mean=52.3, activity_score=680

2. MQTT Publish (ESP32-S3 Unit 1)
   └─ Topic: /phantomsense/unit1/activity
   └─ Payload: {"timestamp_ms": 1234567890, "activity_score": 680, ...}

3. MQTT Subscribe (Franklin Hub)
   └─ Receive message on /phantomsense/unit1/activity

4. Data Aggregation (Hub)
   ├─ Add to unit1 activity buffer
   ├─ Update latest_data[unit1]
   └─ Mark unit1 as "active"

5. LLM Reasoning (Hub - every 5s)
   ├─ Collect last 10 activities from unit1
   ├─ Build context prompt:
   │   "Activity scores in last 5s: [680, 720, 690, 710, ...]"
   │   "Previous pattern: sleeping 00:00-07:00"
   │   "Current time: 7:00 AM"
   ├─ Send to Ollama (RTX 3060)
   └─ Receive: "High activity detected. Likely waking up. Human seems to be moving around."

6. REST API Response (Client Request)
   GET /reasoning/unit1
   ├─ Return cached reasoning result
   └─ Response: {"reasoning": "...", "confidence": 92, "activity_summary": "Waking up"}

7. Web Dashboard
   └─ Display: "Unit 1: Waking up (92% confidence)"
```

## Scalability

### Current Capacity (Franklin)
- **Sensor Units:** 2-10 units concurrently
- **Data Rate:** ~250Hz per unit = 500-2,500Hz total
- **Activity Buffer:** 10,000 entries ≈ 40 seconds @ 250Hz
- **LLM Inference:** 1-2 reasoning requests per unit every 5 seconds
- **API Requests:** Thousands per minute (async)

### Memory Usage
- **Base System:** 20GB (OS + services)
- **Hub Application:** 5-10GB (buffers, state)
- **Ollama Models:** 12-15GB (loaded models)
- **MQTT Queue:** 2-5GB (peak)
- **Reserved:** 20GB headroom
- **Total Used:** ~50-65GB of 96GB

### Future Scaling
- **More Sensor Units:** Add topic routing for unit0-unit99
- **Multi-Hub Setup:** Mesh network with primary/secondary hubs
- **Distributed LLM:** Ollama clusters for parallel inference
- **Cloud Integration:** Optional sync to cloud for ML training

## Security Considerations

### Current Implementation (Local)
- MQTT runs on local network (127.0.0.1:1883)
- No authentication required (local only)
- Ollama runs locally (no external API calls)
- All data stays on Franklin

### Production Recommendations
- Use strong MQTT credentials
- Enable TLS for MQTT (port 8883)
- Firewall MQTT broker
- SSH tunnel for remote access
- Rate limit REST API
- Implement API authentication

## Performance Characteristics

### Latency
| Component | Latency | Notes |
|-----------|---------|-------|
| CSI Capture → Processing | 4ms | Local edge processing |
| CSI → Activity Score | 15ms | TinyML model inference |
| MQTT Publish | 10-50ms | Network dependent |
| MQTT → Hub Processing | 5-20ms | Async routing |
| Activity → LLM Prompt | 100-500ms | Buffering for context |
| LLM Inference | 500-2000ms | Model generation |
| REST API Response | 10-100ms | Cached results |
| **Total End-to-End** | **1-3 seconds** | CSI → Reasoning visible |

### Throughput
- **CSI Frames:** 250 per unit per second (250Hz)
- **Activity Scores:** 1 per unit per second (aggregated)
- **MQTT Messages:** ~500-1000/sec total
- **LLM Requests:** 0.2-2 per unit per second (on-demand)
- **API Requests:** Unlimited (async)

### Resource Utilization (Typical)
- **CPU:** 20-30% average (mostly idle)
- **Memory:** 50-65GB
- **NVIDIA GPU:** 30-50% (LLM inference)
- **AMD GPU:** 0-5% (fallback only)
- **Network:** <10 Mbps (MQTT)

## Future Enhancements

### Planned Features
1. **Web Dashboard** - React-based visualization
2. **Mobile App** - iOS/Android remote access
3. **Cloud Sync** - Optional AWS/GCP integration
4. **Advanced Analytics** - Trend detection, anomalies
5. **Multi-Language LLM** - Support for non-English
6. **Mesh Networking** - Unit-to-unit communication
7. **OTA Updates** - Firmware updates over WiFi
8. **Custom Models** - Transfer learning for specific environments

### Long-Term Vision
- Privacy-by-design ambient intelligence
- Edge-first with optional cloud integration
- Open-source models and algorithms
- Community contributions and extensions
- Commercial deployment support
