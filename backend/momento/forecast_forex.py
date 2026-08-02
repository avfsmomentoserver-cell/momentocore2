"""
Forex Forecast Engine
Generates predictions, range forecasts, and candidate analysis using forex concepts.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# Try relative import first, fall back to direct import for standalone testing
try:
    from .linguistics import (
        FOREX_STATES,
        calculate_rsi,
        calculate_atr,
        identify_support_resistance,
        classify_forex_state,
        get_state_probability_distribution
    )
except ImportError:
    from linguistics import (
        FOREX_STATES,
        calculate_rsi,
        calculate_atr,
        identify_support_resistance,
        classify_forex_state,
        get_state_probability_distribution
    )


def forex_state_sequence(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    num_rounds: int = 5
) -> List[Dict]:
    """Generate sequence of forex states with probabilities."""
    if len(closes) < 20:
        return []
    
    sequences = []
    prices = closes
    window = 20
    
    for i in range(window, len(closes), max(1, len(closes)//num_rounds)):
        state, probs = classify_forex_state(prices[:i], highs[:i], lows[:i], window)
        sequences.append({
            'round': len(sequences) + 1,
            'state': state,
            'probabilities': probs,
            'price': closes[i-1]
        })
        
        if len(sequences) >= num_rounds:
            break
    
    return sequences


def forex_candidates(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: Optional[List[float]] = None,
    max_candidates: int = 3
) -> List[Dict]:
    """Generate ranked trade candidates based on forex analysis."""
    if len(closes) < 20:
        return []
    
    current_price = closes[-1]
    rsi = calculate_rsi(closes)
    atr = calculate_atr(highs, lows, closes)
    sr_levels = identify_support_resistance(highs, lows, closes)
    state, probs = classify_forex_state(closes, highs, lows)
    
    candidates = []
    
    # Long candidate
    if rsi < 70 and len(sr_levels['support']) > 0:
        support = sr_levels['support'][0]
        entry = current_price * 0.9995
        stop_loss = support * 0.998
        take_profit = current_price + (current_price - stop_loss) * 2
        
        risk = abs(entry - stop_loss) / entry
        reward = abs(take_profit - entry) / entry
        rr_ratio = reward / risk if risk > 0 else 0
        
        confidence = probs.get('Trending', 0) + probs.get('Breakout', 0)
        if rsi < 30:
            confidence += 0.2
        
        candidates.append({
            'direction': 'LONG',
            'entry': round(entry, 5),
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'risk_reward': round(rr_ratio, 2),
            'confidence': round(min(confidence, 1.0), 3),
            'reasoning': f"RSI={rsi}, State={state}, Support={support:.5f}"
        })
    
    # Short candidate
    if rsi > 30 and len(sr_levels['resistance']) > 0:
        resistance = sr_levels['resistance'][0]
        entry = current_price * 1.0005
        stop_loss = resistance * 1.002
        take_profit = current_price - (stop_loss - current_price) * 2
        
        risk = abs(stop_loss - entry) / entry
        reward = abs(entry - take_profit) / entry
        rr_ratio = reward / risk if risk > 0 else 0
        
        confidence = probs.get('Trending', 0) + probs.get('Breakout', 0)
        if rsi > 70:
            confidence += 0.2
        
        candidates.append({
            'direction': 'SHORT',
            'entry': round(entry, 5),
            'stop_loss': round(stop_loss, 5),
            'take_profit': round(take_profit, 5),
            'risk_reward': round(rr_ratio, 2),
            'confidence': round(min(confidence, 1.0), 3),
            'reasoning': f"RSI={rsi}, State={state}, Resistance={resistance:.5f}"
        })
    
    # Sort by confidence * risk_reward
    candidates.sort(key=lambda x: x['confidence'] * x['risk_reward'], reverse=True)
    return candidates[:max_candidates]


def forex_forecast(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: Optional[List[float]] = None,
    forecast_horizon: int = 10
) -> Dict:
    """Generate comprehensive forex forecast."""
    if len(closes) < 20:
        return {'error': 'Insufficient data'}
    
    current_price = closes[-1]
    atr = calculate_atr(highs, lows, closes)
    rsi = calculate_rsi(closes)
    state, probs = classify_forex_state(closes, highs, lows)
    sr_levels = identify_support_resistance(highs, lows, closes)
    
    # Range forecast based on ATR
    upward_range = current_price + (atr * forecast_horizon * 0.5)
    downward_range = current_price - (atr * forecast_horizon * 0.5)
    
    # Adjust based on state
    if state == 'Trending':
        if closes[-1] > closes[-5]:
            upward_range = current_price + (atr * forecast_horizon * 0.7)
        else:
            downward_range = current_price - (atr * forecast_horizon * 0.7)
    elif state == 'Ranging':
        upward_range = min(upward_range, sr_levels['resistance'][0] if sr_levels['resistance'] else upward_range)
        downward_range = max(downward_range, sr_levels['support'][0] if sr_levels['support'] else downward_range)
    
    # Multi-timeframe probabilities
    mt_probs = get_state_probability_distribution(closes, highs, lows)
    
    return {
        'current_price': round(current_price, 5),
        'forecast_range': {
            'low': round(downward_range, 5),
            'high': round(upward_range, 5)
        },
        'dominant_state': state,
        'state_probabilities': probs,
        'mt_state_probabilities': mt_probs,
        'indicators': {
            'rsi': rsi,
            'atr': round(atr, 5),
            'support': sr_levels['support'][:3] if sr_levels['support'] else [],
            'resistance': sr_levels['resistance'][:3] if sr_levels['resistance'] else []
        },
        'volatility': 'HIGH' if atr > current_price * 0.001 else 'NORMAL'
    }


_predictions_store = {}


def store_forex_prediction(
    symbol: str,
    prediction: Dict,
    timestamp: Optional[float] = None
) -> str:
    """Store prediction for later retrieval."""
    import time
    ts = timestamp or time.time()
    key = f"{symbol}_{ts}"
    _predictions_store[key] = {
        'symbol': symbol,
        'prediction': prediction,
        'timestamp': ts
    }
    return key


def get_stored_prediction(key: str) -> Optional[Dict]:
    """Retrieve stored prediction."""
    return _predictions_store.get(key)
