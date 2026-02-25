from pydantic import BaseModel, Field, AliasChoices
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any


class BudgetConfig(BaseModel):
    max_tokens: int = Field(..., gt=0)


class AttackConfig(BaseModel):
    name: str
    enabled: bool = True
    max_api_calls: int = Field(default=5, gt=0, description="Maximum API calls (payloads) for this attack")


class JudgeConfig(BaseModel):
    model: str = "behavior"  # behavior | gpt-4o-mini | claude-sonnet-4
    criteria: List[str] = ["refusal_detection", "data_leakage"]


class SystemPromptConfig(BaseModel):
    """Configuration for system prompt sourcing."""
    source: str = "inline"  # inline, env, file, graph, auto
    value: Optional[str] = None
    key: Optional[str] = None
    log: bool = False


class TargetConfig(BaseModel):
    """Configuration for target agent."""
    type: str  # langgraph, crewai
    path: Optional[str] = Field(None, validation_alias=AliasChoices('path', 'graph_path'))
    attr: Optional[str] = Field(None, validation_alias=AliasChoices('attr', 'graph_attr'))
    input_key: Optional[str] = None  # Field name for input in state (e.g., 'user_query', 'input', 'question')
    output_key: Optional[str] = None  # Field name for output in state (e.g., 'response', 'output', 'answer')
    state_class: Optional[str] = None  # Required for langgraph: name of state TypedDict class
    system_prompt: Optional[SystemPromptConfig] = None
    prompt_variable: Optional[str]=None #should be present the same file as the compiled graph

class GeneratorConfig(BaseModel):
    """Configuration for payload generator."""
    strategy: str = "template"  # template, llm, hybrid
    provider: Optional[str] = None  # openai, anthropic, ollama, github
    model: Optional[str] = None
    api_key: Optional[str] = None  # env ref like env://GEN_API_KEY
    seed: Optional[int] = None
    domain: str = "general"  # finance, healthcare, general


class BreakerConfig(BaseModel):
    version: str
    budget: BudgetConfig
    target: Optional[TargetConfig] = None
    generator: Optional[GeneratorConfig] = None
    attacks: List[AttackConfig]
    judge: JudgeConfig = JudgeConfig()  # Defaults to BehaviorJudge (rule-based)
