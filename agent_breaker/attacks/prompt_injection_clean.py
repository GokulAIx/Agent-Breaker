from agent_breaker.targets import AgentTarget
from agent_breaker.config import BreakerConfig
from agent_breaker.judge import Judge, JudgeResult, JudgeVerdict
from typing import Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console

console = Console()


@dataclass
class AttackResult:
    """Result of an attack execution."""
    attack: str
    attack_class: str
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
    """Prompt injection attack with clean, minimal UI."""
    name = "prompt_injection"

    def execute(
        self,
        target: AgentTarget,
        payload: str,
        config: BreakerConfig,
        judge: Judge
    ) -> AttackResult:
        """Execute attack with clean display."""
        
        # Payload - simple inline display
        payload_preview = payload if len(payload) <= 120 else payload[:117] + "..."
        console.print(f"  [dim]Payload:[/dim] {payload_preview}")

        response = target.send(payload)

        # Response - simple inline display  
        response_preview = response if len(response) <= 120 else response[:117] + "..."
        console.print(f"  [dim]Response:[/dim] {response_preview}")

        # Judge evaluation
        judge_result = judge.evaluate(
            payload=payload,
            response=response,
            attack_name=self.name,
            criteria=config.judge.criteria
        )
        
        # Verdict - single clean line
        verdict_display = {
            JudgeVerdict.PASS: "[green]✓ PASS[/green]",
            JudgeVerdict.WARN: "[yellow]⚠ WARN[/yellow]",  
            JudgeVerdict.FAIL: "[red]✗ FAIL[/red]",
            JudgeVerdict.SKIP: "[bright_black]○ SKIP[/bright_black]"
        }
        verdict_str = verdict_display.get(judge_result.verdict, "[white]? UNKNOWN[/white]")
        console.print(f"  {verdict_str} [dim]{judge_result.behavior_class.lower().replace('_', ' ')}[/dim]\n")
        
        return AttackResult(
            attack=self.name,
            attack_class=config.judge.criteria[0] if config.judge.criteria else "unknown",
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
