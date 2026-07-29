"""
SQLAlchemy Models for MomentoCore Data Storage.
Defines schema for rounds, sessions, signals, and features.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Index, Text
from sqlalchemy.sql import func
from .database import Base

class Round(Base):
    """
    Stores individual game round data.
    Core entity for all analysis.
    """
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(String, unique=True, nullable=False, index=True)  # External ID
    multiplier = Column(Float, nullable=False)
    color = Column(String, nullable=False)  # blue, purple, pink
    band = Column(String, nullable=False)   # nano, micro, macro, mega, cosmic
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metadata
    hash = Column(String, unique=True, nullable=False)  # For deduplication
    source = Column(String, default="api")  # api, file, kafka
    
    # Indices
    __table_args__ = (
        Index('idx_rounds_color_time', 'color', 'timestamp'),
        Index('idx_rounds_band_time', 'band', 'timestamp'),
    )

class Session(Base):
    """
    Groups consecutive rounds into logical sessions.
    Created by Sessionizer processing.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    round_count = Column(Integer, nullable=False)
    total_multiplier = Column(Float, nullable=False)
    avg_multiplier = Column(Float, nullable=False)
    
    # Session Classification
    is_hot = Column(Boolean, default=False)  # Contains streak >= 3
    dominant_color = Column(String)
    dominant_band = Column(String)
    
    # Foreign Keys (logical, not enforced for flexibility)
    # round_ids stored as JSON array for simplicity
    round_ids = Column(JSON)

class Signal(Base):
    """
    ML-generated trading signals.
    Output from Detector/Strategy engines.
    """
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String, unique=True, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=func.now())
    
    # Signal Details
    action = Column(String, nullable=False)  # BUY, WAIT, SELL
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    predicted_multiplier = Column(Float)
    target_color = Column(String)
    target_band = Column(String)
    
    # Strategy Context
    strategy_type = Column(String)  # conservative, moderate, aggressive, sniper
    stake_recommendation = Column(Float)
    
    # Reasoning
    reasons = Column(JSON)  # List of triggered patterns
    model_version = Column(String, default="v1.0")
    
    # Status
    is_active = Column(Boolean, default=True)
    result = Column(String)  # WIN, LOSS, PENDING (filled post-round)
    actual_multiplier = Column(Float)
    
    __table_args__ = (
        Index('idx_signals_action_time', 'action', 'generated_at'),
        Index('idx_signals_confidence', 'confidence'),
    )

class FeatureSet(Base):
    """
    Pre-computed features for ML inference.
    Cached to avoid re-computation.
    """
    __tablename__ = "feature_sets"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Feature Categories (stored as JSON for flexibility)
    rolling_stats = Column(JSON)  # MA, EMA, volatility
    pressure_indices = Column(JSON)  # Buy/sell pressure
    dna_signature = Column(JSON)  # Pattern hashes
    lag_features = Column(JSON)  # t-1, t-2, t-3 multipliers
    color_encoding = Column(JSON)  # One-hot encoded colors
    band_encoding = Column(JSON)  # One-hot encoded bands
    
    # Raw feature vector (for quick ML input)
    feature_vector = Column(JSON)

class AgentLog(Base):
    """
    Audit trail for AI Agent actions.
    Critical for debugging and compliance.
    """
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)  # orchestrator, research, etc.
    action = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    
    # Context
    input_data = Column(JSON)
    output_data = Column(JSON)
    decision_reasoning = Column(Text)
    
    # Performance
    execution_time_ms = Column(Float)
    status = Column(String)  # SUCCESS, ERROR, WARNING
    error_message = Column(Text)
