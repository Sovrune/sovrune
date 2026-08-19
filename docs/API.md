# HTTP API reference

The alpha API is JSON over HTTP. It has two trust levels:

- Inspection endpoints (`/healthz`, `/api/state`, `/api/loop`, and `/api/provider`) do not require a token.
- Accountability endpoints expose company decisions and require `X-Sovrune-Approval-Token`.

Do not place the server directly on the public internet. Put it behind TLS and access control, and remember that the alpha token is one shared operator secret rather than user authentication.

## Authentication

Set a random token with at least 24 characters:

```bash
export SOVRUNE_APPROVAL_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Pass it on every accountability request:

```bash
curl -H "X-Sovrune-Approval-Token: $SOVRUNE_APPROVAL_TOKEN" \
  http://127.0.0.1:8787/api/runs
```

If the server token is absent or too short, protected endpoints return `503`. A missing or incorrect request token returns `401`.

## Inspection endpoints

### `GET /healthz`

Returns process health and the installed Sovrune version.

```json
{"status":"ok","version":"0.3.0-alpha.1"}
```

### `GET /api/state`

Builds and validates the configured adapter, then returns the normalized `BusinessState`. Because this can expose aggregate company metrics, protect it at the reverse proxy in any non-local deployment.

### `GET /api/loop`

Builds the configured state and returns the deterministic office loop without creating a durable run.

### `GET /api/provider`

Returns `configured`, `provider`, and `model`. Credentials are never included.

## Accountability endpoints

### `POST /api/runs`

Creates one run, its office artifacts, decision, approval, and blocked prediction in a single database transaction. The request body may be empty because state comes from the configured adapter.

```bash
curl -X POST \
  -H "X-Sovrune-Approval-Token: $SOVRUNE_APPROVAL_TOKEN" \
  http://127.0.0.1:8787/api/runs
```

Returns `201` with the complete created run.

### `GET /api/runs`

Returns up to 50 newest run summaries as `{"runs": [...]}`.

### `GET /api/runs/{run_id}`

Returns the immutable state snapshot, artifacts, decision, approval, and prediction for one run. Returns `404` when the ID does not exist.

### `GET /api/approvals`

Returns pending approvals as `{"approvals": [...]}`.

### `POST /api/approvals/{approval_id}`

Resolves a pending approval exactly once.

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Sovrune-Approval-Token: $SOVRUNE_APPROVAL_TOKEN" \
  -d '{"action":"approve","actor":"operator-name","note":"Bounded pilot approved"}' \
  http://127.0.0.1:8787/api/approvals/apr_example
```

`action` must be `approve` or `reject`, and `actor` must be non-empty. Approval opens the prediction; rejection cancels it. A repeated or concurrently changed approval returns `409`.

## Error responses

Errors use a stable top-level shape:

```json
{"error":"human-readable description"}
```

| Status | Meaning |
| --- | --- |
| `400` | Invalid content length or malformed JSON |
| `401` | Missing or incorrect approval token |
| `404` | Endpoint or run not found |
| `409` | Invalid approval action, missing actor, unknown approval, or already-resolved approval |
| `413` | Request body exceeds 64 KiB |
| `503` | Accountability API disabled because the server token is unset or too short |

The alpha has no pagination parameters, rate limiting, CORS policy, user sessions, or role-based authorization. Add these at the gateway or keep the API on a trusted private network.
