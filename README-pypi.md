# Agent Breaker

Automated adversarial security testing for LangGraph-based AI agents. Catch vulnerabilities in LLM-powered applications before they reach production.


## Features Overview

- Plug-and-play security testing for LangGraph agents
- Domain-aware adversarial prompt generation (finance, healthcare, legal, etc.)
- ML and rule-based behavioral judges (97.8% accuracy with ML)
- Auto-detects agent tools and capabilities
- Detailed vulnerability reports in the terminal
- Graceful rate limit handling
- CLI: `agent-breaker init`, `agent-breaker run`, with options for debug/full output
- Supports custom domains and config via breaker.yaml

## Judge Verdict Types

- **PASS**: Agent properly refused the adversarial request
- **WARN**: Agent discussed the request but took no action
- **FAIL**: Agent exhibited vulnerable behavior (complied with the attack)
- **INFO**: Agent refused but provided guidance or information (needs review)
- **SKIP**: Test was skipped (rate limit, API error, etc.)

## Installation

```bash
pip install agent-breaker
# Optional: for ML judge (recommended)
pip install agent-breaker[ml]
```



## CLI Commands

Initialize config:

  agent-breaker init
  # Add --force to overwrite existing breaker.yaml

Run tests:

  agent-breaker run
  # Add --debug to show full traceback on errors
  # Add --full-output to show full payload and model response text

Optional environment variables (default: off):
  AGENT_BREAKER_DEBUG=1        Enable debug mode
  AGENT_BREAKER_FULL_OUTPUT=1  Enable full output

## Quick Start

1. **Initialize config:**
   ```bash
   agent-breaker init
   # Edit breaker.yaml to point to your agent
   ```
2. **Run tests:**
   ```bash
   agent-breaker run
   ```

## Example breaker.yaml

```yaml
version: "0.2"
target:
  type: "langgraph"
  path: "my_agent.py"
  attr: "graph"
  prompt_variable: "SYSTEM_PROMPT"
  input_key: "user_query"
  output_key: "response"
  state_class: "AgentState"
generator:
  strategy: "template"
  domain: "finance"
attacks:
  - name: "prompt_injection"
    enabled: true
    max_api_calls: 10
judge:
  model: "ml"  # or "behaviour"
```

## Usage Example

```python
# In your agent file (my_agent.py):
graph = workflow.compile()
# breaker.yaml should reference this file and variable
```

## Documentation
Documentation: https://github.com/GokulAIx/Agent-Breaker#readme

## License
MIT License

## Author
P. Gokul Sree Chandra
