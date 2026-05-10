"""
Core hub initialization and utilities
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from .config import config

# Configure logging
LOG_DIR = config.LOG_FILE.parent
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)


class HubState:
    """Central hub state management"""
    
    def __init__(self):
        self.units = {}  # Active sensor units
        self.latest_data = {}  # Latest CSI data per unit
        self.activity_buffer = []  # Buffered activity classifications
        self.reasoning_cache = {}  # LLM reasoning results cache
        self.is_running = False
        self._lock = asyncio.Lock()
    
    async def update_unit_data(self, unit_id: str, data: dict):
        """Update latest data from a sensor unit"""
        async with self._lock:
            if unit_id not in self.units:
                self.units[unit_id] = {
                    'last_seen': asyncio.get_event_loop().time(),
                    'status': 'active'
                }
            self.latest_data[unit_id] = data
            self.units[unit_id]['last_seen'] = asyncio.get_event_loop().time()
    
    async def add_activity(self, unit_id: str, activity: dict):
        """Add activity classification to buffer"""
        async with self._lock:
            activity['unit_id'] = unit_id
            activity['timestamp'] = asyncio.get_event_loop().time()
            self.activity_buffer.append(activity)
            
            # Keep buffer at max size
            if len(self.activity_buffer) > config.BUFFER_SIZE:
                self.activity_buffer.pop(0)
    
    async def get_system_status(self) -> dict:
        """Get current system status"""
        async with self._lock:
            return {
                'units': len(self.units),
                'active_units': sum(1 for u in self.units.values() if u['status'] == 'active'),
                'buffered_activities': len(self.activity_buffer),
                'is_running': self.is_running,
            }


# Global hub state
hub_state = HubState()


def get_logger(name: str) -> logging.Logger:
    """Get a named logger"""
    return logging.getLogger(name)


async def initialize_hub():
    """Initialize hub components"""
    logger.info("Initializing PhantomSense Hub (Franklin)")
    logger.info(f"Configuration: {config.franklin.CPU_CORES} cores, {config.franklin.RAM_GB}GB RAM")
    logger.info(f"GPU Devices: {config.franklin.GPU_DEVICES}")
    
    # Ensure data directories exist
    (config.LOG_FILE.parent).mkdir(parents=True, exist_ok=True)
    (config.database.DB_PATH.parent).mkdir(parents=True, exist_ok=True)
    
    hub_state.is_running = True
    logger.info("Hub initialization complete")


async def shutdown_hub():
    """Shutdown hub components"""
    logger.info("Shutting down PhantomSense Hub")
    hub_state.is_running = False
    logger.info("Hub shutdown complete")
