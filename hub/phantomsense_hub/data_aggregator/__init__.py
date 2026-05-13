"""
Data Aggregator - Processes and aggregates sensor data from multiple units
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict

from ..core.config import config
from ..core import hub_state, get_logger
from ..llm_reasoning import llm_reasoner

logger = get_logger(__name__)


class DataAggregator:
    """Aggregates data from multiple sensor units"""
    
    def __init__(self):
        self.is_running = False
        self.aggregation_interval = config.AGGREGATION_INTERVAL_MS / 1000.0
        self.stats = {
            "total_csi_frames": 0,
            "total_activities": 0,
            "units_active": 0,
        }
    
    async def start(self):
        """Start data aggregation loop"""
        self.is_running = True
        logger.info(f"Starting data aggregator (interval: {config.AGGREGATION_INTERVAL_MS}ms)")
        
        aggregation_task = asyncio.create_task(self._aggregation_loop())
        reasoning_task = asyncio.create_task(self._reasoning_loop())
        
        return [aggregation_task, reasoning_task]
    
    async def stop(self):
        """Stop data aggregation"""
        self.is_running = False
        logger.info("Stopping data aggregator")
    
    async def _aggregation_loop(self):
        """Main aggregation loop"""
        try:
            while self.is_running:
                # Perform aggregation every interval
                await self._process_csi_data()
                await self._process_activities()
                await self._update_statistics()
                
                await asyncio.sleep(self.aggregation_interval)
                
        except asyncio.CancelledError:
            logger.info("Aggregation loop cancelled")
        except Exception as e:
            logger.error(f"Error in aggregation loop: {e}")
    
    async def _reasoning_loop(self):
        """Background reasoning loop"""
        try:
            while self.is_running:
                # Process reasoning every 5 seconds
                await asyncio.sleep(5.0)
                
                if not llm_reasoner.is_available:
                    continue
                
                # Trigger reasoning for each active unit
                for unit_id in hub_state.units.keys():
                    # Get last 10 activities for this unit
                    unit_activities = [
                        a for a in hub_state.activity_buffer[-10:]
                        if a.get('unit_id') == unit_id
                    ]
                    
                    if unit_activities:
                        await llm_reasoner.reason_about_activity(unit_id, unit_activities)
                
        except asyncio.CancelledError:
            logger.info("Reasoning loop cancelled")
        except Exception as e:
            logger.error(f"Error in reasoning loop: {e}")
    
    async def _process_csi_data(self):
        """Process raw CSI data"""
        
        for unit_id, data in hub_state.latest_data.items():
            try:
                # Extract features
                features = {
                    "amplitude_mean": data.get("amplitude_mean", 0),
                    "amplitude_std": data.get("amplitude_std", 0),
                    "snr": data.get("snr", 0),
                    "activity_score": data.get("activity_score", 0),
                }
                
                # Update statistics
                self.stats["total_csi_frames"] += 1
                
                logger.debug(f"Processed CSI from {unit_id}: score={features['activity_score']}")
                
            except Exception as e:
                logger.error(f"Error processing CSI from {unit_id}: {e}")
    
    async def _process_activities(self):
        """Process activity classifications"""
        
        if not hub_state.activity_buffer:
            return
        
        try:
            # Group activities by unit
            activities_by_unit = {}
            for activity in hub_state.activity_buffer:
                unit_id = activity.get("unit_id")
                if unit_id not in activities_by_unit:
                    activities_by_unit[unit_id] = []
                activities_by_unit[unit_id].append(activity)
            
            # Process each unit's activities
            for unit_id, activities in activities_by_unit.items():
                latest = activities[-1]
                
                # Update stats
                self.stats["total_activities"] += 1
                
                logger.debug(
                    f"Activity summary for {unit_id}: "
                    f"latest_score={latest.get('activity_score', 0)}, "
                    f"count={len(activities)}"
                )
        
        except Exception as e:
            logger.error(f"Error processing activities: {e}")
    
    async def _update_statistics(self):
        """Update aggregator statistics"""
        
        self.stats["units_active"] = len(hub_state.units)
        
        if self.stats["total_csi_frames"] > 0 and self.stats["total_csi_frames"] % 50 == 0:
            logger.info(
                f"Aggregator stats: "
                f"frames={self.stats['total_csi_frames']}, "
                f"activities={self.stats['total_activities']}, "
                f"units={self.stats['units_active']}"
            )
    
    async def get_aggregated_report(self) -> dict:
        """Get comprehensive aggregated report"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_status": await hub_state.get_system_status(),
            "statistics": self.stats,
            "units": {},
        }
        
        # Per-unit summaries
        for unit_id, unit_info in hub_state.units.items():
            unit_activities = [a for a in hub_state.activity_buffer if a.get('unit_id') == unit_id]
            
            if unit_activities:
                latest_activity = unit_activities[-1]
                report["units"][unit_id] = {
                    "status": unit_info.get("status"),
                    "last_seen": unit_info.get("last_seen"),
                    "activity_count": len(unit_activities),
                    "latest_activity_score": latest_activity.get("activity_score"),
                    "cached_reasoning": llm_reasoner.reasoning_cache.get(unit_id),
                }
        
        return report
    
    async def get_timeline(self, unit_id: str, max_items: int = 100) -> List[dict]:
        """Get activity timeline for a specific unit"""
        
        timeline = [
            a for a in hub_state.activity_buffer[-max_items:]
            if a.get('unit_id') == unit_id
        ]
        
        return timeline


# Global data aggregator instance
data_aggregator = DataAggregator()


async def initialize_aggregator():
    """Initialize data aggregator"""
    logger.info("Initializing data aggregator")
    return await data_aggregator.start()


async def shutdown_aggregator():
    """Shutdown data aggregator"""
    logger.info("Shutting down data aggregator")
    await data_aggregator.stop()
