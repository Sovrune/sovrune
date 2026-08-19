# Sovrune documentation

Sovrune turns an aggregate company snapshot into a reviewable operating run: sourced evidence, coordinated office artifacts, one proposed decision, a human approval, and a prediction to measure later.

The current release is an alpha. It is suitable for evaluation and bounded internal pilots. It must not receive customer-level data or production write credentials.

## Choose a path

### Evaluate locally

1. Follow the [five-minute quickstart](QUICKSTART.md).
2. Run the fictional Acme adapter before connecting company data.
3. Read the [accountability contract](ACCOUNTABILITY.md) to understand what is persisted and where human approval stops execution.

### Connect a company

1. Read the [Company Adapter SDK](ADAPTER_SDK.md).
2. Generate a starter with `sovrune init`.
3. Configure a model using the [configuration reference](CONFIGURATION.md).
4. Validate the adapter before starting the server.

### Operate a deployment

1. Use the [deployment and operations runbook](DEPLOYMENT.md).
2. Review the [HTTP API reference](API.md) before exposing any endpoint.
3. Apply the controls in [SECURITY.md](../SECURITY.md).
4. Use [troubleshooting](TROUBLESHOOTING.md) when a health, adapter, database, or provider check fails.

### Contribute

Read [CONTRIBUTING.md](../CONTRIBUTING.md), select an item from [ROADMAP.md](../ROADMAP.md), and include tests and documentation with behavior changes.

## Product boundaries

The alpha can read aggregate state, produce deterministic office artifacts, persist a decision chain, and collect a single-use human approval. It does not execute the approved action, grade predictions, provide multi-user authentication, or isolate multiple companies in one database.

Company adapters and model providers are separate boundaries: the adapter supplies normalized business evidence; the provider supplies model inference. The deterministic demo and accountability loop work without giving an LLM direct access to company systems.
