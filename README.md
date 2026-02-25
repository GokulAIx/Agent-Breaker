# Agent Breaker 🔨

> Chaos Monkey for AI Agents - Automated adversarial testing for LangGraph applications

[![Status](https://img.shields.io/badge/status-v0.1_WIP-yellow)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## 🚧 Status: Work in Progress

Agent Breaker is under active development. Currently building v0.1 with core features for LangGraph agent testing.

**Recent Updates:**
- ✅ Mandatory prompt variable configuration
- ✅ Pre-flight config validation with helpful errors
- ✅ Dynamic module loading for any LangGraph agent
- ✅ Capability auto-detection (tools, nodes)
- 🚧 Adversarial Instruction Attacks (prompt injection + goal hijacking)
- 🚧 End-to-end testing
- ⏳ PyPI packaging (after attack implementation complete)

---

## What is Agent Breaker?

Agent Breaker automatically tests AI agents for security vulnerabilities using adversarial prompts. Think of it as chaos engineering for LLM applications.

**Features:**
- 🔌 Plug-and-play testing for LangGraph agents
- 🎯 Domain-aware payload generation (finance, healthcare, legal, etc.)
- 🤖 Auto-detects agent capabilities and tailors attacks
- ⚖️ Behavioral judge (mechanism-agnostic, outcome-focused)
- 📊 Detailed vulnerability reports

**Attack Philosophy:**
Agent Breaker focuses on **behavioral outcomes**, not attack taxonomy.
- **Mechanism**: Adversarial Instruction Attacks (prompt injection, context manipulation)
- **Outcomes**: Goal hijacking, role acceptance, data leakage, unauthorized actions
- **Evaluation**: What the agent *does*, not what the payload *says*

**Why unified attacks?** Goal hijacking isn't a separate primitive—it's a behavioral outcome of adversarial instructions. This design aligns with the BehaviorJudge's outcome-focused approach.

---

## Quick Start (Coming Soon)

```bash
# Install (when on PyPI)
pip install agent-breaker

# Initialize config
agent-breaker init

# Edit breaker.yaml with your agent details
# Run tests
agent-breaker run
```

---

## Configuration

Create a `breaker.yaml` file:

```yaml
version: "1.0"

budget:
  max_tokens: 5000

target:
  type: "langgraph"
  path: "my_agent.py"                    # Path to your agent
  attr: "graph"                          # Compiled graph variable name
  prompt_variable: "SYSTEM_PROMPT"       # Your prompt variable name
  input_key: "user_query"                # State input field
  output_key: "response"                 # State output field
  state_class: "AgentState"              # Your state TypedDict class

generator:
  strategy: "template"
  domain: "finance"                      # Your agent's domain
  seed: 42

attacks:
  - name: "prompt_injection"             # Unified adversarial instruction attacks
    enabled: true
    max_api_calls: 10                    # Includes: direct injection, goal hijacking, role manipulation

judge:
  model: "behavior"                      # Rule-based (free)
  criteria:
    - refusal_detection
    - data_leakage
```

---

## How It Works

1. **Load:** Dynamically imports your LangGraph agent
2. **Detect:** Extracts capabilities (tools, nodes, system prompt)
3. **Generate:** Creates domain-specific adversarial payloads
4. **Test:** Sends payloads to your agent
5. **Judge:** Analyzes responses for vulnerabilities (negation-aware keyword matching in v0.1, ML classifier in v0.2)
6. **Report:** Shows what broke and why

---

## Architecture

```
agent_breaker/
├── adapters/        # Target adapters (LangGraph, CrewAI)
├── attacks/         # Attack implementations
├── generator.py     # Payload generation
├── judge.py         # Behavioral analysis
├── validation.py    # Config validation
└── core.py          # Main orchestration
```

---

## Why Agent Breaker?

**Problem:** AI agents can be manipulated through carefully crafted prompts, leaking sensitive data or bypassing safety rules.

**Solution:** Automated testing that finds vulnerabilities before production.

**Benefits:**
- 🔒 Catch security issues early
- 💰 No manual QA time
- 📈 Continuous testing in CI/CD
- 🎓 Learn how agents fail

### The False Positive Challenge

Early testing revealed a critical issue: **keyword-based judges produce 30% false positives**.

**Example:**
- Agent says: "I am NOT CAPABLE of executing trades"
- Keyword judge sees: "executing" → ❌ FAIL (false positive)
- ML classifier understands: "NOT CAPABLE" → ✅ PASS (correct)

**Why v0.2 needs ML:**
Keyword matching is blind to negation and context. A trained classifier understands semantic meaning, reducing false positives from 30% to <5%.

---

## Roadmap

**v0.1 (Current Focus):**
- [x] LangGraph adapter with dynamic loading 
- [x] Config validation system
- [x] Negation-aware keyword judge (stopgap)
- [ ] Adversarial Instruction Attacks implementation
  - Direct prompt injection
  - Goal hijacking (task abandonment)
  - Role manipulation patterns
  - Context confusion techniques
- [ ] Template-based payload generation
- [ ] Basic reporting

**v0.2 (Next Major Release):**
- [ ] **ML Classifier Judge** (primary focus - solves false positive problem)
  - PyTorch FFN with SentenceTransformers embeddings (384D)
  - 3-class output: REFUSAL / DISCUSSION / COMPLIANCE
  - Trained on 100+ labeled agent responses
  - ~50MB model, understands semantic negation
- [ ] Data collection system for training samples
- [ ] Budget constraints (max_tokens, max_cost enforcement)
- [ ] CrewAI adapter
- [ ] Multi-turn conversation attacks
- [ ] LLM-powered payload generation (optional user toggle)
- [ ] Budget Tracking (Token Cost Estimation, etc)

**v1.0 (Vision):**
- [ ] Support for all major frameworks (LangGraph, CrewAI, AutoGen, etc.)
- [ ] Custom attack pattern definitions
- [ ] Jailbreak detection
- [ ] CI/CD integrations

---

## Contributing

This is a solo project currently in active development. Contributions, ideas, and feedback are welcome once v0.1 is complete!

**Want to help?**
- ⭐ Star the repo
- 🐛 Report bugs
- 💡 Suggest features
- 📖 Improve documentation

---

## Technical Details

**Built With:**
- Python 3.10+
- Pydantic (config validation)
- Typer (CLI)

**Key Concepts:**
- Dynamic module loading (`importlib`)
- Runtime introspection (`getattr`, `hasattr`)
- State management (TypedDict detection)
- Provider-agnostic rate limiting

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

## Author

Built by P. Gokul Sree Chandra

**Connect:**
- LinkedIn: [https://www.linkedin.com/in/gokulsreechandra/]
- Twitter: [https://x.com/gokulaix]
- Blog: [https://medium.com/@gokulaix]

---

## Acknowledgments

Inspired by:
- Chaos Monkey (Netflix)
- OWASP LLM Top 10

---

**⚠️ Disclaimer:** Agent Breaker is a security testing tool. Only test agents you own or have permission to test. Use responsibly.
