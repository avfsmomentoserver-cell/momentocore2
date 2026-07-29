"""Event Schema Definitions"""
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel


class EventSchema(BaseModel):
    """Base event schema for all MomentoCore events."""
    event_id: str
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]
    source: str = "momentocore"
    version: str = "1.0.0"


class RoundIngestedEvent(EventSchema):
    """Event triggered when a new round is ingested."""
    round_id: str
    multiplier: float
    color: str
    band: str


class SignalGeneratedEvent(EventSchema):
    """Event triggered when ML detector generates a signal."""
    signal_type: str  # "BUY", "SELL", "WAIT"
    confidence: float
    recommended_stake: float
    reasoning: str


class AlertTriggeredEvent(EventSchema):
    """Event triggered on critical system alerts."""
    alert_level: str  # "INFO", "WARNING", "CRITICAL"
    message: str
    actionable: bool
