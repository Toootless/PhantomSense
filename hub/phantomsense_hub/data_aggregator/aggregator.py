"""
Data Aggregation Module for PhantomSense
Collects and processes CSI data from devices, feeds to LLM for analysis
"""

import asyncio
import logging
from typing import Dict, Any, List
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
CSI_BUFFER_SIZE = 100  # Keep last 100 CSI frames per unit
ANALYSIS_INTERVAL = 5  # Run LLM analysis every 5 seconds
MIN_SAMPLES_FOR_ANALYSIS = 5  # Need at least 5 samples before analysis


class DataBuffer:
    """Circular buffer for CSI data per unit"""
    
    def __init__(self, max_size=CSI_BUFFER_SIZE):
        self.data = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
    
    async def add(self, csi_data: Dict[str, Any], timestamp: float):
        """Add CSI sample to buffer"""
        async with self.lock:
            self.data.append(csi_data)
            self.timestamps.append(timestamp)
    
    async def get_latest_stats(self) -> Dict[str, Any]:
        """Get statistical summary of buffered data"""
        async with self.lock:
            if not self.data:
                return {}
            
            amplitudes = [d.get("amplitude_mean", d.get("csi_amplitude", 0)) for d in self.data]
            noise_floors = [d.get("noise_floor", d.get("csi_noise_floor", -80)) for d in self.data]
            
            return {
                "count": len(self.data),
                "amplitude_mean": sum(amplitudes) / len(amplitudes) if amplitudes else 0,
                "amplitude_max": max(amplitudes) if amplitudes else 0,
                "amplitude_min": min(amplitudes) if amplitudes else 0,
                "noise_floor_mean": sum(noise_floors) / len(noise_floors) if noise_floors else -80,
                "latest": self.data[-1] if self.data else {},
                "timestamp": self.timestamps[-1] if self.timestamps else 0
            }
    
    async def clear(self):
        """Clear buffer"""
        async with self.lock:
            self.data.clear()
            self.timestamps.clear()


class DataAggregator:
    """Aggregates CSI data and manages analysis pipeline"""
    
    def __init__(self):
        self.unit_buffers: Dict[str, DataBuffer] = {}
        self.latest_analysis: Dict[str, Dict] = {}
        self.analysis_tasks: List[asyncio.Task] = []
        
    async def add_csi_data(self, unit_id: str, unit_name: str, 
                          csi_data: Dict[str, Any]):
        """Add CSI data from a device"""
        
        # Create buffer for unit if needed
        if unit_id not in self.unit_buffers:
            self.unit_buffers[unit_id] = DataBuffer()
            logger.info(f"Created CSI buffer for {unit_name} ({unit_id})")
        
        # Add to buffer
        import time
        await self.unit_buffers[unit_id].add(csi_data, time.time())
    
    async def get_unit_analysis(self, unit_id: str) -> Dict[str, Any]:
        """Get latest LLM analysis for a unit"""
        return self.latest_analysis.get(unit_id, {
            "activity": "Waiting for data...",
            "confidence": 0.0,
            "reasoning": "Insufficient samples"
        })
    
    async def run_analysis_loop(self):
        """Background task: periodically analyze buffered data"""
        from ..llm_reasoning import llm_reasoner
        from ..core import hub_state
        
        logger.info("Starting data analysis loop")
        
        while True:
            try:
                # Analyze each unit's buffer
                for unit_id, buffer in self.unit_buffers.items():
                    stats = await buffer.get_latest_stats()
                    
                    if stats.get("count", 0) >= MIN_SAMPLES_FOR_ANALYSIS:
                        # Get unit name from hub state
                        unit_key = str(unit_id)
                        if unit_key in hub_state.units:
                            unit_name = hub_state.units[unit_key].get("name", f"Unit-{unit_id}")
                        else:
                            unit_name = f"Unit-{unit_id}"
                        
                        # Prepare activity data for reasoning
                        activities = [
                            {
                                "timestamp_ms": int(stats["timestamp"] * 1000),
                                "activity_score": 50,  # Placeholder
                                "rssi": -50,  # Placeholder from hub
                                "snr": stats["amplitude_mean"] - stats["noise_floor_mean"],
                                "phase_velocity": 0.0,  # Placeholder
                            }
                        ]
                        
                        # Run LLM analysis if available
                        if llm_reasoner.is_available:
                            analysis = await llm_reasoner.reason_about_activity(unit_id, activities)
                            
                            # Cache result
                            self.latest_analysis[unit_id] = {
                                "activity": analysis.get("activity_summary", "Unknown"),
                                "confidence": min(100, max(0, analysis.get("confidence", 50))) / 100.0,
                                "reasoning": analysis.get("reasoning", "")[:200]
                            }
                            
                            logger.debug(
                                f"{unit_name}: {self.latest_analysis[unit_id]['activity']} "
                                f"(confidence={self.latest_analysis[unit_id]['confidence']:.1%})"
                            )
                
                # Wait before next analysis cycle
                await asyncio.sleep(ANALYSIS_INTERVAL)
                
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
                await asyncio.sleep(1)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        stats = {}
        for unit_id, buffer in self.unit_buffers.items():
            buf_stats = await buffer.get_latest_stats()
            stats[unit_id] = buf_stats
        return stats


# Global aggregator instance
data_aggregator = DataAggregator()


async def initialize_aggregator() -> List[asyncio.Task]:
    """Initialize data aggregator and start background tasks"""
    logger.info("Initializing data aggregator")
    
    # Start analysis loop
    analysis_task = asyncio.create_task(data_aggregator.run_analysis_loop())
    data_aggregator.analysis_tasks.append(analysis_task)
    
    return [analysis_task]


async def shutdown_aggregator():
    """Shutdown data aggregator"""
    logger.info("Shutting down data aggregator")
    # Cancel analysis tasks
    for task in data_aggregator.analysis_tasks:
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
