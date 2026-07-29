"""
Sessionizer - Groups rounds into sessions based on time gaps
"""
from typing import List, Dict
from datetime import datetime, timedelta


class Sessionizer:
    """
    Groups rounds into sessions based on time gaps.
    A new session starts when the gap between rounds exceeds `gap_seconds`.
    """

    def __init__(self, gap_seconds: int = 300):
        """
        Initialize sessionizer with gap threshold.
        
        Args:
            gap_seconds: Maximum seconds between rounds to stay in same session (default: 5 min)
        """
        self.gap_seconds = gap_seconds

    def sessionize(self, rounds: List[Dict]) -> List[List[Dict]]:
        """
        Group rounds into sessions.

        Args:
            rounds: List of round dictionaries with 'timestamp' keys.

        Returns:
            List of sessions, where each session is a list of rounds.
        """
        if not rounds:
            return []

        # Sort rounds by timestamp
        rounds = sorted(rounds, key=lambda x: x["timestamp"])

        sessions = []
        current_session = [rounds[0]]

        for round in rounds[1:]:
            prev_timestamp = datetime.fromisoformat(current_session[-1]["timestamp"].replace("Z", "+00:00"))
            curr_timestamp = datetime.fromisoformat(round["timestamp"].replace("Z", "+00:00"))
            gap = (curr_timestamp - prev_timestamp).total_seconds()

            if gap > self.gap_seconds:
                sessions.append(current_session)
                current_session = [round]
            else:
                current_session.append(round)

        if current_session:
            sessions.append(current_session)

        return sessions

    def sessionize_with_stats(self, rounds: List[Dict]) -> List[Dict]:
        """
        Group rounds into sessions and compute statistics for each.
        
        Args:
            rounds: List of round dictionaries
            
        Returns:
            List of session dictionaries with metadata
        """
        sessions = self.sessionize(rounds)
        result = []
        
        for idx, session in enumerate(sessions):
            multipliers = [r["multiplier"] for r in session]
            result.append({
                "session_id": f"sess_{idx:04d}",
                "start_time": session[0]["timestamp"],
                "end_time": session[-1]["timestamp"],
                "round_count": len(session),
                "avg_multiplier": sum(multipliers) / len(multipliers),
                "max_multiplier": max(multipliers),
                "high_value_count": sum(1 for m in multipliers if m >= 2.0),
                "round_ids": [r["round_id"] for r in session]
            })
        
        return result
