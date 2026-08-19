# Sovrune

**The open-source operating system for AI-run companies.**

Sovrune turns sourced business evidence into strategy, coordinated work, human-approved delivery, and measured outcomes. It is self-hosted, model-neutral, and designed to answer a harder question than “are the agents busy?”: **did the company improve?**

> **Alpha:** the current release proves the operating contract with a fictional company. It does not autonomously deploy, spend money, or write to production systems.

## Run it

```bash
git clone https://github.com/Sovrune/sovrune
cd sovrune
docker compose up --build
```

Open <http://localhost:8787>.

Public website: [sovrune.com](https://sovrune.com)

Browser-safe demo: [sovrune.com/demo.html](https://sovrune.com/demo.html). It uses fictional aggregate data, stores no credentials, and generates provider configuration locally in the browser.

Without Docker:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
sovrune serve
```

## What ships in `v0.1.0-alpha`

- Provenance-aware `BusinessState`
- Company Adapter contract and fictional Acme adapter
- Evidence → strategy → opportunity → product → engineering → approval → outcome loop
- Human approval boundary
- OpenAI-compatible, Anthropic, Gemini, and Ollama provider adapters
- Animated command center
- Zero runtime dependencies beyond Python 3.11+
- Docker deployment and CI

## Bring your models

Copy `.env.example` to `.env`. Choose a hosted provider, an OpenAI-compatible endpoint, or Ollama. Provider credentials are read from the process environment and are never returned by the API or written to reports.

## Build a company adapter

Implement `CompanyAdapter.build_state()` and return aggregate metrics with source, date, and confidence. Sovrune rejects PII-shaped keys at the operating boundary. The adapter belongs beside the company systems; the operating layer consumes normalized state.

## Architecture

```text
Company systems → Company Adapter → BusinessState
                                      ↓
              Observe → Decide → Execute → Approve → Measure
                                      ↓
                      Provider-neutral model router
```

## Commercial support

The Community Edition is free. Founding design partners receive a managed deployment, one company adapter, two integrations, model configuration, and direct founder support. Contact [hello@sovrune.com](mailto:hello@sovrune.com).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [ROADMAP.md](ROADMAP.md). Do not file vulnerabilities publicly.

Apache-2.0 licensed. “Sovrune” and its visual identity are covered by [TRADEMARKS.md](TRADEMARKS.md).
