"""
MarketDetector - Pattern detection for trading rounds
Detects hot streaks, color bias, band clusters, and volatility regimes
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import deque


class MarketDetector:
    """
    Detects market patterns and generates trading signals.
    
    Patterns detected:
    - Hot Streaks: 3+ consecutive rounds >= 2.0x
    - Color Bias: >=40% Pink/Purple in rolling window
    - Band Clusters: Cosmic/Mega/Moonshot appearances
    - Volatility Index: Market variance scoring
    """

    def __init__(self, window_size: int = 20):
        """
        Initialize detector with rolling window size.
        
        Args:
            window_size: Number of recent rounds to analyze (default: 20)
        """
        self.window_size = window_size
        self.round_buffer = deque(maxlen=window_size)

    def add_round(self, round_data: Dict) -> Optional[Dict]:
        """
        Add a new round and check for patterns.
        
        Args:
            round_data: Round dictionary with multiplier, color, band, timestamp
            
        Returns:
            Signal dictionary if pattern detected, None otherwise
        """
        self.round_buffer.append(round_data)
        
        if len(self.round_buffer) < 5:
            return None
        
        signal = self._detect_all_patterns()
        return signal

    def _detect_all_patterns(self) -> Optional[Dict]:
        """Run all pattern detectors and return strongest signal."""
        patterns = []
        
        # Detect hot streak
        hot_streak = self._detect_hot_streak()
        if hot_streak:
            patterns.append(("hot_streak", hot_streak))
        
        # Detect color bias
        color_bias = self._detect_color_bias()
        if color_bias:
            patterns.append(("color_bias", color_bias))
        
        # Detect band cluster
        band_cluster = self._detect_band_cluster()
        if band_cluster:
            patterns.append(("band_cluster", band_cluster))
        
        if not patterns:
            return None
        
        # Return highest confidence pattern
        best_pattern = max(patterns, key=lambda x: x[1]["confidence"])
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pattern_type": best_pattern[0],
            **best_pattern[1]
        }

    def _detect_hot_streak(self) -> Optional[Dict]:
        """Detect consecutive high-value rounds (>=2.0x)."""
        rounds = list(self.round_buffer)
        streak = 0
        max_streak = 0
        streak_start = None
        
        for i, r in enumerate(rounds):
            if r["multiplier"] >= 2.0:
                if streak == 0:
                    streak_start = i
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 0
        
        if max_streak >= 3:
            confidence = min(0.95, 0.5 + (max_streak - 3) * 0.15)
            return {
                "confidence": confidence,
                "action": "BET_AGGRESSIVE" if confidence > 0.7 else "BET_CONSERVATIVE",
                "metadata": {
                    "streak_length": max_streak,
                    "threshold": 2.0
                }
            }
        return None

    def _detect_color_bias(self) -> Optional[Dict]:
        """Detect unusual concentration of high-value colors (Pink/Purple)."""
        rounds = list(self.round_buffer)
        high_value_colors = ["pink", "purple"]
        count = sum(1 for r in rounds if r["color"].lower() in high_value_colors)
        ratio = count / len(rounds)
        
        if ratio >= 0.40:
            confidence = min(0.90, 0.5 + (ratio - 0.40) * 1.25)
            pink_count = sum(1 for r in rounds if r["color"].lower() == "pink")
            purple_count = sum(1 for r in rounds if r["color"].lower() == "purple")
            
            return {
                "confidence": confidence,
                "action": "BET_AGGRESSIVE" if ratio > 0.60 else "BET_CONSERVATIVE",
                "metadata": {
                    "high_value_ratio": ratio,
                    "pink_count": pink_count,
                    "purple_count": purple_count,
                    "window_size": len(rounds)
                }
            }
        return None

    def _detect_band_cluster(self) -> Optional[Dict]:
        """Detect cluster of high-volatility bands (Cosmic/Mega/Moonshot)."""
        rounds = list(self.round_buffer)
        high_bands = ["cosmic", "mega", "moonshot"]
        count = sum(1 for r in rounds if r["band"].lower() in high_bands)
        ratio = count / len(rounds)
        
        if ratio >= 0.25:
            confidence = min(0.85, 0.5 + (ratio - 0.25) * 1.4)
            return {
                "confidence": confidence,
                "action": "BET_CONSERVATIVE",
                "metadata": {
                    "high_band_ratio": ratio,
                    "high_band_count": count,
                    "bands_detected": list(set(r["band"].lower() for r in rounds if r["band"].lower() in high_bands))
                }
            }
        return None

    def get_volatility_index(self) -> float:
        """Calculate market volatility index (0.0-1.0)."""
        if len(self.round_buffer) < 2:
            return 0.0
        
        multipliers = [r["multiplier"] for r in self.round_buffer]
        mean = sum(multipliers) / len(multipliers)
        variance = sum((m - mean) ** 2 for m in multipliers) / len(multipliers)
        
        # Normalize to 0-1 range (assuming max variance ~1000)
        return min(1.0, variance / 1000.0)

    def reset(self):
        """Clear the round buffer."""
        self.round_buffer.clear()
