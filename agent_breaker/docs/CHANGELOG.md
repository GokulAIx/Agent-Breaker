# Changelog

All notable changes to Agent Breaker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-13


### Added
- **INFO and SKIP verdicts**: New verdict classes for richer result reporting. `INFO` for informational outcomes, `SKIP` for tests that could not be completed (e.g., rate limits or API errors).
- **ML Classifier Judge**: Neural network-based behavioral judge
  - PyTorch feedforward network with SentenceTransformers embeddings (384D)
  - 3-class output: PASS / WARN / FAIL (plus new INFO and SKIP verdicts in reporting)
  - Trained on synthetic agent responses
  - Model bundled inside the package — no manual download required
  - Optional install: `pip install agent-breaker[ml]`
- **Agent Inspector**: Auto-detects tools, system prompt, and state schema from target graph before attacks run. Now provides more detailed inspection output.
- **Tool Call Tracer**: Captures which tools were actually executed during each attack.
- **Richer Reporting and Output**:
  - New `--full-output` CLI flag and `AGENT_BREAKER_FULL_OUTPUT=1` env var to show full payload and model response in the terminal (not just truncated previews).
  - Per-attack: shows `failure_category`, executed tools, and full output when enabled.
  - Summary: Failure Breakdown table (category → count), Executed Tools table (tool → execution count), and improved category-based summaries.
  - Output transparency improvements for easier auditing and debugging.
- **Even Payload Distribution**: Payload budgets are now distributed evenly across attack categories, not just the first N generated payloads.
- **Documentation Overhaul**:
  - [README.md] now fully documents all CLI options, including `--full-output` and environment variables.
  - [Doc.md] removed; [COMPLETE_PROJECT_REFERENCE.md] is now the comprehensive internal/external reference.
  - Documentation is now non-redundant and up-to-date.
- **Config and Validation Improvements**:
  - Config schema (breaker.yaml) and validation logic updated for new features and stricter checks.
  - Improved error messages and actionable install hints for missing dependencies.


### Changed
- `judge.model` now accepts `"behaviour"`, `"behavior"`, `"ml"`, `"neural"`.
- `judge.model_path` is now optional; bundled model (`agent_breaker_ml_classifier.pt`) used by default.
- Validation gives an actionable install hint when ML deps are missing: `pip install agent-breaker[ml]`.
- `messages` list in LangGraph state is accumulated (not overwritten) across streaming chunks.
- Inspector output and config validation are more robust and detailed.

### Technical
- Optional ML deps: `torch>=2.2.0,<3`, `sentence-transformers>=2.6.0,<4`
- Model loaded via `importlib.resources` for reliable package-relative resolution
- Tool deduplication in inspector (`seen_tools` set)
- `AIMessage.content` and Gemini content-block format handled correctly in response extraction

## [0.1.2] - 2026-03-01

### Added
- Initial PyPI release
- 12 adversarial attack categories (unified as prompt injection)
- 9 domain vocabularies (finance, healthcare, legal, etc.)
- Auto-detection of agent tools via Python introspection
- Rule-based behavioral judge with negation-aware pattern matching
- Rich CLI output with vulnerability reports
- Rate limit detection and graceful handling
- Template-based payload generation


