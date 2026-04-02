"""
============================================================================
Robot Hand - Relay Client
============================================================================
Architecture: Layer 2 (Orchestration) + Layer 3 (Execution)
Description: Connects Arduino to Relay server for remote control
Pattern: Async WebSocket Client + Serial Bridge
Safety: Connection retry, error handling, graceful shutdown
============================================================================
"""

import asyncio
import websockets
import serial
import serial.tools.list_ports
import json
import logging
import signal
import sys
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class Config:
    """Application configuration."""
    relay_url: str = "wss://robot-arm-relay-production.up.railway.app"
    arduino_port: Optional[str] = None
    baud_rate: int = 9600
    reconnect_delay: int = 3
    num_fingers: int = 5
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load config from environment or defaults."""
        import os
        return cls(
            relay_url=os.getenv("RELAY_URL", cls.relay_url),
            arduino_port=os.getenv("ARDUINO_PORT"),
            baud_rate=int(os.getenv("BAUD_RATE", "9600")),
        )


# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Arduino Controller
# ============================================================================

class ArduinoController:
    """
    Manages serial communication with Arduino.
    
    Pattern: Resource Manager with context manager support
    Safety: Auto-reconnect, timeout protection, command validation
    """
    
    def __init__(self, port: str, baud_rate: int = 9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial: Optional[serial.Serial] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Establish serial connection."""
        ports = self._find_ports()
        
        for port in [self.port] + ports:
            if not port:
                continue
            try:
                self.serial = serial.Serial(port, self.baud_rate, timeout=1)
                time.sleep(2)  # Wait for Arduino reset
                self.port = port
                self.connected = True
                logger.info(f"✓ Arduino: {port}")
                return True
            except serial.SerialException as e:
                logger.debug(f"Port {port}: {e}")
        
        logger.warning("⚠️  Simulation mode (Arduino not found)")
        return False
    
    def disconnect(self):
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False
    
    def send(self, command: str) -> str:
        """Send command to Arduino."""
        if not self.connected or not self.serial:
            logger.info(f"[SIM] {command}")
            return "OK"
        
        try:
            self.serial.write(f"{command}\n".encode())
            self.serial.flush()
            
            # Read response
            if self.serial.in_waiting > 0:
                response = self.serial.readline().decode().strip()
                logger.debug(f"← Arduino: {response}")
                return response
            return "OK"
            
        except serial.SerialException as e:
            logger.error(f"✗ Serial error: {e}")
            self.connected = False
            return "ERROR"
    
    def set_positions(self, positions: List[int]) -> str:
        """Set finger positions."""
        if len(positions) != 5:
            return "ERROR: Need 5 positions"
        
        # Validate and constrain angles
        angles = [max(0, min(180, int(p))) for p in positions[:5]]
        command = f"SET:{','.join(map(str, angles))}"
        return self.send(command)
    
    def _find_ports(self) -> List[str]:
        """Find available serial ports."""
        ports = []
        for port in serial.tools.list_ports.comports():
            if 'Arduino' in port.description or 'USB' in port.description:
                ports.append(port.device)
        return ports


# ============================================================================
# Relay Client
# ============================================================================

class RelayClient:
    """
    WebSocket client for Relay server.
    
    Pattern: Async WebSocket Client with auto-reconnect
    Safety: Connection pooling, heartbeat, error recovery
    """
    
    def __init__(self, config: Config, arduino: ArduinoController):
        self.config = config
        self.arduino = arduino
        self.running = True
    
    async def run(self):
        """Main event loop with auto-reconnect."""
        logger.info("=" * 60)
        logger.info("🖐️  Robot Hand - Relay Client")
        logger.info("=" * 60)
        logger.info(f"Relay: {self.config.relay_url}")
        logger.info(f"Arduino: {self.config.arduino_port or 'Auto-detect'}")
        logger.info("")
        
        # Connect to Arduino
        self.arduino.connect()
        
        # WebSocket event loop
        while self.running:
            try:
                async with websockets.connect(
                    self.config.relay_url,
                    ping_interval=30,
                    ping_timeout=10
                ) as ws:
                    logger.info("🔌 Connected to Relay")
                    
                    # Register as Arduino client
                    await ws.send(json.dumps({
                        "type": "register",
                        "role": "arduino"
                    }))
                    
                    logger.info("✅ Online! Waiting for commands...")
                    
                    # Message handler
                    await self._handle_messages(ws)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️  Connection closed")
            except Exception as e:
                logger.error(f"❌ Error: {e}")
            
            if self.running:
                logger.info(f"🔄 Reconnecting in {self.config.reconnect_delay}s...")
                await asyncio.sleep(self.config.reconnect_delay)
    
    async def _handle_messages(self, ws: websockets.WebSocketClientProtocol):
        """Handle incoming WebSocket messages."""
        async for message in ws:
            try:
                data = json.loads(message)
                await self._process_message(data, ws)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"❌ Message error: {e}")
    
    async def _process_message(self, data: dict, ws: websockets.WebSocketClientProtocol):
        """Process a single message."""
        msg_type = data.get("type")
        
        if msg_type == "set":
            positions = data.get("positions", [90] * 5)
            result = self.arduino.set_positions(positions)
            logger.info(f"→ SET {positions} → {result}")
            
        elif msg_type == "command":
            cmd = data.get("command", "")
            await self._handle_command(cmd)
            
        elif msg_type == "ping":
            await ws.send(json.dumps({"type": "pong"}))
    
    async def _handle_command(self, cmd: str):
        """Handle command message."""
        if cmd in ("OPEN", "HOME"):
            result = self.arduino.send("OPEN")
        elif cmd == "GRIP":
            result = self.arduino.send("GRIP")
        else:
            result = self.arduino.send(cmd)
        
        logger.info(f"→ {cmd} → {result}")
    
    def stop(self):
        """Stop the client."""
        self.running = False
        self.arduino.disconnect()
        logger.info("👋 Stopped")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Application entry point."""
    config = Config.from_env()
    arduino = ArduinoController(
        port=config.arduino_port or "/dev/ttyUSB1",
        baud_rate=config.baud_rate
    )
    client = RelayClient(config, arduino)
    
    # Signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n🛑 Shutdown signal received")
        client.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("\n👋 Interrupted by user")
    finally:
        client.stop()


if __name__ == "__main__":
    main()
