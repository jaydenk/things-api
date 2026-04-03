# Deployment

## Running as a launchd service

Create a launchd agent so Things API starts automatically at login and restarts if it crashes.

### 1. Set up your `.env` file

The server reads configuration from a `.env` file in its working directory. If you haven't already:

```sh
cd /path/to/things-api
cp env.example .env
# Edit .env and set THINGS_API_TOKEN (required) and THINGS_AUTH_TOKEN (optional, for writes)
```

### 2. Edit the plist template

Open `com.things-api.server.plist` and update:

- **`WorkingDirectory`** — the path to your `things-api` directory (where `.env` lives)
- **`ProgramArguments`** — the path to `uv` (run `which uv` to find it)

The plist includes two options:

| Option | When to use | ProgramArguments |
|---|---|---|
| **A: Local source** (default) | Development, or before publishing to PyPI | `uv run things-api` — runs from the local project |
| **B: PyPI** | After publishing the package | `uvx things-api` — downloads and runs from PyPI |

### 3. Install the plist

```sh
cp com.things-api.server.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.things-api.server.plist
```

### 4. Verify it's running

```sh
curl -s http://localhost:5225/health -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Stop and unload

```sh
launchctl bootout gui/$(id -u)/com.things-api.server
```

### Logs

Logs are written to `/tmp/things-api.log`:

```sh
tail -f /tmp/things-api.log
```

### How it works

- **`WorkingDirectory`** tells launchd to start the process in your project directory, so `pydantic-settings` automatically finds and loads the `.env` file — no need to duplicate tokens in the plist itself.
- **`KeepAlive: true`** restarts the process if it crashes.
- **`RunAtLoad: true`** starts it when you log in.

## n8n integration

Things API works well as a backend for [n8n](https://n8n.io/) workflows. Use an **HTTP Request** node:

| Setting | Value |
|---|---|
| Method | `GET` / `POST` / `PUT` / `DELETE` |
| URL | `http://<host>:5225/today` (or any endpoint) |
| Authentication | Header Auth |
| Header Name | `Authorization` |
| Header Value | `Bearer YOUR_TOKEN_HERE` |
| Response Format | JSON |

For write operations, set the body content type to JSON and pass the relevant fields (e.g. `{"title": "New task", "when": "today"}`).

## Network access

By default, the server binds to `0.0.0.0`, making it accessible on all network interfaces. To restrict to localhost only, set `THINGS_API_HOST=127.0.0.1` in your `.env`.

For remote access (e.g. from another machine on your network or via [Tailscale](https://tailscale.com/)), the default `0.0.0.0` binding works — just ensure the port (default `5225`) is accessible and use your machine's IP or Tailscale hostname in requests.
