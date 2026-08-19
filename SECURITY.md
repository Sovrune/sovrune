# Security

Sovrune is alpha software. Do not grant it production write access.

Report vulnerabilities privately to **security@sovrune.com**. Include the affected version, reproduction, impact, and any suggested mitigation. Please do not open a public issue before a fix is available.

## Security boundaries

- Provider credentials come from environment variables and are never exposed by the HTTP API.
- Company adapters must emit aggregate state, not customer records.
- The core rejects common PII-shaped keys at its boundary.
- The alpha has no deployment, payment, or production-write capability.
- External action requires an explicit human approval integration that is not part of this alpha.

Operators remain responsible for network isolation, secret management, model-provider terms, backups, and access control.
