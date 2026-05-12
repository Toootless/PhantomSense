"""
MQTT Bridge - Asynchronous MQTT client for sensor unit communication
"""

import asyncio
import json
import logging
from typing import Callable, Optional

from aiomqtt import Client

from ..core.config import config
from ..core import hub_state, get_logger

logger = get_logger(__name__)


class MQTTBridge:
    """Asynchronous MQTT bridge for PhantomSense"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        self.callbacks = {}  # Topic -> callback mapping
        self.reconnect_attempts = 0
        self.message_loop_task = None
    
    async def connect(self) -> bool:
        """Connect to MQTT broker and start message loop"""
        try:
            logger.info(f"Connecting to MQTT broker: {config.mqtt.BROKER_HOST}:{config.mqtt.BROKER_PORT}")
            
            self.client = Client(
                hostname=config.mqtt.BROKER_HOST,
                port=config.mqtt.BROKER_PORT,
                username=config.mqtt.USERNAME,
                password=config.mqtt.PASSWORD,
                keepalive=config.mqtt.KEEPALIVE,
            )
            
            # Connect via async context manager
            await self.client.__aenter__()
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("Connected to MQTT broker")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error during MQTT disconnect: {e}")
            self.is_connected = False
            logger.info("Disconnected from MQTT broker")
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to MQTT topic with callback"""
        if not self.is_connected:
            logger.warning("Not connected to MQTT broker")
            return
        
        self.callbacks[topic] = callback
        logger.debug(f"Subscribing to topic: {topic}")
        
        try:
            await self.client.subscribe(topic)
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
    
    async def publish(self, topic: str, payload: dict, qos: int = 1) -> bool:
        """Publish message to MQTT topic"""
        if not self.is_connected:
            logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            message = json.dumps(payload)
            await self.client.publish(topic, message, qos=qos)
            logger.debug(f"Published to {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False
    
    async def message_loop(self):
        """Main message loop - continuously listen for MQTT messages"""
        if not self.is_connected:
            logger.error("Not connected to MQTT broker")
            return
        
        logger.info("Starting MQTT message loop")
        
        try:
            async with self.client.messages() as messages:
                async for message in messages:
                    topic = message.topic
                    payload = json.loads(message.payload.decode())
                    
                    logger.debug(f"Received message on {topic}")
                    
                    # Route message to appropriate handler
                    await self._route_message(topic, payload)
                    
        except asyncio.CancelledError:
            logger.info("MQTT message loop cancelled")
        except Exception as e:
            logger.error(f"Error in MQTT message loop: {e}")
            self.is_connected = False
    
    async def _route_message(self, topic: str, payload: dict):
        """Route MQTT message to appropriate handler"""
        
        # Extract unit ID from topic: /phantomsense/unit1/...
        parts = topic.split('/')
        if len(parts) < 3:
            logger.warning(f"Invalid topic format: {topic}")
            return
        
        unit_id = parts[2]  # unit1, unit2, etc.
        message_type = parts[3] if len(parts) > 3 else "unknown"
        
        try:
            if message_type == "csi_data":
                await self._handle_csi_data(unit_id, payload)
            elif message_type == "activity":
                await self._handle_activity(unit_id, payload)
            elif message_type == "status":
                await self._handle_status(unit_id, payload)
            else:
                logger.debug(f"Unknown message type: {message_type}")
        except Exception as e:
            logger.error(f"Error routing message from {unit_id}: {e}")
    
    async def _handle_csi_data(self, unit_id: str, data: dict):
        """Handle CSI data from sensor unit"""
        logger.debug(f"CSI data from {unit_id}: amplitude_mean={data.get('amplitude_mean'):.2f}")
        
        # Update hub state
        await hub_state.update_unit_data(unit_id, data)
        
        # Call registered callback if exists
        callback = self.callbacks.get(f"{config.mqtt.TOPIC_CSI_DATA}")
        if callback:
            await callback(unit_id, data)
    
    async def _handle_activity(self, unit_id: str, activity: dict):
        """Handle activity classification from sensor unit"""
        logger.info(f"Activity from {unit_id}: score={activity.get('activity_score')}")
        
        # Add to buffer
        await hub_state.add_activity(unit_id, activity)
        
        # Call registered callback if exists
        callback = self.callbacks.get(f"{config.mqtt.TOPIC_ACTIVITY}")
        if callback:
            await callback(unit_id, activity)
    
    async def _handle_status(self, unit_id: str, status: dict):
        """Handle status update from sensor unit"""
        logger.debug(f"Status from {unit_id}: {status}")
        
        # Update hub state
        if unit_id in hub_state.units:
            hub_state.units[unit_id].update(status)


# Global MQTT bridge instance
mqtt_bridge = MQTTBridge()


async def initialize_mqtt():
    """Initialize and connect MQTT bridge"""
    logger.info("Initializing MQTT bridge")
    
    if await mqtt_bridge.connect():
        # Subscribe to sensor topics
        await mqtt_bridge.subscribe(config.mqtt.TOPIC_CSI_DATA, None)
        await mqtt_bridge.subscribe(config.mqtt.TOPIC_ACTIVITY, None)
        await mqtt_bridge.subscribe(config.mqtt.TOPIC_STATUS, None)
        
        logger.info("MQTT bridge initialized")
        return True
    else:
        logger.error("Failed to initialize MQTT bridge")
        return False


async def shutdown_mqtt():
    """Shutdown MQTT bridge"""
    logger.info("Shutting down MQTT bridge")
    await mqtt_bridge.disconnect()
