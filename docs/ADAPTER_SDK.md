# Company Adapter SDK

## Contract

An adapter is a no-argument subclass of `CompanyAdapter` whose `build_state()` method returns one validated `BusinessState`.

```text
Company analytics / APIs
          │ read-only aggregation
          ▼
    CompanyAdapter.build_state()
          │ BusinessState with evidence
          ▼
  validation + PII-shaped-key firewall
          │
          ▼
       Sovrune offices
```

Sovrune owns the normalized operating contract. The company owns authentication, queries, aggregation, and source-specific failure handling inside its adapter.

## Load an adapter

Set either a Python module reference or file reference:

```bash
SOVRUNE_COMPANY_ADAPTER=my_company.adapter:MyCompanyAdapter
SOVRUNE_COMPANY_ADAPTER=/opt/my-company/adapter.py:MyCompanyAdapter
```

When the variable is absent, Sovrune loads `sovrune.demo:AcmeAdapter`.

## Required state

- `company`: display name.
- `north_star`: a `Metric` with evidence.
- `metrics`: aggregate supporting metrics.
- `risks` and `experiments`: optional aggregate dictionaries.
- Every `Evidence` needs a source, `as_of` date, and confidence from `0` to `1`.

The state validator rejects keys named `email`, `phone`, `address`, `card`, `password`, `secret`, or `token` anywhere in the payload. This is a guardrail, not a substitute for source-system access control or review.

## Operational guidance

- Use a read-only service identity for company systems.
- Aggregate before constructing `BusinessState`.
- Put no credentials or customer-level records in returned objects or exceptions.
- Convert source failures into a clear adapter exception; do not silently invent metrics.
- Keep `build_state()` bounded. Add source-specific retries and timeouts inside the adapter.
- Run `sovrune validate module:Class` in CI before deployment.

## Current trade-offs

The alpha contract is synchronous and stateless. That makes adapters easy to test and deploy, but long-running collectors should materialize aggregates before Sovrune reads them. A future version can add async collection, capability declarations, freshness policy, and versioned schemas without giving the operating layer direct production access.
