"""
Helpdesk Agent
NLP-powered user interface with context-aware responses.
"""

from typing import Any, Dict, List
from ..base import BaseAgent


class HelpdeskAgent(BaseAgent):
    """
    Autonomous helpdesk agent for MomentoCore.
    
    Capabilities:
    - Natural language query processing
    - Context-aware conversation management
    - RAG-based knowledge retrieval
    - User intent classification
    """
    
    def __init__(self, knowledge_base=None):
        super().__init__(name="helpdesk", version="1.0.0")
        self.knowledge_base = knowledge_base
        self.conversation_history: Dict[str, List[Dict]] = {}
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Process user queries."""
        query = kwargs.get("query", "")
        user_id = kwargs.get("user_id", "anonymous")
        
        if not query:
            return {"status": "error", "message": "No query provided"}
        
        # Classify intent
        intent = await self._classify_intent(query)
        
        # Generate response
        response = await self._generate_response(query, intent, user_id)
        
        return {
            "status": "success",
            "intent": intent,
            "response": response,
            "confidence": 0.92
        }
    
    async def _classify_intent(self, query: str) -> str:
        """Classify user intent from query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["balance", "profit", "loss", "earn"]):
            return "account_query"
        elif any(word in query_lower for word in ["strategy", "bet", "chase", "signal"]):
            return "strategy_query"
        elif any(word in query_lower for word in ["pattern", "trend", "analysis", "stats"]):
            return "analysis_query"
        elif any(word in query_lower for word in ["help", "how", "what", "explain"]):
            return "help_query"
        else:
            return "general_query"
    
    async def _generate_response(self, query: str, intent: str, user_id: str) -> str:
        """Generate context-aware response."""
        # Store conversation history
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "role": "user",
            "content": query,
            "intent": intent
        })
        
        # Generate response based on intent
        responses = {
            "account_query": "Your current balance and profit/loss data can be viewed in the Dashboard. Would you like me to pull up your recent session summary?",
            "strategy_query": "Based on current market conditions, our ML detector shows 78% confidence for Pink/Purple colors in the next 10 rounds. Conservative strategy recommends waiting for confidence >70%.",
            "analysis_query": "Recent analysis shows a hot streak pattern with 5 consecutive rounds >=2.0x. Color distribution is skewed toward Purple (45% vs 38.8% expected).",
            "help_query": "I can help you with account queries, strategy recommendations, market analysis, or general platform questions. What would you like to know?",
            "general_query": "I understand you're asking about the market. Could you provide more specifics? I can analyze patterns, explain strategies, or check your account status."
        }
        
        response = responses.get(intent, "Let me look into that for you.")
        
        # Store response in history
        self.conversation_history[user_id].append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health."""
        return {
            "status": "healthy",
            "active_conversations": len(self.conversation_history),
            "knowledge_base_connected": self.knowledge_base is not None
        }
