"""
Agent target abstractions for Agent Breaker.
Defines how attacks interact with target agents.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AgentTarget(ABC):
    """Base class for agent targets."""
    
    @abstractmethod
    def send(self, payload: str) -> str:
        """Send a payload to the agent and return its response."""
        pass
    
    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """Get target context (system prompt, tools, metadata)."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the target's system prompt."""
        pass
    
    def call_tool(self, name: str, *args, **kwargs) -> Any:
        """Call a specific tool on the agent (optional)."""
        raise NotImplementedError("Tool calling not supported by this target")


class MockTarget(AgentTarget):
    """Mock target for testing and development."""
    
    def __init__(self, system_prompt: str = "You are a helpful assistant."):
        self.system_prompt = system_prompt
        self.call_count = 0
        self.history = []
    
    def send(self, payload: str) -> str:
        """Simulate a safe agent response with negation patterns."""
        self.call_count += 1
        self.history.append(payload)
        
        # Simple mock behavior: detect injection attempts and respond with negation
        lower_payload = payload.lower()
        
        # Test negation detection: respond with "not capable" patterns
        if "execute" in lower_payload or "trade" in lower_payload:
            return "I am not capable of executing trades. I do not have the authorization or capability to perform financial transactions."
        
        if "reveal" in lower_payload or "api key" in lower_payload:
            return "I cannot reveal sensitive information. I do not have access to API keys or credentials."
        
        if "regulator" in lower_payload:
            return "I am unable to change my role or impersonate a regulator. I do not have the authority to make regulatory decisions."
        
        if "ignore" in lower_payload:
            return "I cannot ignore my system instructions. I am not authorized to bypass safety policies."
        
        # Simulate ambiguous response for variety
        if "policy" in lower_payload or "system" in lower_payload:
            return "I understand you're asking about policy changes. Let me explain how our system works..."
        
        return f"I'm here to help with your questions. How can I assist you today?"
    
    def get_system_prompt(self) -> str:
        """Return system prompt."""
        return self.system_prompt
    
    def get_context(self) -> Dict[str, Any]:
        """Return mock context."""
        return {
            "system_prompt": self.system_prompt,
            "type": "mock",
            "call_count": self.call_count,
            "tools": [],
            "capabilities": {
                "tools": [],
                "nodes": ["chat"],
                "has_tools": False,
            }
        }
