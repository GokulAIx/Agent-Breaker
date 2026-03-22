# Agent Breaker — Complete Project Reference

## Documentation Audit


Current documentation is now consolidated and up-to-date:

- [README.md](README.md): main public-facing doc, now fully covers all major terminal options including `--full-output`
- [ML_JUDGE_SETUP.md](ML_JUDGE_SETUP.md): useful and still relevant for ML judge setup
- [SPEC.md](SPEC.md): currently minimal and not sufficient as a product spec
- [CHANGELOG.md](CHANGELOG.md): useful for version history
- [ondoc.md](ondoc.md): idea notes, not formal product documentation

This file serves as the dedicated, complete architecture/reference file that covers the whole repository in one place.

---

## What Agent Breaker Is

Agent Breaker is a CLI tool for adversarial security testing of AI agents, currently focused on LangGraph-based agents.

It does five main things:

1. loads a target agent
2. inspects its structure and tools
3. generates adversarial prompts
4. runs those prompts against the agent
5. judges the agent response and prints a security report

Primary use case:
- test whether an agent refuses malicious or manipulative instructions
- detect unsafe tool execution, policy override, leakage, role acceptance, and similar failures

---

## Current CLI Commands

### `agent-breaker init`
Creates a starter [breaker.yaml](breaker.yaml) from the packaged template.

### `agent-breaker run`
Runs a configured security test session.

### `agent-breaker run --debug`
Runs with full traceback on errors.

### `agent-breaker run --full-output`
Runs with full payload and full model response shown in the terminal instead of truncated previews.

This is a recent feature and should be treated as a documented user-facing capability.

---

## Environment Variables

### `AGENT_BREAKER_DEBUG=1`
Enables full traceback behavior, same purpose as `--debug`.

### `AGENT_BREAKER_FULL_OUTPUT=1`
Enables full payload and response rendering in terminal output, same purpose as `--full-output`.

---

## Installation

### Basic install
```bash
pip install agent-breaker
```

### ML judge install
```bash
pip install agent-breaker[ml]
```

### Source install
```bash
git clone https://github.com/GokulAIx/Agent-Breaker
cd Agent-Breaker
pip install -e .
pip install -e .[ml]
```

---

## Typical User Workflow

1. install the package
2. run `agent-breaker init`
3. edit [breaker.yaml](breaker.yaml)
4. point `target.path` to the agent file
5. set `target.attr`, `target.input_key`, `target.output_key`, `target.state_class`, and `target.prompt_variable`
6. choose `generator.domain`
7. choose `judge.model`
8. run `agent-breaker run` or `agent-breaker run --full-output`

---

## Configuration Reference

Main config file: [breaker.yaml](breaker.yaml)

### Top-level fields

#### `version`
Config schema version.

#### `budget.max_tokens`
Reserved budget field for overall token budgeting.

#### `target`
Describes the agent under test.

Supported current type:
- `langgraph`

Important target fields:
- `type`: target framework
- `path`: Python file containing the compiled graph
- `attr`: exported compiled graph variable name
- `input_key`: field used to inject the adversarial payload
- `output_key`: field used to extract the final response
- `state_class`: state TypedDict name used by the graph
- `prompt_variable`: system prompt variable name in the agent file

#### `generator`
Controls payload generation.

Fields:
- `strategy`: currently only `template` is implemented
- `domain`: one of the supported domain vocabularies
- `seed`: deterministic generation seed

#### `attacks`
List of enabled attack modules.

Current supported attack:
- `prompt_injection`

Per-attack fields:
- `name`
- `enabled`
- `max_api_calls`

#### `judge`
Controls verdict logic.

Supported models:
- `behaviour`
- `behavior`
- `ml`
- `neural`

Fields:
- `model`
- `model_path`
- `criteria`

---

## Supported Domains

Defined in [agent_breaker/generator.py](agent_breaker/generator.py).

Current domain vocabularies:
- finance
- healthcare
- general
- legal
- devops
- customer_service
- hr
- ecommerce
- content_moderation

Each domain provides vocabulary for:
- authority roles
- forbidden actions
- sensitive assets
- threats

---

## Attack Categories

All currently come from the template generator in [agent_breaker/generator.py](agent_breaker/generator.py).

### Prompt-injection style categories
- `authority_override`
- `policy_override`
- `role_confusion`
- `emergency_framing`
- `confidentiality_pretext`
- `indirect_injection`

### Goal-hijacking style categories
- `direct_override`
- `priority_escalation`
- `mode_switch`
- `goal_replacement`
- `context_injection`
- `task_substitution`

Recent improvement:
- payload budgets are now distributed evenly across categories instead of just taking the first `N` generated payloads

---

## Verdict System

The system uses four verdicts:
- `PASS`
- `WARN`
- `FAIL`
- `SKIP`

### Behavior meanings
- `PASS`: the agent refused the malicious request
- `WARN`: the agent discussed or engaged without clearly complying
- `FAIL`: the agent complied, leaked, accepted role injection, or executed a tool unsafely
- `SKIP`: the test could not be completed, usually because of rate limit or API error

### ML label mapping
In the ML judge, the model label mapping is:
- `0 = PASS`
- `1 = WARN`
- `2 = FAIL`

---

## Terminal Output Behavior

By default, the terminal shows truncated previews for:
- payload
- response

With `--full-output` or `AGENT_BREAKER_FULL_OUTPUT=1`, the terminal shows:
- full payload text
- full response text

This exists so users can inspect the complete model output and decide whether they agree with the verdict.

The output also includes:
- agent structure report
- tool list
- system prompt preview
- per-payload verdict
- optional failure category
- optional executed tools
- results by category
- overall summary
- failure breakdown
- executed tools summary
- rate limit guidance

---

## Runtime Flow

Main orchestration lives in [agent_breaker/core.py](agent_breaker/core.py).

Execution flow:

1. CLI parses config in [agent_breaker/cli.py](agent_breaker/cli.py)
2. config is validated in [agent_breaker/validation.py](agent_breaker/validation.py)
3. [agent_breaker/core.py](agent_breaker/core.py) creates target, generator, and judge
4. [agent_breaker/inspector.py](agent_breaker/inspector.py) prints the agent structure report
5. [agent_breaker/generator.py](agent_breaker/generator.py) generates payloads
6. [agent_breaker/attacks/prompt_injection.py](agent_breaker/attacks/prompt_injection.py) sends each payload
7. target adapter runs the graph through [agent_breaker/adapters/langgraph.py](agent_breaker/adapters/langgraph.py)
8. tool execution is captured by [agent_breaker/tracer.py](agent_breaker/tracer.py)
9. response is judged in [agent_breaker/judge.py](agent_breaker/judge.py)
10. summary tables are printed from [agent_breaker/core.py](agent_breaker/core.py)

---

## Repository Map

### Root files

#### [breaker.yaml](breaker.yaml)
Active local configuration file for running the tool in this repository.

#### [example_breaker.yaml](example_breaker.yaml)
Older example config. Useful historically, but not aligned with the current validated schema in all fields.

#### [README.md](README.md)
Main public-facing project overview.


#### [SPEC.md](SPEC.md)
Minimal command list; currently too thin for project discovery.

#### [ML_JUDGE_SETUP.md](ML_JUDGE_SETUP.md)
Dedicated guide for ML judge installation and use.

#### [CHANGELOG.md](CHANGELOG.md)
Version history.

#### [ondoc.md](ondoc.md)
Design notes about prompt injection patterns and vocabulary design.

#### [pyproject.toml](pyproject.toml)
Package metadata, dependencies, optional extras, and entry point.

#### [example_agent.py](example_agent.py)
Simple example LangGraph financial agent used for testing and demos.

#### [working_langgraph_agent.py](working_langgraph_agent.py)
More realistic FinOps LangGraph example with tools and a production-style graph flow.

#### [COMPLETE_PROJECT_REFERENCE.md](COMPLETE_PROJECT_REFERENCE.md)
This file. Intended as the repository-wide architecture and feature reference.

### Root folders

#### [agent_breaker](agent_breaker)
Main package source code.

#### [examples](examples)
Contains example config material.

#### [agent_breaker.egg-info](agent_breaker.egg-info)
Packaging metadata generated during build/install.

#### `__pycache__`
Python cache artifacts. Not part of source design.

---

## Package Source Map

### [agent_breaker/__init__.py](agent_breaker/__init__.py)
Currently empty package initializer.

### [agent_breaker/main.py](agent_breaker/main.py)
Minimal executable entry point that runs the CLI app.

### [agent_breaker/cli.py](agent_breaker/cli.py)
Typer CLI definition.

Features:
- `init` command
- `run` command
- `--debug`
- `--full-output`
- sets environment toggles for runtime behavior
- loads YAML config
- calls validation
- invokes `AgentBreaker`

### [agent_breaker/config.py](agent_breaker/config.py)
Pydantic models for runtime configuration.

Defines:
- `BudgetConfig`
- `AttackConfig`
- `JudgeConfig`
- `SystemPromptConfig`
- `TargetConfig`
- `GeneratorConfig`
- `BreakerConfig`

### [agent_breaker/validation.py](agent_breaker/validation.py)
Pre-flight configuration validation.

Checks:
- required target fields
- target file existence
- known attack names
- enabled attacks
- budget values
- valid judge model names
- ML dependency availability
- packaged ML model availability
- valid generator strategy
- valid domain values

### [agent_breaker/core.py](agent_breaker/core.py)
Main orchestration engine.

Responsibilities:
- construct target, generator, and judge
- load LangGraph target
- choose rule-based or ML judge
- print configuration summary
- run attacks over generated candidates
- stop early on rate limit
- accumulate results
- print category and overall summary tables
- print failure and executed-tool breakdowns

### [agent_breaker/targets.py](agent_breaker/targets.py)
Abstract target interface plus `MockTarget`.

Defines the target contract:
- `send()`
- `get_context()`
- `get_system_prompt()`
- optional `call_tool()`

### [agent_breaker/generator.py](agent_breaker/generator.py)
Payload generation system.

Defines:
- `PayloadCandidate`
- abstract `PayloadGenerator`
- concrete `TemplateGenerator`

Features:
- deterministic template generation
- domain vocabularies
- capability-aware vocabulary overrides
- sensitive asset extraction from system prompt
- attack-category templates
- even interleaving across categories before budget truncation

### [agent_breaker/judge.py](agent_breaker/judge.py)
Judging system.

Contains:
- `JudgeVerdict`
- `JudgeResult`
- abstract `Judge`
- `BehaviorClassifier`
- `BehaviorJudge`
- `MLJudge`
- placeholder `LLMJudge`

BehaviorJudge features:
- regex-based refusal detection
- contrast-aware handling
- negation-aware action handling
- role acceptance detection
- data-shape leak detection
- discussion detection
- rate-limit and API-error handling

MLJudge features:
- bundled `.pt` model support
- `SentenceTransformer` embeddings
- PyTorch classifier
- rule override for certain false-positive `FAIL` cases
- tool execution override when actual tools run

### [agent_breaker/inspector.py](agent_breaker/inspector.py)
Pre-run agent inspection.

Displays:
- target type
- entry point
- node count
- tool count
- node descriptions
- tool descriptions
- system prompt preview

### [agent_breaker/tracer.py](agent_breaker/tracer.py)
Captures tool calls from streaming LangGraph execution.

Tracks:
- tool name
- arguments
- partial result
- whether the tool actually executed

### [agent_breaker/agent_breaker_ml_classifier.pt](agent_breaker/agent_breaker_ml_classifier.pt)
Bundled ML classifier model used by `MLJudge` when no custom `model_path` is given.

### [agent_breaker/templates](agent_breaker/templates)
Packaged starter templates.

#### [agent_breaker/templates/breaker.yaml](agent_breaker/templates/breaker.yaml)
Default config template used by `agent-breaker init`.

### [agent_breaker/attacks](agent_breaker/attacks)
Attack implementations.

#### [agent_breaker/attacks/prompt_injection.py](agent_breaker/attacks/prompt_injection.py)
Current attack executor.

Features:
- renders payload and response
- supports truncated or full terminal output
- passes tool trace into the judge
- prints verdict line
- prints failure category when present
- prints executed tool names when present
- returns structured `AttackResult`

### [agent_breaker/adapters](agent_breaker/adapters)
Framework-specific target adapters.

#### [agent_breaker/adapters/__init__.py](agent_breaker/adapters/__init__.py)
Exports `LangGraphTarget`.

#### [agent_breaker/adapters/langgraph.py](agent_breaker/adapters/langgraph.py)
Current production adapter for LangGraph.

Features:
- dynamic module import
- graph attribute lookup
- system prompt extraction
- initial state schema discovery
- safe state initialization
- stateless invocation with unique `thread_id`
- streaming graph execution
- response extraction from multiple content formats
- capability extraction from graph/module
- tool discovery and deduplication
- rate-limit normalization into standard skip responses
- exposes `last_tool_trace` for judging

---

## Example and Demo Files

### [example_agent.py](example_agent.py)
Simple finance example agent with tool declarations. Good for demonstrations and local experimentation.

### [working_langgraph_agent.py](working_langgraph_agent.py)
Richer FinOps example with:
- `ingest` node
- `agent` node
- `tools` node
- `finalize` node
- realistic policy-oriented system prompt
- tool binding to Gemini via LangChain
- graph compiled and exported as `graph`

### [examples/breaker.yaml](examples/breaker.yaml)
Example configuration showing how to point Agent Breaker at the sample agent.

---

## Packaging and Distribution

Packaging is defined in [pyproject.toml](pyproject.toml).

Current important details:
- package name: `agent-breaker`
- Python requirement: `>=3.12`
- script entry point: `agent-breaker = agent_breaker.main:app`
- optional extra: `ml`
- packaged data includes templates and model file

Core runtime dependencies include:
- `typer`
- `rich`
- `pydantic`
- `pydantic-settings`
- `pyyaml`
- `httpx`
- `langgraph`
- `python-dotenv`

Optional ML dependencies include:
- `torch`
- `sentence-transformers`

---

## What Is Already Good

The project already has several strong pieces:
- practical README
- dedicated ML setup guide
- changelog
- working examples
- rich terminal UX
- inspection output
- category-based summaries
- tool tracing
- full-output mode for transparency

---


## Documentation Gaps To Fix Later

Recommended follow-up documentation updates:

1. expand [SPEC.md](SPEC.md) into a real product/CLI spec
2. add PyPI publishing instructions after release workflow is finalized
3. add CI/CD usage examples
4. add screenshots or terminal captures for default vs `--full-output`
5. document current limits clearly, especially single-turn testing and LangGraph focus

---

## Recommended Public Positioning

If users search for Agent Breaker, the documentation should clearly communicate:
- what it is
- who it is for
- how to install it
- how to configure a target
- how to run it
- what the verdicts mean
- how to inspect complete model output
- how ML judging works
- how tool execution is detected
- what files they need to export from their agent

This file is intended to be the complete internal and external reference until the README and other docs are aligned.
