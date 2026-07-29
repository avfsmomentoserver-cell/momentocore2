"""
Feature Extraction Engine.
Computes 40+ ML-ready features from round data.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from collections import deque

class FeatureExtractor:
    """
    Extracts statistical, temporal, and pattern-based features.
    Optimized for real-time inference.
    """

    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    def add_round(self, round_data: Dict[str, Any]):
        """Add a new round to the history buffer."""
        self.history.append(round_data)

    def extract_all(self) -> Dict[str, Any]:
        """
        Compute all feature categories.
        Returns a dictionary ready for model input.
        """
        if len(self.history) < 5:
            return self._get_empty_features()

        df = self._to_dataframe()
        
        features = {
            "rolling_stats": self._compute_rolling_stats(df),
            "pressure_indices": self._compute_pressure(df),
            "dna_signature": self._compute_dna(df),
            "lag_features": self._compute_lags(df),
            "color_encoding": self._encode_colors(df),
            "band_encoding": self._encode_bands(df),
            "feature_vector": self._build_vector(df)
        }
        
        return features

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert history deque to pandas DataFrame."""
        return pd.DataFrame(list(self.history))

    def _compute_rolling_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compute rolling statistics (MA, EMA, Volatility)."""
        multipliers = df['multiplier']
        
        return {
            "ma_5": float(multipliers.tail(5).mean()),
            "ma_10": float(multipliers.tail(10).mean()),
            "ma_20": float(multipliers.tail(20).mean()),
            "ema_5": float(multipliers.ewm(span=5, adjust=False).mean().iloc[-1]),
            "volatility_10": float(multipliers.tail(10).std()),
            "max_recent": float(multipliers.tail(10).max()),
            "min_recent": float(multipliers.tail(10).min()),
            "skewness": float(multipliers.tail(20).skew()),
            "kurtosis": float(multipliers.tail(20).kurtosis())
        }

    def _compute_pressure(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute buy/sell pressure indices.
        High multiplier = 'sell' pressure (market pays out)
        Low multiplier = 'buy' pressure (market accumulates)
        """
        multipliers = df['multiplier']
        recent = multipliers.tail(10)
        
        # Pressure: % of rounds below 2.0x (accumulation phase)
        accumulation_rate = (recent < 2.0).sum() / len(recent)
        
        # Payout intensity: average of rounds > 5.0x
        payout_intensity = recent[recent > 5.0].mean() if (recent > 5.0).any() else 0.0
        
        return {
            "accumulation_pressure": float(accumulation_rate),
            "payout_intensity": float(payout_intensity),
            "pressure_balance": float(accumulation_rate - (payout_intensity / 20.0))
        }

    def _compute_dna(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Compute DNA-like pattern signatures.
        Encodes recent sequence into hashable string.
        """
        # Color sequence (last 10)
        color_seq = ''.join(df['color'].tail(10).str[0].str.upper())
        
        # Band sequence (last 10)
        band_seq = ''.join(df['band'].tail(10).str[0].str.upper())
        
        # Multiplier tier sequence (L=low, M=med, H=high)
        def tier(m):
            if m < 2.0: return 'L'
            elif m < 10.0: return 'M'
            else: return 'H'
        
        tier_seq = ''.join([tier(m) for m in df['multiplier'].tail(10)])
        
        return {
            "color_dna": color_seq,
            "band_dna": band_seq,
            "tier_dna": tier_seq,
            "combined_hash": hash(color_seq + band_seq + tier_seq)
        }

    def _compute_lags(self, df: pd.DataFrame) -> Dict[str, float]:
        """Create lag features (t-1, t-2, t-3...)."""
        multipliers = df['multiplier']
        
        return {
            "lag_1": float(multipliers.iloc[-2]) if len(multipliers) > 1 else 0.0,
            "lag_2": float(multipliers.iloc[-3]) if len(multipliers) > 2 else 0.0,
            "lag_3": float(multipliers.iloc[-4]) if len(multipliers) > 3 else 0.0,
            "lag_5": float(multipliers.iloc[-6]) if len(multipliers) > 5 else 0.0,
            "diff_1": float(multipliers.iloc[-1] - multipliers.iloc[-2]) if len(multipliers) > 1 else 0.0,
            "diff_2": float(multipliers.iloc[-2] - multipliers.iloc[-3]) if len(multipliers) > 2 else 0.0,
        }

    def _encode_colors(self, df: pd.DataFrame) -> Dict[str, int]:
        """One-hot encode last color."""
        last_color = df['color'].iloc[-1]
        return {
            "is_blue": 1 if last_color == "blue" else 0,
            "is_purple": 1 if last_color == "purple" else 0,
            "is_pink": 1 if last_color == "pink" else 0
        }

    def _encode_bands(self, df: pd.DataFrame) -> Dict[str, int]:
        """One-hot encode last band."""
        last_band = df['band'].iloc[-1]
        return {
            "is_nano": 1 if last_band == "nano" else 0,
            "is_micro": 1 if last_band == "micro" else 0,
            "is_macro": 1 if last_band == "macro" else 0,
            "is_mega": 1 if last_band == "mega" else 0,
            "is_cosmic": 1 if last_band == "cosmic" else 0
        }

    def _build_vector(self, df: pd.DataFrame) -> List[float]:
        """
        Build flattened feature vector for ML model input.
        Order must be consistent with training.
        """
        stats = self._compute_rolling_stats(df)
        pressure = self._compute_pressure(df)
        lags = self._compute_lags(df)
        colors = self._encode_colors(df)
        bands = self._encode_bands(df)
        
        # Fixed order vector
        vector = [
            stats['ma_5'], stats['ma_10'], stats['ma_20'],
            stats['ema_5'], stats['volatility_10'],
            stats['max_recent'], stats['min_recent'],
            pressure['accumulation_pressure'], pressure['payout_intensity'],
            lags['lag_1'], lags['lag_2'], lags['lag_3'],
            lags['diff_1'], lags['diff_2'],
            colors['is_blue'], colors['is_purple'], colors['is_pink'],
            bands['is_nano'], bands['is_micro'], bands['is_macro'],
            bands['is_mega'], bands['is_cosmic']
        ]
        
        return vector

    def _get_empty_features(self) -> Dict[str, Any]:
        """Return zero-filled features when insufficient history."""
        return {
            "rolling_stats": {},
            "pressure_indices": {},
            "dna_signature": {},
            "lag_features": {},
            "color_encoding": {},
            "band_encoding": {},
            "feature_vector": []
        }
