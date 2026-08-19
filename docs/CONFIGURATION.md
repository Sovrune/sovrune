# Configuration and model providers

Sovrune reads configuration from environment variables. The application does not parse `.env` itself; Docker Compose loads it automatically, while a local shell must export it before running `sovrune`.

```bash
cp .env.example .env
set -a
. ./.env
set +a
sovrune serve
```

Never commit `.env` or real provider credentials.

## Core settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `SOVRUNE_COMPANY_ADAPTER` | `sovrune.demo:AcmeAdapter` | Adapter in `module:Class` or `/absolute/file.py:Class` form |
| `SOVRUNE_DB` | `./sovrune.db` | SQLite database path; Docker defaults to `/app/data/sovrune.db` |
| `SOVRUNE_HOST` | `127.0.0.1` | HTTP bind address |
| `SOVRUNE_PORT` | `8787` | HTTP listen port |
| `SOVRUNE_APPROVAL_TOKEN` | unset | Enables protected accountability endpoints when at least 24 characters |
| `SOVRUNE_PROVIDER` | `none` | `ollama`, `openai`, `openai-compatible`, `anthropic`, or `gemini` |
| `SOVRUNE_MODEL` | provider-specific | Model identifier sent to the provider |

Generate an approval token with a cryptographically secure random source:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

## Ollama

```dotenv
SOVRUNE_PROVIDER=ollama
SOVRUNE_MODEL=qwen3
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

From Docker Desktop, use `http://host.docker.internal:11434` to reach Ollama on the host. Ensure the selected model is already available in Ollama.

## OpenAI

```dotenv
SOVRUNE_PROVIDER=openai
SOVRUNE_MODEL=gpt-5
OPENAI_API_KEY=replace-me
```

Sovrune uses the OpenAI-compatible chat-completions shape in this alpha.

## OpenAI-compatible endpoints

```dotenv
SOVRUNE_PROVIDER=openai-compatible
SOVRUNE_MODEL=your-model-id
SOVRUNE_OPENAI_BASE_URL=https://provider.example/v1
OPENAI_API_KEY=replace-me
```

The base URL must exclude `/chat/completions`; Sovrune appends it. A key is optional only for loopback URLs beginning with `http://localhost` or `http://127.0.0.1`.

## Anthropic

```dotenv
SOVRUNE_PROVIDER=anthropic
SOVRUNE_MODEL=claude-sonnet-4-5
ANTHROPIC_API_KEY=replace-me
```

## Gemini

```dotenv
SOVRUNE_PROVIDER=gemini
SOVRUNE_MODEL=gemini-2.5-pro
GEMINI_API_KEY=replace-me
```

## Verify configuration

Start Sovrune and inspect the provider status. The response reports only provider name, model name, and whether required configuration is present; it never returns the credential.

```bash
curl http://127.0.0.1:8787/api/provider
```

Then validate the company boundary separately:

```bash
sovrune validate "$SOVRUNE_COMPANY_ADAPTER"
```

`configured: true` confirms that required settings exist, not that the remote provider is reachable or that the model identifier is valid.
