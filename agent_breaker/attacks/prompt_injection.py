from agent_breaker.targets import AgentTarget
from agent_breaker.config import BreakerConfig
from agent_breaker.judge import Judge, JudgeResult, JudgeVerdict
from typing import Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()


@dataclass
class AttackResult:
    """Result of an attack execution."""
    attack: str
    attack_class: str  # e.g., authority_override, policy_override
    payload: str
    response: str
    judge_result: Optional[JudgeResult]
    details: Dict[str, Any]
    
    @property
    def vulnerable(self) -> bool:
        """Check if attack revealed a vulnerability."""
        if not self.judge_result:
            return False
        return self.judge_result.verdict == JudgeVerdict.FAIL


class PromptInjectionAttack:
    """Prompt injection attack module."""
    name = "prompt_injection"

    def execute(
        self,
        target: AgentTarget,
        payload: str,
        config: BreakerConfig,
        judge: Judge
    ) -> AttackResult:
        """
        Execute prompt injection attack.
        
        Args:
            target: AgentTarget to test
            payload: Adversarial payload to send
            config: BreakerConfig instance
            judge: Judge instance for evaluation
            
        Returns:
            AttackResult with judge verdict
        """
        # Simple, clean payload display
        payload_preview = payload if len(payload) <= 100 else payload[:97] + "..."
        console.print(f"  [dim]Payload:[/dim] {payload_preview}")

        response = target.send(payload)

        # Simple, clean response display
        response_preview = response if len(response) <= 100 else response[:97] + "..."
        console.print(f"  [dim]Response:[/dim] {response_preview}")

        # Use judge to evaluate response
        judge_result = judge.evaluate(
            payload=payload,
            response=response,
            attack_name=self.name,
            criteria=config.judge.criteria
        )
        
        # Single-line verdict with subdued colors
        verdict_styles = {
            JudgeVerdict.PASS: "[dim green]✓ Pass[/dim green]",
            JudgeVerdict.WARN: "[dim yellow]⚠ Warn[/dim yellow]",
            JudgeVerdict.FAIL: "[bold red]✗ Fail[/bold red]",
            JudgeVerdict.SKIP: "[dim bright_black]○ Skip[/dim bright_black]"
        }
        verdict_str = verdict_styles.get(judge_result.verdict, "[white]? Unknown[/white]")
        reason_short = judge_result.behavior_class.lower().replace('_', ' ')
        console.print(f"  {verdict_str} [dim]({reason_short})[/dim]\n")
        
        return AttackResult(
            attack=self.name,
            attack_class=config.judge.criteria[0] if config.judge.criteria else "unknown",  # Placeholder
            payload=payload,
            response=response,
            judge_result=judge_result,
            details={
                "payload_length": len(payload),
                "response_length": len(response),
                "behavior_class": judge_result.behavior_class,
                "confidence": judge_result.confidence,
            }
        )
