"""
Forex Linguistics Module
Provides technical indicators, market state classification, and support/resistance analysis.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

FOREX_STATES = ['Ranging', 'Trending', 'Breakout', 'Reversal']


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI indicator."""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = np.diff(prices[-period-1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 1
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calculate Average True Range."""
    if len(closes) < period + 1:
        return abs(highs[-1] - lows[-1]) if highs and lows else 0.0
    
    tr_values = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        tr_values.append(tr)
    
    return round(np.mean(tr_values[-period:]), 5)


def identify_support_resistance(
    highs: List[float], 
    lows: List[float], 
    closes: List[float],
    lookback: int = 20
) -> Dict[str, List[float]]:
    """Identify support and resistance levels with confluence weighting."""
    if len(closes) < lookback:
        return {'support': [min(lows)], 'resistance': [max(highs)]}
    
    pivot_tolerance = 0.001  # 0.1% tolerance
    
    supports = []
    resistances = []
    
    for i in range(lookback, len(closes) - lookback):
        # Check for swing low (support)
        if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and \
           all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
            supports.append(lows[i])
        
        # Check for swing high (resistance)
        if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and \
           all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
            resistances.append(highs[i])
    
    # Cluster nearby levels
    def cluster_levels(levels: List[float], tolerance: float) -> List[Tuple[float, int]]:
        if not levels:
            return []
        
        levels.sort()
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] < tolerance:
                current_cluster.append(level)
            else:
                clusters.append((np.mean(current_cluster), len(current_cluster)))
                current_cluster = [level]
        
        clusters.append((np.mean(current_cluster), len(current_cluster)))
        return sorted(clusters, key=lambda x: x[1], reverse=True)
    
    support_clusters = cluster_levels(supports, pivot_tolerance)
    resistance_clusters = cluster_levels(resistances, pivot_tolerance)
    
    return {
        'support': [level for level, _ in support_clusters[:3]],
        'resistance': [level for level, _ in resistance_clusters[:3]]
    }


def classify_forex_state(
    prices: List[float],
    highs: List[float],
    lows: List[float],
    window: int = 20
) -> Tuple[str, Dict[str, float]]:
    """Classify current forex market state."""
    if len(prices) < window * 2:
        return 'Ranging', {state: 0.25 for state in FOREX_STATES}
    
    recent_prices = prices[-window:]
    prev_prices = prices[-window*2:-window]
    
    # Calculate metrics
    recent_high = max(recent_prices)
    recent_low = min(recent_prices)
    prev_high = max(prev_prices)
    prev_low = min(prev_prices)
    
    range_size = (recent_high - recent_low) / recent_low
    prev_range_size = (prev_high - prev_low) / prev_low
    
    trend_strength = abs(recent_prices[-1] - recent_prices[0]) / recent_prices[0]
    
    # Breakout detection
    breakout_up = recent_high > prev_high * 1.002
    breakout_down = recent_low < prev_low * 0.998
    
    # Reversal detection
    reversal_up = breakout_down and recent_prices[-1] > recent_prices[-5]
    reversal_down = breakout_up and recent_prices[-1] < recent_prices[-5]
    
    probabilities = defaultdict(float)
    
    if breakout_up or breakout_down:
        if reversal_up or reversal_down:
            probabilities['Reversal'] = 0.6
            probabilities['Breakout'] = 0.2
        else:
            probabilities['Breakout'] = 0.7
            probabilities['Trending'] = 0.2
    elif trend_strength > 0.005:
        probabilities['Trending'] = 0.65
        probabilities['Ranging'] = 0.2
    else:
        probabilities['Ranging'] = 0.7
        probabilities['Trending'] = 0.15
    
    probabilities['Breakout'] += 0.1
    probabilities['Reversal'] += 0.05
    
    total = sum(probabilities.values())
    probabilities = {k: v/total for k, v in probabilities.items()}
    
    dominant_state = max(probabilities, key=probabilities.get)
    return dominant_state, dict(probabilities)


def get_state_probability_distribution(
    prices: List[float],
    highs: List[float],
    lows: List[float],
    windows: List[int] = [10, 20, 50]
) -> Dict[str, float]:
    """Get multi-timeframe state probability distribution."""
    all_probabilities = defaultdict(list)
    
    for window in windows:
        if len(prices) >= window * 2:
            _, probs = classify_forex_state(prices, highs, lows, window)
            for state, prob in probs.items():
                all_probabilities[state].append(prob)
    
    final_probs = {}
    for state in FOREX_STATES:
        if all_probabilities[state]:
            final_probs[state] = round(np.mean(all_probabilities[state]), 3)
        else:
            final_probs[state] = 0.25
    
    total = sum(final_probs.values())
    return {k: round(v/total, 3) for k, v in final_probs.items()}


def calculate_momentum_confirmation(
    prices: List[float],
    volumes: Optional[List[float]] = None,
    periods: List[int] = [5, 10, 20]
) -> Dict[str, float]:
    """Calculate momentum confirmation across multiple periods."""
    momentum_signals = {}
    
    for period in periods:
        if len(prices) > period:
            momentum = (prices[-1] - prices[-period]) / prices[-period]
            
            if volumes and len(volumes) > period:
                avg_vol_recent = np.mean(volumes[-period:])
                avg_vol_prev = np.mean(volumes[-period*2:-period])
                vol_confirmation = avg_vol_recent / avg_vol_prev if avg_vol_prev > 0 else 1.0
            else:
                vol_confirmation = 1.0
            
            momentum_signals[f'momentum_{period}'] = round(momentum, 5)
            momentum_signals[f'vol_conf_{period}'] = round(vol_confirmation, 3)
    
    return momentum_signals
