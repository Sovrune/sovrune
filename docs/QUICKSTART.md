# Five-minute Company Adapter quickstart

This path gets a fictional aggregate company state into Sovrune. It does not ask for database credentials, customer records, or an LLM API key.

## 1. Install

```bash
git clone https://github.com/Sovrune/sovrune
cd sovrune
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Python 3.11 or newer is required.

## 2. Generate your adapter

```bash
sovrune init "North Star Labs" --output ./north-star --provider ollama
```

The command creates:

```text
north-star/
├── adapter.py       # aggregate BusinessState builder
├── .env.example     # adapter and provider selection; no credentials
└── .gitignore       # excludes .env and Python cache files
```

## 3. Validate the boundary

Use the exact validation command printed by `sovrune init`. For this example:

```bash
sovrune validate './north-star/adapter.py:NorthStarLabsAdapter'
```

A valid result looks like:

```text
valid adapter ./north-star/adapter.py:NorthStarLabsAdapter: North Star Labs · 1 metrics · confidence 0.800
```

Validation fails before startup when the class is wrong, the return value is not `BusinessState`, evidence is incomplete, confidence is invalid, or a PII-shaped key crosses the boundary.

## 4. Run it

```bash
cp north-star/.env.example .env
set -a; . ./.env; set +a
sovrune serve
```

Open <http://127.0.0.1:8787>. The starter uses Ollama, but the deterministic operating loop and dashboard work before a model is configured.

## 5. Replace fictional aggregates

Edit `north-star/adapter.py`. Keep data access inside `build_state()` and return only aggregate `Metric`, risk, and experiment values with evidence provenance. Run `sovrune validate` after every change.

Next: [Company Adapter SDK reference](ADAPTER_SDK.md).
