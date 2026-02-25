from pathlib import Path
import typer
import importlib.resources as resources
import yaml
from agent_breaker.validation import validate_config
from agent_breaker.config import BreakerConfig
from agent_breaker.core import AgentBreaker

app = typer.Typer(help="Agent Breaker - Chaos Monkey for AI agents")


@app.command()
def init(force: bool = False):
    """Initialize a breaker.yaml config file"""
    target = Path("breaker.yaml")

    if target.exists() and not force:
        typer.echo("breaker.yaml already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    with resources.files("agent_breaker.templates").joinpath("breaker.yaml").open("r") as f:
        content = f.read()

    target.write_text(content)
    typer.echo("breaker.yaml created")


@app.command()
def run(config: Path = Path("breaker.yaml")):
    """Run Agent Breaker"""
    if not config.exists():
        typer.echo("❌ Config file not found.")
        raise typer.Exit(1)
    
    data = yaml.safe_load(config.read_text())
    cfg = BreakerConfig(**data)

    errors=validate_config(cfg)
    if errors:
        typer.echo("Errors in the configuration file: Breaker.yaml")
        for i,error in enumerate(errors):
            typer.echo(f"{i+1}: {error}")
        raise typer.Exit(1)

    breaker = AgentBreaker(cfg)
    breaker.run()
