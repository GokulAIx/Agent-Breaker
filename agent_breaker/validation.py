from pathlib import Path
from typing import List
import importlib.util
from importlib import resources
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
            
            # Validate attack name against known attacks
            VALID_ATTACKS = ["prompt_injection"]
            if attack.name and attack.name.lower() not in VALID_ATTACKS:
                errors.append(
                    f"attacks[{i}].name: Unknown attack '{attack.name}'. "
                    f"Available: {', '.join(VALID_ATTACKS)}"
                )
            
            if attack.enabled:
                enabled_count += 1
                if attack.max_api_calls <= 0:
                    errors.append(f"attacks[{i}].max_api_calls: Must be greater than 0 (got {attack.max_api_calls})")
        
        if enabled_count == 0:
            errors.append("attacks: At least one attack must be enabled")
    
    # Validate budget
    if config.budget.max_tokens <= 0:
        errors.append(f"budget.max_tokens: Must be greater than 0 (got {config.budget.max_tokens})")
    
    judge_model = config.judge.model.lower()
    valid_judges = ["behaviour", "behavior", "ml", "neural"]
    if judge_model not in valid_judges:
        errors.append(
            f"judge.model: Invalid judge '{config.judge.model}'. "
            f"Available: behaviour, ml"
        )

    if judge_model in ["ml", "neural"]:
        missing_packages = []

        if importlib.util.find_spec("torch") is None:
            missing_packages.append("torch")

        if importlib.util.find_spec("sentence_transformers") is None:
            missing_packages.append("sentence-transformers")

        if missing_packages:
            errors.append(
                "judge.model: ML judge selected but optional ML dependencies are not installed. "
                "Run: pip install agent-breaker[ml] "
                f"(missing: {', '.join(missing_packages)})"
            )

        if config.judge.model_path and not Path(config.judge.model_path).exists():
            errors.append(
                f"judge.model_path: File '{config.judge.model_path}' does not exist"
            )
        elif not config.judge.model_path:
            packaged_model = resources.files("agent_breaker").joinpath("agent_breaker_ml_classifier.pt")
            if not packaged_model.is_file():
                errors.append(
                    "judge.model: Bundled ML model is missing from the package. "
                    "Reinstall agent-breaker[ml] or provide judge.model_path explicitly."
                )
        

    if config.generator.strategy != "template":
        errors.append(
        f"generator.strategy: Only 'template' is currently supported. "
        f"LLM generators are planned for a future version"
    )    
    
    # Validate generator domain
    VALID_DOMAINS = ["finance", "healthcare", "legal", "devops", "customer_service", "hr", "ecommerce", "content_moderation", "general"]
    if config.generator and config.generator.domain not in VALID_DOMAINS:
        errors.append(
            f"generator.domain: Invalid domain '{config.generator.domain}'. "
            f"Available: {', '.join(VALID_DOMAINS)}"
        )
    
    return errors
