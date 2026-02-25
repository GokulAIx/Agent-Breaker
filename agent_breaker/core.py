from agent_breaker.config import BreakerConfig
from agent_breaker.attacks.prompt_injection import PromptInjectionAttack
from agent_breaker.targets import MockTarget, AgentTarget
from agent_breaker.generator import TemplateGenerator, PayloadGenerator
from agent_breaker.judge import BehaviorJudge, Judge, JudgeVerdict
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

console = Console()


ATTACK_REGISTRY = {
    "prompt_injection": PromptInjectionAttack,
}


class AgentBreaker:
    def __init__(self, config: BreakerConfig):
        self.config = config
        self.results = []
    
    def _create_target(self) -> AgentTarget:
        """Create target from config."""
        if not self.config.target:
            raise ValueError(
                "No target specified in breaker.yaml. "
                "Add a 'target:' section with type, path, and other required fields."
            )
        
        target_type = self.config.target.type.lower()
        system_prompt = self._get_system_prompt()
        
        if target_type == "langgraph":
            from agent_breaker.adapters.langgraph import LangGraphTarget
            
            if not self.config.target.path or not self.config.target.attr:
                raise ValueError("LangGraph target requires 'path' and 'attr' fields")
            
            return LangGraphTarget(
                graph_path=self.config.target.path,
                graph_attr=self.config.target.attr,
                prompt_variable=self.config.target.prompt_variable,
                input_key=self.config.target.input_key or "user_query",
                output_key=self.config.target.output_key,
                state_class=self.config.target.state_class,
                system_prompt=self.config.target.system_prompt
            )
        
        elif target_type == "mock":
            return MockTarget(system_prompt=system_prompt)
        
        else:
            raise ValueError(f"Unsupported target type: {target_type}")
    
    def _create_generator(self) -> PayloadGenerator:
        """Create payload generator from config."""
        gen_config = self.config.generator
        
        if not gen_config or gen_config.strategy == "template":
            return TemplateGenerator(
                domain=gen_config.domain if gen_config else "general",
                seed=gen_config.seed if gen_config else None
            )
        
        
        raise NotImplementedError(f"Generator strategy '{gen_config.strategy}' not yet implemented")
    
    def _create_judge(self) -> Judge:
        """Create judge from config."""
        # V1: Always use BehaviorJudge (rule-based)
        # Future: Support optional LLM judge if user provides API key
        return BehaviorJudge()
    
    def _get_system_prompt(self, target: Optional[AgentTarget] = None) -> str:
        """Extract system prompt from config or target."""
        # Priority 1: Get from target if available
        if target:
            prompt = target.get_system_prompt()
            if prompt and prompt != "System prompt not extractable from graph":
                return prompt
        
        # Priority 2: Get from config
        if self.config.target and self.config.target.system_prompt:
            sp_config = self.config.target.system_prompt
            if sp_config.source == "inline" and sp_config.value:
                return sp_config.value
        
        # Fallback
        return "You are a helpful assistant."

    def run(self):
        # Clean header
        console.print("\n[bold]Agent Breaker[/bold] [dim]— Security Testing for AI Agents[/dim]\n")
        
        # Create target, generator, and judge
        target = self._create_target()
        generator = self._create_generator()
        judge = self._create_judge()
        system_prompt = self._get_system_prompt(target)
        
        # Configuration summary - simple, no box
        console.print("[dim]Configuration:[/dim]")
        console.print(f"  Target: {target.__class__.__name__}")
        console.print(f"  Generator: {generator.__class__.__name__}")
        console.print(f"  Judge: {judge.__class__.__name__}")
        
        # Show API budget
        enabled_attacks = [a for a in self.config.attacks if a.enabled]
        if enabled_attacks:
            budget_info = ", ".join([f"{a.name}={a.max_api_calls}" for a in enabled_attacks])
            console.print(f"  Budget: {budget_info}")
        
        console.print()

        # Track if we hit a rate limit (to stop all subsequent attacks)
        rate_limit_hit = False

        for attack_cfg in self.config.attacks:
            if not attack_cfg.enabled:
                continue
            
            # Skip remaining attacks if we already hit a rate limit
            if rate_limit_hit:
                console.print(f"[dim]⏭️  Skipping attack '{attack_cfg.name}' (rate limit already hit)[/dim]")
                continue

            attack_cls = ATTACK_REGISTRY.get(attack_cfg.name)
            if not attack_cls:
                console.print(f"[yellow]⚠️  Unknown attack: {attack_cfg.name}[/yellow]")
                continue

            # Simple attack header
            console.print(f"\n[bold]━━ {attack_cfg.name.replace('_', ' ').title()} ━━[/bold]\n")
            
            # Generate payloads (respecting per-attack API budget)
            target_context = target.get_context()
            candidates = generator.generate(
                attack_name=attack_cfg.name,
                target_context=target_context,
                system_prompt=system_prompt,
                config=self.config,
                max_candidates=attack_cfg.max_api_calls
            )
            
            console.print(f"[dim]Testing {len(candidates)} payloads...[/dim]\n")
            
            # Execute attack with each payload using progress bar
            attack = attack_cls()
            
            # Test execution with timing
            console.print()
            import time
            total_start = time.time()
            
            for i, candidate in enumerate(candidates, 1):
                console.print(f"[bold]{i}/{len(candidates)}[/bold] [dim]{candidate.attack_class.replace('_', ' ').title()}[/dim]")
                result = attack.execute(target, candidate.payload, self.config, judge)
                result.attack_class = candidate.attack_class
                self.results.append(result)
                
                # Check for rate limit - stop immediately
                if result.judge_result and result.judge_result.verdict == JudgeVerdict.SKIP:
                    if result.judge_result.behavior_class == "RATE_LIMIT":
                        rate_limit_hit = True
                        skipped_count = len(candidates) - i
                        if skipped_count > 0:
                            console.print(f"[dim yellow]⚠ Rate limit — skipped {skipped_count} remaining[/dim yellow]\n")
                        break
            
            total_elapsed = time.time() - total_start
            console.print(f"[dim]Completed in {total_elapsed:.1f}s[/dim]")

        console.print("\n[bold]━━━━━ Results ━━━━━[/bold]\n")
        self._print_summary()
    
    def _print_summary(self):
        """Print detailed test summary with breakdown by attack category."""
        total = len(self.results)
        failed = sum(1 for r in self.results if r.judge_result and r.judge_result.verdict == JudgeVerdict.FAIL)
        warned = sum(1 for r in self.results if r.judge_result and r.judge_result.verdict == JudgeVerdict.WARN)
        skipped = sum(1 for r in self.results if r.judge_result and r.judge_result.verdict == JudgeVerdict.SKIP)
        passed = total - failed - warned - skipped
        
        # Group results by attack class
        from collections import defaultdict
        by_class = defaultdict(lambda: {"pass": 0, "warn": 0, "fail": 0, "skip": 0})
        
        for result in self.results:
            if result.judge_result:
                attack_class = result.attack_class
                verdict = result.judge_result.verdict
                if verdict == JudgeVerdict.PASS:
                    by_class[attack_class]["pass"] += 1
                elif verdict == JudgeVerdict.WARN:
                    by_class[attack_class]["warn"] += 1
                elif verdict == JudgeVerdict.FAIL:
                    by_class[attack_class]["fail"] += 1
                elif verdict == JudgeVerdict.SKIP:
                    by_class[attack_class]["skip"] += 1
        
        # Better formatted tables with proper spacing
        details_table = Table(
            box=box.SIMPLE_HEAD,
            show_header=True,
            header_style="bold white",
            expand=True,
            padding=(0, 2)
        )
        details_table.add_column("Category", style="white", no_wrap=True)
        details_table.add_column("Pass", justify="center", style="dim green")
        details_table.add_column("Warn", justify="center", style="dim yellow")
        details_table.add_column("Fail", justify="center", style="dim red")
        details_table.add_column("Skip", justify="center", style="dim bright_black")
        details_table.add_column("Status", justify="center", no_wrap=True)
        
        # Sort by attack class name for consistent display
        for attack_class in sorted(by_class.keys()):
            counts = by_class[attack_class]
            # Format attack class name nicely
            display_name = attack_class.replace("_", " ").title()
            
            # Determine overall result for this category
            total_in_category = counts["pass"] + counts["warn"] + counts["fail"] + counts["skip"]
            
            if counts["fail"] > 0:
                result_text = "[bold red]Vulnerable[/bold red]"
            elif counts["warn"] > 0:
                result_text = "[dim yellow]Review[/dim yellow]"
            elif counts["skip"] == total_in_category:
                result_text = "[dim]Not Tested[/dim]"
            elif counts["pass"] > 0:
                result_text = "[dim green]Secure[/dim green]"
            else:
                result_text = "[dim]—[/dim]"
            
            details_table.add_row(
                display_name,
                str(counts["pass"]),
                str(counts["warn"]),
                str(counts["fail"]),
                str(counts["skip"]),
                result_text
            )
        
        console.print()
        console.print("[bold]Results by Category[/bold]")
        console.print(details_table)
        
        console.print()
        console.print("[bold]Overall Summary[/bold]")
        summary_table = Table(
            box=box.SIMPLE_HEAD,
            show_header=True,
            header_style="bold white",
            expand=True,
            padding=(0, 2)
        )
        summary_table.add_column("Metric", style="white", no_wrap=True)
        summary_table.add_column("Count", justify="right", style="white")
        summary_table.add_column("Percentage", justify="right", style="dim")
        
        summary_table.add_row(
            "Total",
            str(total),
            "100%"
        )
        if passed > 0:
            summary_table.add_row(
                "Passed",
                f"[dim green]{passed}[/dim green]",
                f"[dim green]{(passed/total*100):.0f}%[/dim green]"
            )
        if warned > 0:
            summary_table.add_row(
                "Warned",
                f"[dim yellow]{warned}[/dim yellow]",
                f"[dim yellow]{(warned/total*100):.0f}%[/dim yellow]"
            )
        if failed > 0:
            summary_table.add_row(
                "Failed",
                f"[bold red]{failed}[/bold red]",
                f"[bold red]{(failed/total*100):.0f}%[/bold red]"
            )
        if skipped > 0:
            summary_table.add_row(
                "Skipped",
                f"[dim]{skipped}[/dim]",
                f"[dim]{(skipped/total*100):.0f}%[/dim]"
            )
        
        console.print()
        console.print(summary_table)
        
        # Simple rate limit/error notification
        if skipped > 0:
            rate_limited = sum(1 for r in self.results if r.judge_result and r.judge_result.behavior_class == "RATE_LIMIT")
            api_errors = sum(1 for r in self.results if r.judge_result and r.judge_result.behavior_class == "API_ERROR")
            
            console.print()
            if rate_limited > 0:
                console.print(f"[dim yellow]⚠ Rate Limit:[/dim yellow] {rate_limited} test(s) skipped due to API quota")
                console.print(f"[dim]  → Wait a few minutes, reduce max_api_calls ({self.config.attacks[0].max_api_calls}), or upgrade plan[/dim]")
            elif api_errors > 0:
                console.print(f"[dim yellow]⚠ API Error:[/dim yellow] {api_errors} test(s) failed due to API errors")
                console.print(f"[dim]  → Check API key, network connectivity, or service status[/dim]")
        
        # Simple final assessment
        console.print()
        
        if skipped == total:
            console.print("[bold red]✗ No Tests Completed[/bold red] [dim]— all skipped due to errors[/dim]")
        elif failed > 0:
            console.print(f"[bold red]✗ Vulnerable[/bold red] [dim]— {failed} test(s) failed[/dim]")
        elif warned > 0:
            console.print(f"[dim yellow]⚠ Review Needed[/dim yellow] [dim]— {warned} ambiguous response(s)[/dim]")
        elif passed > 0 and skipped > 0:
            console.print(f"[dim green]✓ Partial Pass[/dim green] [dim]— {passed} passed, {skipped} skipped[/dim]")
        elif passed > 0:
            console.print(f"[bold green]✓ All Passed[/bold green] [dim]— agent defended against {passed} attack(s)[/dim]")
        else:
            console.print("[dim]No results[/dim]")
        
        console.print()
