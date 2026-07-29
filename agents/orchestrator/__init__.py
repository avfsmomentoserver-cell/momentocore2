"""
Orchestrator Agent
Central brain for workflow coordination and agent dispatch.
"""

import asyncio
from typing import Any, Dict, List
from .base import BaseAgent


class OrchestratorAgent(BaseAgent):
    """
    Coordinates workflows across all MomentoCore agents.
    
    Responsibilities:
    - Receive incoming events (rounds, signals, user requests)
    - Dispatch tasks to appropriate agents
    - Monitor agent health and performance
    - Aggregate results and trigger downstream actions
    """
    
    def __init__(self):
        super().__init__(name="orchestrator", version="1.0.0")
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, List[str]] = {}
        
    def register_agent(self, agent_name: str, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent_name] = agent
        self.logger.info(f"Registered agent: {agent_name}")
    
    def define_workflow(self, workflow_name: str, agent_sequence: List[str]):
        """Define a workflow as a sequence of agent executions."""
        self.workflows[workflow_name] = agent_sequence
        self.logger.info(f"Defined workflow '{workflow_name}': {agent_sequence}")
    
    async def execute(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow based on event type.
        
        Args:
            event_type: Type of incoming event (e.g., 'round_ingested', 'user_query')
            payload: Event data
            
        Returns:
            Aggregated results from all agents in the workflow
        """
        self.set_state("running")
        results = {}
        
        # Determine workflow based on event type
        workflow_map = {
            "round_ingested": "data_pipeline",
            "signal_detected": "alert_workflow",
            "user_query": "helpdesk_workflow",
            "system_health_check": "health_workflow"
        }
        
        workflow_name = workflow_map.get(event_type, "default")
        
        if workflow_name not in self.workflows:
            self.logger.warning(f"No workflow defined for: {workflow_name}")
            return {"status": "no_workflow", "event_type": event_type}
        
        # Execute agents in sequence
        for agent_name in self.workflows[workflow_name]:
            if agent_name not in self.agents:
                self.logger.error(f"Agent not found: {agent_name}")
                continue
            
            agent = self.agents[agent_name]
            try:
                result = await agent.execute(**payload)
                results[agent_name] = result
                
                # Early termination on critical errors
                if result.get("status") == "critical_error":
                    self.logger.error(f"Critical error in {agent_name}, stopping workflow")
                    break
                    
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {str(e)}")
                results[agent_name] = {"status": "error", "message": str(e)}
        
        self.set_state("idle")
        return {"status": "completed", "workflow": workflow_name, "results": results}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all registered agents."""
        health_status = {
            "orchestrator": "healthy",
            "agents": {}
        }
        
        for name, agent in self.agents.items():
            try:
                agent_health = await agent.health_check()
                health_status["agents"][name] = agent_health
            except Exception as e:
                health_status["agents"][name] = {"status": "unhealthy", "error": str(e)}
        
        return health_status
    
    async def run_background_monitoring(self):
        """Continuously monitor agent health in background."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            health = await self.health_check()
            
            # Alert on unhealthy agents
            for name, status in health["agents"].items():
                if status.get("status") != "healthy":
                    self.logger.warning(f"Agent {name} is unhealthy: {status}")
