# Troubleshooting

Start with three checks:

```bash
sovrune validate "${SOVRUNE_COMPANY_ADAPTER:-sovrune.demo:AcmeAdapter}"
curl http://127.0.0.1:8787/healthz
curl http://127.0.0.1:8787/api/provider
```

## The command center does not open

- Confirm `sovrune serve` is still running and note its printed address.
- If accessing another machine or container, bind deliberately with `sovrune serve --host 0.0.0.0`; add firewall and proxy controls first.
- Check whether port `8787` is already occupied or change it with `--port`/`SOVRUNE_PORT`.
- With Docker, inspect `docker compose ps` and `docker compose logs sovrune`.

## Adapter validation fails

- Use `module:Class` or `/absolute/path/adapter.py:Class`.
- Ensure the class has a no-argument constructor and subclasses `CompanyAdapter`.
- Return a `BusinessState`, not a dictionary.
- Give every metric evidence with `source`, `as_of`, and confidence from `0` to `1`.
- Remove customer records and keys shaped like email, phone, address, card, password, secret, or token.

Run `sovrune validate` after each adapter change before restarting the service.

## Provider reports `configured: false`

- Confirm the shell exported `.env`; installing the file alone does not load it outside Docker Compose.
- Hosted providers require their matching API-key variable.
- OpenAI-compatible local endpoints without a key must use a loopback URL.
- `configured: true` does not perform a network request. Verify model existence, endpoint reachability, account quota, and provider permissions separately.

Provider failures intentionally omit remote response bodies to reduce accidental credential or data leakage. Consult the provider's own logs when using a local gateway.

## Accountability API returns `503`

`SOVRUNE_APPROVAL_TOKEN` is missing or shorter than 24 characters in the server process. Generate a strong token, restart the service, and send the same value in `X-Sovrune-Approval-Token`.

## Accountability API returns `401`

The request header is absent or does not match the server value. Check shell expansion and proxy configuration. Do not put the token in a URL query string.

## Approval returns `409`

Read the error body. The approval may not exist, may already be resolved, or the request may have an invalid `action` or blank `actor`. List current pending approvals with:

```bash
sovrune approvals
```

## Runs disappear between restarts

Confirm every command and server process uses the same `SOVRUNE_DB` path. With Docker, ensure the `sovrune-data` volume is mounted at `/app/data` and do not use `docker compose down -v`.

Relative database paths are resolved from the process working directory. Prefer an absolute path for non-Docker services.

## Database is locked

Sovrune enables SQLite WAL mode and waits briefly for locks, but Community Edition is designed for one modest instance. Stop duplicate writers, verify the database is on a local filesystem rather than a network share, and retry. Do not delete `-wal` or `-shm` files from a running database.

## What to include in a bug report

Include the Sovrune version, operating system, Python or Docker version, command used, expected behavior, and a minimal fictional adapter that reproduces the issue. Remove credentials, approval tokens, real company metrics, customer data, private URLs, and database files.
