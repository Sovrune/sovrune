# Accountability spine

Sovrune Community Edition stores operating runs in SQLite. A run is one immutable company snapshot plus office artifacts, a proposed decision, a pending approval, and a prediction that cannot open before approval.

```text
BusinessState
    │
    ▼
Operating run ──► 7 office artifacts
    │
    ├──► proposed decision ──► pending approval
    │                              │
    │                     approve ─┴─ reject
    │                         │          │
    └──► prediction      open       cancelled
```

## Run locally

```bash
export SOVRUNE_DB=./data/sovrune.db
sovrune operate
sovrune runs
sovrune approvals
```

`sovrune operate` validates the configured Company Adapter and writes the whole accountability chain in one transaction. A failed insert leaves no partial run.

Resolve a pending decision using the approval ID printed by `sovrune operate` or `sovrune approvals`:

```bash
sovrune approve apr_... --by nishank --note "Run the bounded experiment"
sovrune reject apr_... --by nishank --note "Evidence is not fresh enough"
```

An approval is single-use. Approval changes the decision to `approved`, the run to `approved`, and the prediction from `pending_approval` to `open`. Rejection changes the decision and run to `rejected` and cancels the prediction.

## HTTP API

Reads:

```text
GET /api/runs
GET /api/runs/{run_id}
GET /api/approvals
```

The accountability HTTP API, including reads, is disabled by default because decisions and approver identities are company-confidential. To enable it, configure a random token of at least 24 characters:

```bash
export SOVRUNE_APPROVAL_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Then send the token only in the request header for every accountability request:

```text
POST /api/runs
X-Sovrune-Approval-Token: ...

POST /api/approvals/{approval_id}
X-Sovrune-Approval-Token: ...
Content-Type: application/json

{"action":"approve","actor":"nishank","note":"bounded experiment approved"}
```

The header is compared in constant time and is never returned by the API. This alpha token is an operator control, not multi-user authentication. Do not expose mutation endpoints publicly until authentication and role-based authorization ship.

## Storage and reliability

- SQLite uses foreign keys, transactions, WAL mode, uniqueness constraints, and bounded status enums.
- Docker stores the database in the named `sovrune-data` volume.
- IDs are opaque UUID-based strings and do not encode company information.
- Evidence is copied into the decision so a later adapter change cannot rewrite its original basis.
- SQLite is appropriate for one-company Community Edition. Managed multi-company deployments should use PostgreSQL, authenticated identities, tenant-scoped rows, migrations, backups, and an append-only audit event table.

## What remains

This slice does not execute the approved action or grade an outcome. The next accountability increment adds due-window selection, measurement ingestion, explicit verdicts, and append-only audit events.
