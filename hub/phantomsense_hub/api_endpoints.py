"""
PhantomSense Hub REST API
Provides data endpoints for desktop and web clients
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Mock data structures
class CSIData(BaseModel):
    amplitude_mean: float = 0.0
    noise_floor: int = -80
    timestamp: int = 0

class ActivityData(BaseModel):
    name: str = "Unknown Activity"
    confidence: float = 0.0
    timestamp: int = 0

class UnitStatus(BaseModel):
    unit_id: str
    unit_name: str
    connected: bool
    ip_address: str = "N/A"
    rssi: int = 0
    latest_csi: CSIData = CSIData()
    latest_activity: ActivityData = ActivityData()
    frame_count: int = 0
    activity_count: int = 0

class HubStatus(BaseModel):
    units: Dict[str, UnitStatus]
    total_frames: int = 0
    total_activities: int = 0
    uptime_seconds: int = 0

# Global state (would be replaced with actual database)
hub_data = {
    "units": {
        "unit1": UnitStatus(
            unit_id="unit1",
            unit_name="PhantomSense-Unit-1",
            connected=False,
            latest_csi=CSIData(amplitude_mean=0.0),
            latest_activity=ActivityData(name="Idle"),
        ),
        "unit2": UnitStatus(
            unit_id="unit2",
            unit_name="PhantomSense-Unit-2",
            connected=False,
            latest_csi=CSIData(amplitude_mean=0.0),
            latest_activity=ActivityData(name="Idle"),
        ),
    },
    "total_frames": 0,
    "total_activities": 0,
}

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/devices")
async def get_devices() -> HubStatus:
    """Get status of all connected devices"""
    return HubStatus(**hub_data)


@router.get("/devices/{unit_id}")
async def get_device(unit_id: str) -> UnitStatus:
    """Get status of specific device"""
    if unit_id not in hub_data["units"]:
        raise HTTPException(status_code=404, detail="Unit not found")
    return hub_data["units"][unit_id]


@router.get("/devices/{unit_id}/csi")
async def get_csi_data(unit_id: str, limit: int = 100) -> Dict[str, Any]:
    """Get recent CSI data for device"""
    if unit_id not in hub_data["units"]:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    unit = hub_data["units"][unit_id]
    return {
        "unit_id": unit_id,
        "latest_csi": unit.latest_csi.dict(),
        "frame_count": unit.frame_count,
    }


@router.get("/devices/{unit_id}/activity")
async def get_activity_data(unit_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get recent activity classification results"""
    if unit_id not in hub_data["units"]:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    unit = hub_data["units"][unit_id]
    return {
        "unit_id": unit_id,
        "latest_activity": unit.latest_activity.dict(),
        "activity_count": unit.activity_count,
    }


@router.post("/devices/{unit_id}/update")
async def update_device(unit_id: str, data: Dict[str, Any]) -> Dict[str, str]:
    """Update device data (called by devices or MQTT bridge)"""
    if unit_id not in hub_data["units"]:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    unit = hub_data["units"][unit_id]
    
    # Update CSI data
    if "csi" in data:
        csi = data["csi"]
        unit.latest_csi = CSIData(
            amplitude_mean=csi.get("amplitude_mean", unit.latest_csi.amplitude_mean),
            noise_floor=csi.get("noise_floor", unit.latest_csi.noise_floor),
            timestamp=csi.get("timestamp", 0),
        )
        unit.frame_count += 1
        hub_data["total_frames"] += 1
    
    # Update activity data
    if "activity" in data:
        activity = data["activity"]
        unit.latest_activity = ActivityData(
            name=activity.get("name", "Unknown"),
            confidence=activity.get("confidence", 0.0),
            timestamp=activity.get("timestamp", 0),
        )
        unit.activity_count += 1
        hub_data["total_activities"] += 1
    
    # Update connection status
    if "connected" in data:
        unit.connected = data["connected"]
    
    if "ip_address" in data:
        unit.ip_address = data["ip_address"]
    
    if "rssi" in data:
        unit.rssi = data["rssi"]
    
    logger.info(f"Updated data for {unit_id}")
    
    return {"status": "success", "unit_id": unit_id}


@router.post("/update")
async def device_update(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Device update endpoint - receives data from ESP32 devices.
    Expects JSON with: unit_id, unit_name, rssi, ip_address, csi_amplitude, csi_noise_floor, timestamp_ms
    """
    unit_id = str(data.get("unit_id", "unit_unknown"))
    
    # Create unit if doesn't exist
    if unit_id not in hub_data["units"]:
        hub_data["units"][unit_id] = UnitStatus(
            unit_id=unit_id,
            unit_name=data.get("unit_name", f"Unit-{unit_id}"),
            connected=True,
            ip_address=data.get("ip_address", "N/A"),
        )
        logger.info(f"Registered new device: {unit_id}")
    
    # Update device info
    unit = hub_data["units"][unit_id]
    unit.connected = True
    unit.ip_address = data.get("ip_address", unit.ip_address)
    unit.rssi = data.get("rssi", unit.rssi)
    unit.unit_name = data.get("unit_name", unit.unit_name)
    
    # Update CSI data if provided
    if "csi_amplitude" in data or "csi_noise_floor" in data:
        unit.latest_csi = CSIData(
            amplitude_mean=data.get("csi_amplitude", unit.latest_csi.amplitude_mean),
            noise_floor=data.get("csi_noise_floor", unit.latest_csi.noise_floor),
            timestamp=data.get("timestamp_ms", 0),
        )
        unit.frame_count += 1
        hub_data["total_frames"] += 1
    
    logger.info(f"Device update from {unit_id} ({unit.unit_name}): RSSI={unit.rssi}, IP={unit.ip_address}")
    
    return {"status": "success", "unit_id": unit_id}


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "message": "PhantomSense Hub is running"}


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get overall hub statistics"""
    return {
        "total_frames": hub_data["total_frames"],
        "total_activities": hub_data["total_activities"],
        "connected_units": sum(1 for u in hub_data["units"].values() if u.connected),
        "total_units": len(hub_data["units"]),
    }
