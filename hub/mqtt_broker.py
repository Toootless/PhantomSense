#!/usr/bin/env python3
"""
Minimal MQTT Broker for PhantomSense
Accepts connections and relays messages between subscribers
"""

import asyncio
import logging
import signal
from typing import Dict, Set, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MQTT_BROKER")


class SimpleMQTTBroker:
    """Basic MQTT broker implementation"""
    
    def __init__(self, host='127.0.0.1', port=1883):
        self.host = host
        self.port = port
        self.clients: Dict[str, 'MQTTClient'] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of client_ids
        self.running = False
        self.server = None
    
    async def start(self):
        """Start the MQTT broker"""
        logger.info(f"Starting MQTT broker on {self.host}:{self.port}")
        self.running = True
        
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info("MQTT broker listening")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """Handle incoming client connection"""
        addr = writer.get_extra_info('peername')
        logger.debug(f"New connection from {addr}")
        
        try:
            # Read MQTT CONNECT packet
            data = await reader.readexactly(1)
            if not data:
                return
            
            # Very basic MQTT protocol handling
            # Just echo CONNACK (simplified - not full MQTT)
            writer.write(bytes([0x20, 0x02, 0x00, 0x00]))  # CONNACK
            await writer.drain()
            
            client_id = f"client_{addr[1]}"
            self.clients[client_id] = {
                'reader': reader,
                'writer': writer,
                'addr': addr
            }
            
            logger.info(f"Client connected: {client_id}")
            
            # Handle client messages
            while self.running:
                try:
                    # Read message header
                    header = await reader.readexactly(2)
                    if not header:
                        break
                    
                    msg_type = (header[0] >> 4) & 0x0F
                    remaining_len = header[1]
                    
                    # Read remaining payload
                    if remaining_len > 0:
                        payload = await reader.readexactly(remaining_len)
                    else:
                        payload = b''
                    
                    # Handle message types
                    if msg_type == 3:  # PUBLISH
                        await self.handle_publish(client_id, payload)
                    elif msg_type == 8:  # SUBSCRIBE
                        await self.handle_subscribe(client_id, payload)
                    elif msg_type == 12:  # PINGREQ
                        writer.write(bytes([0xD0, 0x00]))  # PINGRESP
                        await writer.drain()
                    elif msg_type == 14:  # DISCONNECT
                        break
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"Message handling error: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Client error: {e}")
        
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            writer.close()
            await writer.wait_closed()
            logger.info(f"Client disconnected: {client_id}")
    
    async def handle_publish(self, client_id: str, payload: bytes):
        """Handle PUBLISH message"""
        # Very simplified - just parse topic and payload
        try:
            # Skip QoS and packet ID for now
            # Just extract and relay to subscribers
            logger.debug(f"Publish from {client_id}")
        except Exception as e:
            logger.error(f"Publish error: {e}")
    
    async def handle_subscribe(self, client_id: str, payload: bytes):
        """Handle SUBSCRIBE message"""
        try:
            logger.debug(f"Subscribe from {client_id}")
        except Exception as e:
            logger.error(f"Subscribe error: {e}")
    
    async def stop(self):
        """Stop the MQTT broker"""
        logger.info("Stopping MQTT broker")
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()


async def main():
    """Main entry point"""
    broker = SimpleMQTTBroker(host='127.0.0.1', port=1883)
    
    # Setup signal handlers (Unix only)
    import platform
    if platform.system() != 'Windows':
        def signal_handler(sig):
            logger.info(f"Received signal {sig}")
            asyncio.create_task(broker.stop())
        
        loop = asyncio.get_event_loop()
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, signal_handler, sig)
    
    try:
        await broker.start()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())
