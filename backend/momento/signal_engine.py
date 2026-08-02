"""
Signal Engine Module
Real-time signal generation from streaming data.
"""

import asyncio
import time
from typing import Dict, Optional, Callable, List
from collections import deque
import numpy as np

# Try relative import first, fall back to direct import
try:
    from .pipeline import PredictionPipeline
    from .live_stream import LiveStreamClient
except ImportError:
    from pipeline import PredictionPipeline
    from live_stream import LiveStreamClient


class SignalEngine:
    """
    Real-time signal generation engine.
    Combines live stream data with prediction pipeline.
    """
    
    def __init__(self, symbol: str = 'EURUSD', broker: str = 'deriv'):
        self.symbol = symbol
        self.broker = broker
        self.pipeline = PredictionPipeline(symbol=symbol)
        self.stream_client = LiveStreamClient(broker=broker, symbol=symbol)
        
        self.signals: deque = deque(maxlen=100)
        self.last_signal_time = 0
        self.signal_count = 0
        self.is_running = False
        
        self.signal_callback: Optional[Callable[[Dict], None]] = None
    
    async def on_tick(self, tick: Dict) -> None:
        """Process incoming tick and generate signals."""
        self.pipeline.ingest_tick(tick)
        
        # Generate signal every 10 ticks or on significant price change
        if len(self.pipeline.data_buffer['closes']) >= 20:
            if self.signal_count % 10 == 0 or self._significant_move(tick):
                signal = self.pipeline.get_streaming_signal()
                
                if signal:
                    signal['tick'] = tick
                    signal['generated_at'] = time.time()
                    self.signals.append(signal)
                    self.last_signal_time = time.time()
                    self.signal_count += 1
                    
                    if self.signal_callback:
                        await self._safe_callback(signal)
    
    def _significant_move(self, tick: Dict) -> bool:
        """Detect significant price movement."""
        closes = list(self.pipeline.data_buffer['closes'])
        if len(closes) < 5:
            return False
        
        recent_avg = np.mean(closes[-5:])
        current_price = tick.get('price', tick.get('close', 0))
        
        return abs(current_price - recent_avg) / recent_avg > 0.0005
    
    async def _safe_callback(self, signal: Dict) -> None:
        """Safely execute signal callback."""
        try:
            if asyncio.iscoroutinefunction(self.signal_callback):
                await self.signal_callback(signal)
            else:
                self.signal_callback(signal)
        except Exception as e:
            print(f"Signal callback error: {e}")
    
    def set_signal_callback(self, callback: Callable[[Dict], None]) -> None:
        """Set callback for new signals."""
        self.signal_callback = callback
    
    async def start(self) -> None:
        """Start the signal engine."""
        self.is_running = True
        print(f"Signal Engine started for {self.symbol}")
        await self.stream_client.run_with_reconnect(self.on_tick)
    
    async def stop(self) -> None:
        """Stop the signal engine."""
        self.is_running = False
        await self.stream_client.disconnect()
        print("Signal Engine stopped")
    
    def get_recent_signals(self, count: int = 10) -> List[Dict]:
        """Get most recent signals."""
        return list(self.signals)[-count:]
    
    def get_statistics(self) -> Dict:
        """Get engine statistics."""
        return {
            'symbol': self.symbol,
            'broker': self.broker,
            'signal_count': self.signal_count,
            'last_signal_time': self.last_signal_time,
            'is_running': self.is_running,
            'buffer_size': len(self.pipeline.data_buffer['closes'])
        }


async def demo_engine():
    """Demo function to test signal engine."""
    engine = SignalEngine(symbol='R_100', broker='deriv')
    
    def on_signal(signal: Dict):
        print(f"Signal: {signal['signal']} @ {signal['tick'].get('price', 'N/A')}")
        print(f"  Confidence: {signal.get('confidence', 0):.2f}")
        print(f"  Reasoning: {signal.get('reasoning', 'N/A')}")
    
    engine.set_signal_callback(on_signal)
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        await engine.stop()


if __name__ == '__main__':
    asyncio.run(demo_engine())
