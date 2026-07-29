"""
ChaseStrategy - Betting strategies based on detector signals
Implements Conservative, Moderate, Aggressive, and Sniper modes
"""
from typing import Dict, Optional, List
from enum import Enum


class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    SNIPER = "sniper"


class ChaseStrategy:
    """
    Implements betting strategies based on market signals.
    
    Strategies:
    - Conservative: Only bet on >70% confidence, half stakes
    - Moderate: Bet on >50% confidence, normal stakes
    - Aggressive: Scale bet size with confidence, include loss recovery
    - Sniper: Wait for perfect setup (Color+BAND signal)
    """

    def __init__(self, base_stake: float = 10.0, risk_level: RiskLevel = RiskLevel.MODERATE):
        """
        Initialize strategy with base stake and risk level.
        
        Args:
            base_stake: Default bet amount (default: $10)
            risk_level: Strategy risk profile (default: MODERATE)
        """
        self.base_stake = base_stake
        self.risk_level = risk_level
        self.balance = 1000.0
        self.consecutive_losses = 0
        self.total_profit = 0.0

    def calculate_bet(self, signal: Dict) -> Optional[float]:
        """
        Calculate bet size based on signal and risk level.
        
        Args:
            signal: Signal dictionary from MarketDetector
            
        Returns:
            Bet amount if should bet, None if should wait
        """
        confidence = signal.get("confidence", 0.0)
        pattern_type = signal.get("pattern_type", "")
        action = signal.get("action", "WAIT")
        
        if action == "WAIT":
            return None
        
        # Check confidence threshold based on risk level
        thresholds = {
            RiskLevel.CONSERVATIVE: 0.70,
            RiskLevel.MODERATE: 0.50,
            RiskLevel.AGGRESSIVE: 0.40,
            RiskLevel.SNIPER: 0.80
        }
        
        min_confidence = thresholds[self.risk_level]
        if confidence < min_confidence:
            return None
        
        # Sniper mode: require specific pattern combination
        if self.risk_level == RiskLevel.SNIPER:
            metadata = signal.get("metadata", {})
            has_color = metadata.get("pink_count", 0) > 0 or metadata.get("purple_count", 0) > 0
            has_band = metadata.get("high_band_ratio", 0) > 0.3
            if not (has_color and has_band):
                return None
        
        # Calculate bet size
        bet_size = self._calculate_stake(confidence, action)
        
        # Ensure we don't bet more than available balance
        if bet_size > self.balance * 0.5:  # Max 50% of balance
            bet_size = self.balance * 0.5
        
        return round(bet_size, 2)

    def _calculate_stake(self, confidence: float, action: str) -> float:
        """Calculate stake based on risk level and confidence."""
        
        if self.risk_level == RiskLevel.CONSERVATIVE:
            return self.base_stake * 0.5
        
        elif self.risk_level == RiskLevel.MODERATE:
            return self.base_stake
        
        elif self.risk_level == RiskLevel.AGGRESSIVE:
            # Scale with confidence and add loss recovery
            multiplier = 1.0 + (confidence - 0.5) * 2.0
            if self.consecutive_losses > 0:
                # Martingale-lite: increase after losses
                multiplier *= (1.0 + self.consecutive_losses * 0.2)
            return self.base_stake * multiplier
        
        elif self.risk_level == RiskLevel.SNIPER:
            # High confidence, high stake
            return self.base_stake * 2.0
        
        return self.base_stake

    def update_balance(self, bet_amount: float, multiplier: float, won: bool):
        """
        Update balance after a bet result.
        
        Args:
            bet_amount: Amount wagered
            multiplier: Round multiplier
            won: Whether the bet won (cashed out before crash)
        """
        if won:
            profit = bet_amount * (multiplier - 1)
            self.balance += profit
            self.total_profit += profit
            self.consecutive_losses = 0
        else:
            self.balance -= bet_amount
            self.total_profit -= bet_amount
            self.consecutive_losses += 1

    def get_stats(self) -> Dict:
        """Return current strategy statistics."""
        return {
            "balance": round(self.balance, 2),
            "total_profit": round(self.total_profit, 2),
            "consecutive_losses": self.consecutive_losses,
            "risk_level": self.risk_level.value,
            "base_stake": self.base_stake
        }

    def reset(self):
        """Reset strategy state."""
        self.balance = 1000.0
        self.consecutive_losses = 0
        self.total_profit = 0.0


class AutoChaseBot:
    """
    Automated bot that combines detector and strategy.
    """

    def __init__(self, risk_level: RiskLevel = RiskLevel.MODERATE):
        from .detector import MarketDetector
        self.detector = MarketDetector()
        self.strategy = ChaseStrategy(risk_level=risk_level)
        self.signals_received = 0
        self.bets_placed = 0

    def process_round(self, round_data: Dict) -> Optional[Dict]:
        """
        Process a new round through detector and strategy.
        
        Args:
            round_data: Round dictionary
            
        Returns:
            Action dictionary if bet placed, None otherwise
        """
        # Run detection
        signal = self.detector.add_round(round_data)
        
        if not signal:
            return None
        
        self.signals_received += 1
        
        # Calculate bet
        bet_amount = self.strategy.calculate_bet(signal)
        
        if not bet_amount:
            return {
                "action": "WAIT",
                "signal": signal,
                "reason": "Below confidence threshold or unfavorable conditions"
            }
        
        self.bets_placed += 1
        
        return {
            "action": "BET",
            "bet_amount": bet_amount,
            "signal": signal,
            "strategy_stats": self.strategy.get_stats()
        }

    def get_performance(self) -> Dict:
        """Get bot performance metrics."""
        return {
            "signals_received": self.signals_received,
            "bets_placed": self.bets_placed,
            "bet_ratio": self.bets_placed / max(1, self.signals_received),
            "strategy_stats": self.strategy.get_stats()
        }
