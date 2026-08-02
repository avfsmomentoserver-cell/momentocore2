"""
Live Stream Module
WebSocket client for real-time forex tick ingestion.
"""

import asyncio
import json
import time
from typing import Optional, Callable, Dict, Any
import websockets


class LiveStreamClient:
    """
    WebSocket client for streaming forex tick data.
    Supports multiple brokers and automatic reconnection.
    """
    
    def __init__(self, broker: str = 'deriv', symbol: str = 'R_100'):
        self.broker = broker
        self.symbol = symbol
        self.ws_url = self._get_broker_url(broker)
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.is_running = False
        self.tick_callback: Optional[Callable[[Dict], None]] = None
        self.reconnect_delay = 5
        self.last_tick_time = 0
        self.tick_count = 0
    
    def _get_broker_url(self, broker: str) -> str:
        """Get WebSocket URL for broker."""
        urls = {
            'deriv': 'wss://ws.binary.com/websocket/v3',
            'oanda': 'wss://stream-fxpractice.oanda.com/v3/pricing',
            'generic': 'ws://localhost:8765'
        }
        return urls.get(broker, urls['generic'])
    
    async def connect(self) -> bool:
        """Establish WebSocket connection."""
        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10
            )
            self.is_connected = True
            print(f"Connected to {self.broker} at {self.ws_url}")
            
            # Subscribe to symbol
            await self.subscribe(self.symbol)
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def subscribe(self, symbol: str) -> None:
        """Subscribe to symbol price stream."""
        if not self.websocket:
            return
        
        subscribe_msg = {
            "ticks": symbol,
            "subscribe": 1
        }
        
        await self.websocket.send(json.dumps(subscribe_msg))
        print(f"Subscribed to {symbol}")
    
    async def listen(self, callback: Callable[[Dict], None]) -> None:
        """Listen for incoming ticks."""
        self.tick_callback = callback
        self.is_running = True
        
        while self.is_running and self.is_connected:
            try:
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=60
                )
                data = json.loads(message)
                
                if 'tick' in data:
                    tick = self._parse_tick(data)
                    self.last_tick_time = time.time()
                    self.tick_count += 1
                    
                    if self.tick_callback:
                        await self._safe_callback(tick)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Listen error: {e}")
                self.is_connected = False
                break
    
    async def _safe_callback(self, tick: Dict) -> None:
        """Safely execute callback with error handling."""
        try:
            if asyncio.iscoroutinefunction(self.tick_callback):
                await self.tick_callback(tick)
            else:
                self.tick_callback(tick)
        except Exception as e:
            print(f"Callback error: {e}")
    
    def _parse_tick(self, data: Dict) -> Dict:
        """Parse raw tick data into standard format."""
        tick_data = data.get('tick', {})
        return {
            'symbol': self.symbol,
            'price': tick_data.get('quote', 0),
            'bid': tick_data.get('bid', 0),
            'ask': tick_data.get('ask', 0),
            'timestamp': tick_data.get('epoch', time.time()),
            'broker': self.broker
        }
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self.is_running = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.is_connected = False
        print("Disconnected")
    
    async def run_with_reconnect(self, callback: Callable[[Dict], None]) -> None:
        """Run listener with automatic reconnection."""
        while self.is_running:
            if await self.connect():
                await self.listen(callback)
            
            if self.is_running:
                print(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)


async def demo_stream():
    """Demo function to test live streaming."""
    client = LiveStreamClient(broker='deriv', symbol='R_100')
    
    def on_tick(tick: Dict):
        print(f"Tick: {tick['price']} @ {tick['timestamp']}")
    
    try:
        await client.run_with_reconnect(on_tick)
    except KeyboardInterrupt:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(demo_stream())
