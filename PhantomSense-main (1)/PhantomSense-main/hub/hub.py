#!/usr/bin/env python3
"""
PhantomSense Hub - Main Entry Point
Optimized for Franklin workstation (Ryzen 9, 96GB RAM, dual GPU)
"""

import asyncio
import logging
import signal
import sys
from typing import Set

import uvicorn
from fastapi import FastAPI

# Import all components
from phantomsense_hub.core import initialize_hub, shutdown_hub, get_logger
from phantomsense_hub.mqtt_bridge import initialize_mqtt, shutdown_mqtt, mqtt_bridge
from phantomsense_hub.llm_reasoning import initialize_llm, shutdown_llm
from phantomsense_hub.data_aggregator import initialize_aggregator, shutdown_aggregator
from phantomsense_hub.api import app as api_app
from phantomsense_hub.core.config import config

logger = get_logger(__name__)

# Global task management
active_tasks: Set[asyncio.Task] = set()


async def main():
    """Main hub initialization and startup"""
    
    logger.info("=" * 60)
    logger.info("PhantomSense Hub Starting (Franklin)")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"  CPU: {config.franklin.CPU_CORES} cores @ {config.franklin.CPU_THREADS} threads")
    logger.info(f"  RAM: {config.franklin.AVAILABLE_RAM_GB}GB available")
    logger.info(f"  GPU: {config.franklin.GPU_DEVICES}")
    logger.info(f"  MQTT Broker: {config.mqtt.BROKER_HOST}:{config.mqtt.BROKER_PORT}")
    logger.info(f"  Ollama: {config.ollama.OLLAMA_HOST}")
    logger.info(f"  API: http://{config.api.HOST}:{config.api.PORT}")
    logger.info("=" * 60)
    
    try:
        # Initialize core hub
        await initialize_hub()
        
        # Initialize MQTT bridge
        if not await initialize_mqtt():
            logger.warning("MQTT bridge initialization failed (non-critical)")
        
        # Initialize LLM reasoning
        if not await initialize_llm():
            logger.warning("LLM reasoning unavailable (non-critical)")
        
        # Initialize data aggregator and start background tasks
        aggregator_tasks = await initialize_aggregator()
        for task in aggregator_tasks:
            active_tasks.add(task)
            task.add_done_callback(active_tasks.discard)
        
        # Start MQTT message loop
        mqtt_task = asyncio.create_task(mqtt_bridge.message_loop())
        active_tasks.add(mqtt_task)
        mqtt_task.add_done_callback(active_tasks.discard)
        
        logger.info("All components initialized successfully")
        logger.info("Hub is ready to receive sensor data")
        
        # Start REST API server (runs in background)
        api_server = uvicorn.Server(
            uvicorn.Config(
                app=api_app,
                host=config.api.HOST,
                port=config.api.PORT,
                log_level=config.LOG_LEVEL.lower(),
            )
        )
        
        api_task = asyncio.create_task(api_server.serve())
        active_tasks.add(api_task)
        
        logger.info(f"REST API listening on http://{config.api.HOST}:{config.api.PORT}")
        logger.info("Hub ready!")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        await cleanup()


async def cleanup():
    """Cleanup and shutdown all components"""
    
    logger.info("Cleaning up...")
    
    # Cancel all active tasks
    for task in list(active_tasks):
        if not task.done():
            task.cancel()
    
    # Wait for tasks to complete
    if active_tasks:
        await asyncio.gather(*active_tasks, return_exceptions=True)
    
    # Shutdown components
    await shutdown_mqtt()
    await shutdown_llm()
    await shutdown_aggregator()
    await shutdown_hub()
    
    logger.info("Hub shutdown complete")


def setup_signal_handlers(loop):
    """Setup signal handlers for graceful shutdown"""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(cleanup())
        sys.exit(0)
    
    for sig in [signal.SIGINT, signal.SIGTERM]:
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s, None))


if __name__ == "__main__":
    # Setup
    import colorlog
    
    # Configure colorized logging
    handler = logging.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Run main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Hub stopped by user")
    except Exception as e:
        logger.error(f"Hub crashed: {e}", exc_info=True)
        sys.exit(1)
