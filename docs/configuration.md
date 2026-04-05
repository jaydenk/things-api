# Configuration

## Quick setup

Run the interactive setup wizard:

```sh
things-api init
```

This generates an API token, detects your Things URL scheme settings, and writes the config to `~/.config/things-api/config`. If you skip this step, the wizard runs automatically on first launch.

## Config resolution order

Settings are resolved in this priority (highest wins):

```
CLI flags (--token, --port)
    ↓
Environment variables (THINGS_API_TOKEN, etc.)
    ↓
~/.config/things-api/config
    ↓
.env in current working directory
    ↓
Defaults
```

## CLI flags

```sh
things-api --token SECRET --port 8080
```

Only `--token` and `--port` are available as flags. All other settings use the config file or environment variables.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `THINGS_API_HOST` | No | `0.0.0.0` | Address the server binds to |
| `THINGS_API_PORT` | No | `5225` | Port the server listens on |
| `THINGS_API_TOKEN` | **Yes** | — | Bearer token used to authenticate every request. The server refuses to start without it. |
| `THINGS_AUTH_TOKEN` | No | — | Things URL scheme auth token — enables write operations (create, update, complete, cancel) |
| `THINGS_DB_PATH` | No | Auto-detected | Override the path to the Things SQLite database. By default, `things.py` finds it automatically. |
| `THINGS_VERIFY_TIMEOUT` | No | `0.5` | Seconds to wait after a write before reading back the result for verification |

## Config file format

The config file at `~/.config/things-api/config` uses dotenv format:

```dotenv
THINGS_API_TOKEN=tk_a7f3b9c2e1d8...
THINGS_AUTH_TOKEN=your-things-auth-token
THINGS_API_PORT=5225
```

## Read-only vs read-write mode

Without `THINGS_AUTH_TOKEN`, the API runs in **read-only mode**. All `GET` endpoints work normally, but `POST`, `PUT`, and `DELETE` return `503 Service Unavailable`.

To enable write operations:

1. Open **Things 3**
2. Go to **Settings > General > Enable Things URLs**
3. Copy the auth token
4. Run `things-api init` and paste the token when prompted, or add `THINGS_AUTH_TOKEN=...` to your config file

## Security notes

- `THINGS_API_TOKEN` is stored internally as a `SecretStr` — it will not appear in logs, stack traces, or error messages.
- All authentication uses timing-safe comparison to prevent timing attacks.
- Failed authentication attempts are rate-limited (10 per minute per IP).
- The Swagger/ReDoc documentation UI is disabled. The API schema is not exposed at `/docs` or `/redoc`.
