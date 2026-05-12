"""
REST API - FastAPI endpoints for hub access
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..core.config import config
from ..core import hub_state, get_logger
from ..data_aggregator import data_aggregator
from ..llm_reasoning import llm_reasoner

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PhantomSense Hub API",
    description="Privacy-first WiFi-based activity tracking",
    version="1.0.0",
)


# ==================== Request/Response Models ====================

class ActivityData(BaseModel):
    """Activity classification data"""
    timestamp_ms: int
    activity_score: int
    rssi: int
    snr: float
    phase_velocity: float


class DeviceUpdateData(BaseModel):
    """Device data update from ESP32"""
    unit_id: int
    unit_name: str
    rssi: int
    ip_address: Optional[str] = None
    csi_amplitude: Optional[float] = None
    csi_noise_floor: Optional[float] = None
    timestamp_ms: int


class ReasoningResult(BaseModel):
    """LLM reasoning result"""
    unit_id: str
    timestamp: str
    reasoning: str
    confidence: int
    activity_summary: str


class UnitStatus(BaseModel):
    """Sensor unit status"""
    unit_id: str
    status: str
    last_seen: float
    activity_count: int
    latest_score: int


class SystemReport(BaseModel):
    """System-wide aggregated report"""
    timestamp: str
    units_active: int
    total_activities: int
    total_csi_frames: int


# ==================== Endpoints ====================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "hub_running": hub_state.is_running,
        "ollama_available": llm_reasoner.is_available,
        "mqtt_connected": True,  # TODO: Connect to actual MQTT state
    }


@app.get("/status", tags=["System"])
async def get_system_status():
    """Get system status"""
    status = await hub_state.get_system_status()
    
    return {
        **status,
        "ollama_available": llm_reasoner.is_available,
        "aggregator_stats": data_aggregator.stats,
    }


@app.get("/units", tags=["Units"])
async def list_units():
    """List all active sensor units"""
    
    units = []
    for unit_id, info in hub_state.units.items():
        units.append({
            "unit_id": unit_id,
            "status": info.get("status"),
            "last_seen": info.get("last_seen"),
        })
    
    return {"units": units, "count": len(units)}


@app.get("/units/{unit_id}", tags=["Units"])
async def get_unit_status(unit_id: str):
    """Get status of specific unit"""
    
    if unit_id not in hub_state.units:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    unit = hub_state.units[unit_id]
    activities = [a for a in hub_state.activity_buffer if a.get('unit_id') == unit_id]
    
    return {
        "unit_id": unit_id,
        "status": unit.get("status"),
        "last_seen": unit.get("last_seen"),
        "activity_count": len(activities),
        "latest_activity": activities[-1] if activities else None,
    }


@app.get("/timeline/{unit_id}", tags=["Data"])
async def get_activity_timeline(unit_id: str, max_items: int = 50):
    """Get activity timeline for a unit"""
    
    if unit_id not in hub_state.units:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    timeline = await data_aggregator.get_timeline(unit_id, max_items)
    
    return {
        "unit_id": unit_id,
        "timeline": timeline,
        "count": len(timeline),
    }


@app.get("/reasoning/{unit_id}", tags=["LLM"])
async def get_unit_reasoning(unit_id: str):
    """Get LLM reasoning for a unit"""
    
    if unit_id not in hub_state.units:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    if not llm_reasoner.is_available:
        raise HTTPException(status_code=503, detail="Ollama not available")
    
    cached = llm_reasoner.reasoning_cache.get(unit_id)
    
    if not cached:
        return {"unit_id": unit_id, "reasoning": "No reasoning available yet"}
    
    return cached


@app.post("/reasoning/{unit_id}/analyze", tags=["LLM"])
async def trigger_reasoning(unit_id: str):
    """Trigger reasoning for a unit"""
    
    if unit_id not in hub_state.units:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    if not llm_reasoner.is_available:
        raise HTTPException(status_code=503, detail="Ollama not available")
    
    # Get recent activities
    activities = [a for a in hub_state.activity_buffer if a.get('unit_id') == unit_id][-10:]
    
    if not activities:
        return {"unit_id": unit_id, "error": "No activities to reason about"}
    
    result = await llm_reasoner.reason_about_activity(unit_id, activities)
    
    return result


@app.get("/report", tags=["Reporting"])
async def get_aggregated_report():
    """Get aggregated system report"""
    
    return await data_aggregator.get_aggregated_report()


@app.get("/patterns", tags=["Analysis"])
async def analyze_patterns(hours: int = 1):
    """Analyze activity patterns over time"""
    
    if not llm_reasoner.is_available:
        raise HTTPException(status_code=503, detail="Ollama not available")
    
    return await llm_reasoner.analyze_patterns(hours)


@app.get("/data/latest", tags=["Data"])
async def get_latest_data():
    """Get latest CSI data from all units"""
    
    return {
        "timestamp": datetime.now().isoformat(),
        "data": hub_state.latest_data,
    }


@app.get("/metrics", tags=["System"])
async def get_metrics():
    """Get performance metrics"""
    
    return {
        "aggregator_stats": data_aggregator.stats,
        "buffer_size": len(hub_state.activity_buffer),
        "active_units": len(hub_state.units),
        "cached_reasoning_results": len(llm_reasoner.reasoning_cache),
    }


# ==================== Device API Endpoints (for Desktop App) ====================

@app.get("/devices", tags=["Devices"])
async def get_all_devices():
    """Get status of all devices (for desktop app)"""
    units = {}
    
    for unit_id, unit_info in hub_state.units.items():
        activities = [a for a in hub_state.activity_buffer if a.get('unit_id') == unit_id]
        latest_activity = activities[-1] if activities else {"name": "Idle", "confidence": 0.0}
        latest_csi = unit_info.get("latest_csi", {"amplitude_mean": 0.0, "noise_floor": -80})
        
        units[unit_id] = {
            "unit_id": unit_id,
            "unit_name": unit_info.get("name", f"Unit-{unit_id}"),
            "connected": unit_info.get("status") == "connected",
            "ip_address": unit_info.get("ip_address", "N/A"),
            "rssi": unit_info.get("rssi", 0),
            "latest_csi": {
                "amplitude_mean": latest_csi.get("amplitude_mean", 0.0),
                "noise_floor": latest_csi.get("noise_floor", -80),
                "timestamp": latest_csi.get("timestamp", 0),
            },
            "latest_activity": {
                "name": latest_activity.get("name", "Unknown"),
                "confidence": latest_activity.get("confidence", 0.0),
                "timestamp": latest_activity.get("timestamp", 0),
            },
            "frame_count": len([f for f in hub_state.latest_data.get("frames", []) if f.get("unit_id") == unit_id]),
            "activity_count": len(activities),
        }
    
    return {
        "units": units,
        "count": len(units),
    }


@app.post("/update", tags=["Devices"])
async def update_device_data(data: DeviceUpdateData):
    """Receive data update from ESP32 device (HTTP POST from device)"""
    
    unit_id = str(data.unit_id)
    
    # Create or update unit in hub_state
    if unit_id not in hub_state.units:
        hub_state.units[unit_id] = {
            "name": data.unit_name,
            "status": "connected",
            "last_seen": datetime.now().timestamp(),
            "ip_address": data.ip_address,
        }
        logger.info(f"Registered new device: {unit_id} ({data.unit_name})")
    else:
        hub_state.units[unit_id]["status"] = "connected"
        hub_state.units[unit_id]["last_seen"] = datetime.now().timestamp()
        if data.ip_address:
            hub_state.units[unit_id]["ip_address"] = data.ip_address
    
    # Update RSSI and CSI data
    hub_state.units[unit_id]["rssi"] = data.rssi
    hub_state.units[unit_id]["latest_csi"] = {
        "amplitude_mean": data.csi_amplitude or 0.0,
        "noise_floor": data.csi_noise_floor or -80,
        "timestamp": data.timestamp_ms,
    }
    
    logger.debug(f"Updated device {unit_id}: RSSI={data.rssi}, CSI={data.csi_amplitude}")
    
    return {
        "status": "success",
        "unit_id": unit_id,
        "message": "Data received",
    }


@app.get("/devices/{unit_id}/stream", tags=["Devices"])
async def get_device_data_stream(unit_id: str):
    """Get current data stream for a device"""
    if unit_id not in hub_state.units:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    unit_info = hub_state.units[unit_id]
    activities = [a for a in hub_state.activity_buffer if a.get('unit_id') == unit_id]
    
    return {
        "unit_id": unit_id,
        "connected": unit_info.get("status") == "connected",
        "latest_csi": unit_info.get("latest_csi", {}),
        "recent_activities": activities[-10:] if activities else [],
        "last_update": unit_info.get("last_update", 0),
    }


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return {"error": exc.detail, "status_code": exc.status_code}


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {"error": "Internal server error", "status_code": 500}


# Startup/shutdown events

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("API server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("API server shutdown")


# Import datetime for response schemas
from datetime import datetime
