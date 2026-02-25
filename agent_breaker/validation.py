from pathlib import Path
from typing import List
from agent_breaker.config import BreakerConfig


def validate_config(config: BreakerConfig) -> List[str]:
    """
    Validate breaker.yaml configuration and return list of error messages.
    
    Returns:
        List of error strings. Empty list if config is valid.
    """
    errors = []
    
    # Validate target exists
    if config.target is None:
        errors.append("target: No target specified in breaker.yaml")
        return errors  # Can't validate target fields if target doesn't exist
    
    # Validate LangGraph-specific requirements
    if config.target.type == "langgraph":
        # Check required fields
        if config.target.path is None:
            errors.append("target.path: Required for langgraph targets")
        elif not Path(config.target.path).exists():
            errors.append(f"target.path: File '{config.target.path}' does not exist")
        
        if config.target.attr is None:
            errors.append("target.attr: Required for langgraph targets (e.g., 'graph')")
        
        if config.target.input_key is None:
            errors.append("target.input_key: Required for langgraph targets (e.g., 'user_query')")
        
        if config.target.output_key is None:
            errors.append("target.output_key: Required for langgraph targets (e.g., 'response')")
        
        if config.target.state_class is None:
            errors.append("target.state_class: Required for langgraph targets (e.g., 'AgentState')")

        if config.target.prompt_variable is None:
            errors.append("target.prompt_variable: Required for langgraph targets (e.g.,'System_prompt')")
    
    # Validate attacks
    if not config.attacks:
        errors.append("attacks: At least one attack must be configured")
    else:
        enabled_count = 0
        for i, attack in enumerate(config.attacks):
            if attack.name is None or attack.name == "":
                errors.append(f"attacks[{i}].name: Attack name is required")
            
            if attack.enabled:
                enabled_count += 1
                if attack.max_api_calls <= 0:
                    errors.append(f"attacks[{i}].max_api_calls: Must be greater than 0 (got {attack.max_api_calls})")
        
        if enabled_count == 0:
            errors.append("attacks: At least one attack must be enabled")
    
    # Validate budget
    if config.budget.max_tokens <= 0:
        errors.append(f"budget.max_tokens: Must be greater than 0 (got {config.budget.max_tokens})")
    
    return errors
