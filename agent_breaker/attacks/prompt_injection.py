from agent_breaker.targets import AgentTarget
from agent_breaker.config import BreakerConfig
from agent_breaker.judge import Judge, JudgeResult, JudgeVerdict
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
from rich.console import Console
from rich.panel import Panel

console = Console()


def _full_output_enabled() -> bool:
    """Return whether full payload/response output should be shown."""
    return os.environ.get("AGENT_BREAKER_FULL_OUTPUT", "").strip().lower() in {"1", "true", "yes", "on"}


def _render_text(label: str, text: str) -> None:
    """Render either truncated or full text for terminal output."""
    if _full_output_enabled():
        console.print(Panel(text or "", title=label, border_style="dim", expand=False))
        return

    preview = text if len(text) <= 100 else text[:97] + "..."
    console.print(f"  [dim]{label}:[/dim] {preview}")


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
        _render_text("Payload", payload)

        response = target.send(payload)

        _render_text("Response", response)

        # Use judge to evaluate response
        judge_result = judge.evaluate(
            payload=payload,
            response=response,
            attack_name=self.name,
            criteria=config.judge.criteria,
            tool_trace=getattr(target, "last_tool_trace", None)
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
        console.print(f"  {verdict_str} [dim]({reason_short})[/dim]")

        if judge_result.failure_category:
            console.print(f"  [dim red]Category:[/dim red] [dim]{judge_result.failure_category.replace('_', ' ')}[/dim]")

        if judge_result.tool_calls:
            console.print(f"  [dim yellow]Tools:[/dim yellow] [dim]{', '.join(judge_result.tool_calls)}[/dim]")

        console.print()
        
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
                "failure_category": judge_result.failure_category,
                "tool_calls": judge_result.tool_calls,
            }
        )
