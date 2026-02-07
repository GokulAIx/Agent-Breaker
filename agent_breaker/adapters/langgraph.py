"""
LangGraph adapter for Agent Breaker.
Loads and executes compiled LangGraph graphs.
"""
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from agent_breaker.targets import AgentTarget


class LangGraphTarget(AgentTarget):
    """Target adapter for LangGraph compiled graphs."""
    
    def __init__(
        self,
        graph_path: str,
        graph_attr: str,
        input_key: str = "user_query",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize LangGraph target.
        
        Args:
            graph_path: Path to Python file containing compiled graph
            graph_attr: Attribute name of the compiled graph
            input_key: Key to inject payload into initial state
            system_prompt: Optional system prompt (if not extractable from graph)
        """
        self.graph_path = Path(graph_path)
        self.graph_attr = graph_attr
        self.input_key = input_key
        self._system_prompt = system_prompt
        self.call_count = 0
        self.history = []
        
        # Load the graph
        self.graph = self._load_graph()
        
        # Try to extract system prompt if not provided
        if not self._system_prompt:
            self._system_prompt = self._extract_system_prompt()
    
    def _load_graph(self):
        """Load compiled graph from file."""
        if not self.graph_path.exists():
            raise FileNotFoundError(f"Graph file not found: {self.graph_path}")
        
        # Load module dynamically
        spec = importlib.util.spec_from_file_location("user_graph", self.graph_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {self.graph_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules["user_graph"] = module
        spec.loader.exec_module(module)
        
        # Get graph attribute
        if not hasattr(module, self.graph_attr):
            raise AttributeError(
                f"Module {self.graph_path} does not have attribute '{self.graph_attr}'"
            )
        
        graph = getattr(module, self.graph_attr)
        
        # Verify it's a compiled graph (has invoke method)
        if not hasattr(graph, 'invoke'):
            raise TypeError(
                f"'{self.graph_attr}' is not a compiled LangGraph (missing 'invoke' method)"
            )
        
        return graph
    
    def _extract_system_prompt(self) -> str:
        """Attempt to extract system prompt from graph metadata."""
        # Try common locations for system prompts
        
        # 1. Check loaded module for SYSTEM_PROMPT variable
        if "user_graph" in sys.modules:
            module = sys.modules["user_graph"]
            for attr_name in ['SYSTEM_PROMPT', 'system_prompt', 'SYSTEM_MESSAGE', 'PROMPT']:
                if hasattr(module, attr_name):
                    prompt = getattr(module, attr_name)
                    if isinstance(prompt, str) and prompt:
                        return prompt
        
        # 2. Check graph config
        if hasattr(self.graph, 'config') and isinstance(self.graph.config, dict):
            if 'system_prompt' in self.graph.config:
                return self.graph.config['system_prompt']
            if 'system' in self.graph.config:
                return self.graph.config['system']
        
        # 3. Check nodes for system messages
        if hasattr(self.graph, 'nodes'):
            for node in self.graph.nodes.values():
                if hasattr(node, 'system_prompt'):
                    return node.system_prompt
                if hasattr(node, 'system_message'):
                    return node.system_message
        
        # Default fallback
        return "System prompt not extractable from graph"
    
    def send(self, payload: str) -> str:
        """
        Send payload to LangGraph and return response.
        
        Args:
            payload: Adversarial payload to inject
            
        Returns:
            Agent response as string
        """
        self.call_count += 1
        self.history.append(payload)
        
        try:
            # Build input state with payload
            # CRITICAL: Reset state fields to ensure stateless execution
            # If graph has 'messages' or other accumulator fields, they'll persist across calls
            input_state = {
                self.input_key: payload,
                "messages": [],  # Reset conversation history
            }
            
            # Invoke graph with fresh state AND unique thread_id for isolation
            # thread_id ensures each invoke is truly independent (no state sharing)
            config = {"configurable": {"thread_id": f"test_{self.call_count}"}}
            result = self.graph.invoke(input_state, config=config)
            
            # Extract response from result
            # LangGraph typically returns final state dict
            response = self._extract_response(result)
            
            return response
            
        except Exception as e:
            # Detect rate limit errors across all providers
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check for rate limit indicators (works for OpenAI, Anthropic, Gemini, Azure)
            rate_limit_indicators = [
                '429',                      # HTTP status code (all providers)
                'rate limit',               # Generic rate limit message
                'ratelimit',                # Compact form
                'rate_limit_exceeded',      # OpenAI
                'rate_limit_error',         # Anthropic
                'resource_exhausted',       # Gemini/gRPC
                'quota exceeded',           # Gemini/Azure
                'too many requests',        # Generic HTTP
                'toomanyrequests',          # Azure compact form
            ]
            
            is_rate_limit = (
                any(indicator in error_str for indicator in rate_limit_indicators) or
                'ratelimit' in error_type.lower()
            )
            
            if is_rate_limit:
                # Return standardized rate limit message for judge detection
                return f"⚠️ RATE_LIMIT: {error_type}: {str(e)[:200]}"
            else:
                # Return generic error
                return f"Error executing graph: {str(e)}"
    
    def _extract_response(self, result: Any) -> str:
        """Extract response string from graph result."""
        # Handle different result formats
        if isinstance(result, str):
            return result
        
        if isinstance(result, dict):
            # Common output keys
            for key in ['output', 'response', 'result', 'answer', 'messages']:
                if key in result:
                    value = result[key]
                    
                    # Handle messages list
                    if isinstance(value, list) and value:
                        last_msg = value[-1]
                        if isinstance(last_msg, dict):
                            # Check for nested text content (Gemini format)
                            if 'text' in last_msg:
                                return str(last_msg['text'])
                            if 'content' in last_msg:
                                content = last_msg['content']
                                # Content might also be nested dict with 'text' key
                                if isinstance(content, dict) and 'text' in content:
                                    return str(content['text'])
                                return str(content)
                        return str(last_msg)
                    
                    # Handle nested dict with 'text' key (Gemini format)
                    if isinstance(value, dict) and 'text' in value:
                        return str(value['text'])
                    
                    return str(value)
            
            # Check top-level for 'text' key (direct Gemini format)
            if 'text' in result:
                return str(result['text'])
            
            # Check for 'content' at top level
            if 'content' in result:
                content = result['content']
                if isinstance(content, dict) and 'text' in content:
                    return str(content['text'])
                return str(content)
            
            # Fallback: stringify entire result
            return str(result)
        
        # Last resort
        return str(result)
    
    def _extract_capabilities(self) -> Dict[str, Any]:
        """Extract agent capabilities from graph structure."""
        capabilities = {
            "tools": [],
            "nodes": [],
            "has_tools": False,
        }
        
        try:
            # Get graph structure
            graph_def = self.graph.get_graph()
            
            # Extract node names (filter out system nodes)
            system_nodes = {'__start__', '__end__'}
            user_nodes = [
                node for node in graph_def.nodes 
                if node not in system_nodes
            ]
            capabilities["nodes"] = user_nodes
            
            # Try to extract tools from the loaded module
            if "user_graph" in sys.modules:
                module = sys.modules["user_graph"]
                
                # Look for tools in common locations
                for attr_name in dir(module):
                    if attr_name.startswith('_'):
                        continue
                        
                    attr = getattr(module, attr_name)
                    
                    # Check for LangChain tool (has name, description, and invoke/run methods)
                    if hasattr(attr, 'name') and hasattr(attr, 'description'):
                        tool_name = getattr(attr, 'name', attr_name)
                        tool_desc = getattr(attr, 'description', 'No description')
                        
                        capabilities["tools"].append({
                            "name": tool_name,
                            "description": tool_desc
                        })
                        capabilities["has_tools"] = True
                    
                    # Check for lists of tools (common pattern: tools = [tool1, tool2])
                    elif isinstance(attr, list) and attr:
                        for item in attr:
                            if hasattr(item, 'name') and hasattr(item, 'description'):
                                capabilities["tools"].append({
                                    "name": item.name,
                                    "description": item.description
                                })
                                capabilities["has_tools"] = True
                
                # Check for ToolNode in graph
                for node_name in user_nodes:
                    if 'tool' in node_name.lower():
                        capabilities["has_tools"] = True
                        
        except Exception:
            # Silently fail - capabilities are optional
            pass
        
        return capabilities
    
    def get_context(self) -> Dict[str, Any]:
        """Get target context for payload generation."""
        capabilities = self._extract_capabilities()
        
        context = {
            "system_prompt": self._system_prompt,
            "type": "langgraph",
            "graph_path": str(self.graph_path),
            "graph_attr": self.graph_attr,
            "input_key": self.input_key,
            "call_count": self.call_count,
            "capabilities": capabilities,
        }
        
        # Add graph metadata if available
        if hasattr(self.graph, 'nodes'):
            context["node_count"] = len(self.graph.nodes)
            context["node_names"] = list(self.graph.nodes.keys()) if hasattr(self.graph.nodes, 'keys') else []
        
        if hasattr(self.graph, 'edges'):
            context["edge_count"] = len(self.graph.edges)
        
        return context
    
    def get_system_prompt(self) -> str:
        """Get the extracted system prompt."""
        return self._system_prompt
