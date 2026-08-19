# Deployment and operations

This runbook covers a single-company Community Edition deployment using Docker Compose and SQLite. For multi-company use, do not share this database between tenants; use separate isolated instances until tenant-aware storage and authorization ship.

## Prerequisites

- Docker Engine with Compose
- A reviewed `.env` file readable only by the service operator
- A writable persistent volume
- TLS and upstream authentication for any network beyond localhost
- A tested backup destination outside the Docker volume

## Deploy

```bash
git clone https://github.com/Sovrune/sovrune
cd sovrune
cp .env.example .env
docker compose up --build -d
docker compose ps
curl http://127.0.0.1:8787/healthz
```

The Compose service publishes port `8787` and stores SQLite data in the `sovrune-data` named volume. Set `SOVRUNE_APPROVAL_TOKEN` before using accountability endpoints over HTTP.

## Reverse proxy requirements

Terminate TLS at a maintained reverse proxy or private ingress. The proxy should:

- require organizational authentication for every route;
- remove any client-supplied identity headers it creates itself;
- limit request bodies to 64 KiB or less;
- apply request rate limits and access logging without logging the approval-token header;
- forward to Sovrune on a private interface;
- expose `/healthz` only to the load balancer or monitoring system.

The built-in Python server is an application server for the alpha, not an internet security perimeter.

## Backup

For the safest simple backup, briefly stop the service so the SQLite database and WAL cannot change during the copy:

```bash
docker compose stop sovrune
SOVRUNE_VOLUME="$(docker volume ls \
  --filter label=com.docker.compose.volume=sovrune-data \
  --format '{{.Name}}')"
docker run --rm \
  -v "$SOVRUNE_VOLUME:/source:ro" \
  -v "$PWD/backups:/backup" \
  alpine cp /source/sovrune.db /backup/sovrune.db
docker compose start sovrune
```

Confirm `SOVRUNE_VOLUME` contains exactly one expected volume name before running the copy; Compose normally prefixes it with the project name. Store backups encrypted outside the host and test restoration regularly.

## Restore

Restoration replaces accountability history, so announce the maintenance window and preserve the current volume before proceeding.

1. Stop Sovrune.
2. Copy the selected database into a new named volume as `/app/data/sovrune.db`.
3. Point a temporary deployment at that volume.
4. Start it and verify `/healthz`, `sovrune runs`, and `sovrune approvals`.
5. Promote the restored deployment only after the run counts and latest approval state match expectations.

Do not overwrite the only copy of a database during restore.

## Upgrade

```bash
git fetch --tags
git checkout v0.3.0-alpha.1
docker compose build
docker compose up -d
curl http://127.0.0.1:8787/healthz
```

Before changing versions, take a backup and read the release notes. Sovrune applies additive SQLite schema initialization at startup, but the alpha does not yet provide downgrade migrations.

## Rollback

If health or smoke checks fail:

1. Stop the new container without deleting the volume.
2. Start the previously tested image against a database compatible with that version.
3. If the database changed incompatibly, restore the pre-upgrade backup into a new volume.
4. Confirm health, run listing, and pending approvals before reopening access.

Never use `docker compose down -v` in routine operations; `-v` deletes the named data volume.

## Operational checks

- Every minute: `GET /healthz` returns `200` and the expected version.
- After configuration changes: `/api/provider` reports the intended provider and model.
- Before each operating run: the adapter validates and its evidence dates are current.
- Daily: review pending approvals and failed application logs.
- Regularly: create and restore-test an encrypted backup.

See [troubleshooting](TROUBLESHOOTING.md) for common failures and [SECURITY.md](../SECURITY.md) for trust boundaries.
