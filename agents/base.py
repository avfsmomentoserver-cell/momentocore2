"""
Base Agent Class for MomentoCore
Provides unified interface for all AI agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class for all MomentoCore AI agents.
    
    Attributes:
        name: Unique agent identifier
        version: Agent version string
        state: Current agent state (idle, running, error)
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.state = "idle"
        self.created_at = datetime.utcnow()
        self.logger = logging.getLogger(f"agents.{name}")
        
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's primary function.
        
        Returns:
            Dictionary containing execution results
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check agent health status.
        
        Returns:
            Dictionary with health metrics
        """
        pass
    
    def set_state(self, state: str):
        """Update agent state."""
        self.state = state
        self.logger.info(f"Agent {self.name} state changed to: {state}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "state": self.state,
            "created_at": self.created_at.isoformat()
        }
