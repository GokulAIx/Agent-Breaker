"""
Agent structure inspector for Agent Breaker.
Analyzes agent capabilities before testing.
"""
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


class Inspector:
    """Analyzes and reports agent structure before security testing."""
    
    def __init__(self, target):
        """
        Initialize inspector with a target agent.
        
        Args:
            target: AgentTarget instance (already loaded and analyzed)
        """
        self.target = target
    
    def inspect(self) -> Dict[str, Any]:
        """
        Extract agent structure information.
        
        Returns:
            Dict with keys:
            - nodes: list of node names
            - tools: list of {name, description}
            - has_tools: bool
            - entry_point: str (first non-system node)
            - system_prompt_preview: first 150 chars of system prompt
        """
        context = self.target.get_context()
        
        capabilities = context.get("capabilities", {})
        nodes = capabilities.get("nodes", [])
        tools = capabilities.get("tools", [])
        has_tools = capabilities.get("has_tools", False)
        system_prompt = context.get("system_prompt", "")
        
        # Get entry point (first node if available)
        entry_point = nodes[0] if nodes else "unknown"
        
        # Get system prompt preview (first 150 chars)
        preview = system_prompt[:150] if system_prompt else "No system prompt found"
        if len(system_prompt) > 150:
            preview += "..."
        
        return {
            "nodes": nodes,
            "tools": tools,
            "has_tools": has_tools,
            "entry_point": entry_point,
            "system_prompt_preview": preview,
            "target_type": context.get("type", "unknown"),
        }
    
    def print_report(self) -> None:
        """Print formatted agent structure report to console."""
        data = self.inspect()
        
        # Header
        console.print("\n[bold cyan]━━ Agent Structure Report ━━[/bold cyan]\n")
        
        # Basic info
        info_table = Table(show_header=False, box=box.ROUNDED)
        info_table.add_row("[dim]Type:[/dim]", f"[cyan]{data['target_type']}[/cyan]")
        info_table.add_row("[dim]Entry Point:[/dim]", f"[cyan]{data['entry_point']}[/cyan]")
        info_table.add_row("[dim]Node Count:[/dim]", f"[cyan]{len(data['nodes'])}[/cyan]")
        info_table.add_row("[dim]Tool Count:[/dim]", f"[cyan]{len(data['tools'])}[/cyan]")
        console.print(info_table)

        # Nodes table
        console.print("\n[bold]Nodes[/bold]")
        nodes_table = Table(box=box.ROUNDED, show_lines=True)
        nodes_table.add_column("Node", style="cyan", no_wrap=True)
        nodes_table.add_column("What It Does", style="dim")
        for node in data["nodes"]:
            nodes_table.add_row(node, self._describe_node(node))
        if data["nodes"]:
            console.print(nodes_table)
        else:
            console.print("[dim]No nodes detected[/dim]")

        # Tools table
        console.print("\n[bold]Tools[/bold]")
        if data["has_tools"] and data["tools"]:
            tools_table = Table(box=box.ROUNDED, show_lines=True)
            tools_table.add_column("Tool", style="yellow", no_wrap=True)
            tools_table.add_column("What It Does", style="dim")
            for tool in data["tools"]:
                name = tool.get("name", "unknown")
                desc = tool.get("description", "No description")
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                tools_table.add_row(str(name), str(desc))
            console.print(tools_table)
            console.print(f"\n[bold cyan]⚠ {len(data['tools'])} tool(s) detected[/bold cyan] — attacks will target these")
        else:
            console.print("[dim]No tools detected[/dim]")

        # System prompt preview
        console.print("\n[bold]System Prompt (preview)[/bold]")
        console.print(
            Panel(
                f"[dim]\"{data['system_prompt_preview']}\"[/dim]",
                box=box.ROUNDED,
                border_style="dim",
            )
        )
        
        console.print()

    def _describe_node(self, node_name: str) -> str:
        """Best-effort description for common LangGraph node naming patterns."""
        name = node_name.lower()
        if "ingest" in name or "input" in name:
            return "Accepts user input and normalizes initial graph state."
        if "agent" in name or "llm" in name or "model" in name:
            return "Runs LLM reasoning and decides the next action."
        if "tool" in name:
            return "Executes selected tools and returns tool outputs to the graph."
        if "final" in name or "respond" in name or "output" in name:
            return "Builds final response fields returned to the caller."
        return "Workflow node in the agent graph."
