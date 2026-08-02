"""
Prediction Pipeline Module
Orchestrates the complete forex prediction flow from data ingestion to signal generation.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque
import time

# Try relative import first, fall back to direct import for standalone testing
try:
    from .linguistics import (
        calculate_rsi,
        calculate_atr,
        identify_support_resistance,
        classify_forex_state,
        calculate_momentum_confirmation,
        get_state_probability_distribution
    )
    from .forecast_forex import (
        forex_candidates,
        forex_forecast,
        store_forex_prediction
    )
except ImportError:
    from linguistics import (
        calculate_rsi,
        calculate_atr,
        identify_support_resistance,
        classify_forex_state,
        calculate_momentum_confirmation,
        get_state_probability_distribution
    )
    from forecast_forex import (
        forex_candidates,
        forex_forecast,
        store_forex_prediction
    )


class PredictionPipeline:
    """
    Complete forex prediction pipeline with streaming support.
    Processes OHLCV data and generates predictions in <50ms.
    """
    
    def __init__(self, symbol: str = 'EURUSD', window_size: int = 100):
        self.symbol = symbol
        self.window_size = window_size
        self.data_buffer = {
            'opens': deque(maxlen=window_size),
            'highs': deque(maxlen=window_size),
            'lows': deque(maxlen=window_size),
            'closes': deque(maxlen=window_size),
            'volumes': deque(maxlen=window_size)
        }
        self.last_prediction_time = 0
        self.processing_times = deque(maxlen=100)
    
    def ingest_tick(self, tick: Dict) -> None:
        """Ingest a single tick of data."""
        self.data_buffer['opens'].append(tick.get('open', tick.get('price', 0)))
        self.data_buffer['highs'].append(tick.get('high', tick.get('price', 0)))
        self.data_buffer['lows'].append(tick.get('low', tick.get('price', 0)))
        self.data_buffer['closes'].append(tick.get('close', tick.get('price', 0)))
        self.data_buffer['volumes'].append(tick.get('volume', 0))
    
    def ingest_batch(self, ohlcv_data: List[Dict]) -> None:
        """Ingest a batch of OHLCV data."""
        for bar in ohlcv_data:
            self.data_buffer['opens'].append(bar['open'])
            self.data_buffer['highs'].append(bar['high'])
            self.data_buffer['lows'].append(bar['low'])
            self.data_buffer['closes'].append(bar['close'])
            self.data_buffer['volumes'].append(bar.get('volume', 0))
    
    def run_prediction(self) -> Dict:
        """Execute complete prediction pipeline."""
        start_time = time.time()
        
        if len(self.data_buffer['closes']) < 20:
            return {
                'status': 'insufficient_data',
                'current_length': len(self.data_buffer['closes']),
                'required': 20
            }
        
        # Convert deques to lists
        opens = list(self.data_buffer['opens'])
        highs = list(self.data_buffer['highs'])
        lows = list(self.data_buffer['lows'])
        closes = list(self.data_buffer['closes'])
        volumes = list(self.data_buffer['volumes'])
        
        # Generate forecast
        forecast = forex_forecast(opens, highs, lows, closes, volumes)
        
        # Generate candidates
        candidates = forex_candidates(opens, highs, lows, closes, volumes)
        
        # Get momentum confirmation
        momentum = calculate_momentum_confirmation(closes, volumes if any(volumes) else None)
        
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        self.last_prediction_time = time.time()
        
        return {
            'status': 'success',
            'symbol': self.symbol,
            'timestamp': self.last_prediction_time,
            'processing_time_ms': round(processing_time, 2),
            'avg_processing_time_ms': round(np.mean(self.processing_times), 2) if self.processing_times else 0,
            'forecast': forecast,
            'candidates': candidates,
            'momentum': momentum,
            'data_points': len(closes)
        }
    
    def get_streaming_signal(self) -> Optional[Dict]:
        """Generate real-time trading signal from latest data."""
        if len(self.data_buffer['closes']) < 20:
            return None
        
        result = self.run_prediction()
        if result['status'] != 'success':
            return None
        
        forecast = result['forecast']
        candidates = result['candidates']
        
        if not candidates:
            return {
                'signal': 'HOLD',
                'confidence': 0.5,
                'reasoning': 'No high-confidence candidates'
            }
        
        best_candidate = candidates[0]
        
        if best_candidate['confidence'] > 0.7 and best_candidate['risk_reward'] > 1.5:
            return {
                'signal': best_candidate['direction'],
                'entry': best_candidate['entry'],
                'stop_loss': best_candidate['stop_loss'],
                'take_profit': best_candidate['take_profit'],
                'confidence': best_candidate['confidence'],
                'risk_reward': best_candidate['risk_reward'],
                'reasoning': best_candidate['reasoning'],
                'state': forecast['dominant_state']
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': best_candidate['confidence'],
                'reasoning': f"Confidence {best_candidate['confidence']:.2f} below threshold"
            }
    
    def reset(self) -> None:
        """Clear all buffered data."""
        for key in self.data_buffer:
            self.data_buffer[key].clear()
        self.processing_times.clear()
