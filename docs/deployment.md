# Deployment

These instructions assume you've already completed the [Getting Started](../README.md#getting-started) steps — the repo is cloned, dependencies are installed, and your `.env` file is configured.

## Running as a launchd service

A launchd agent keeps Things API running in the background. It starts automatically at login and restarts if it crashes.

### 1. Edit the plist template

Open `com.things-api.server.plist` in the project root and set two paths:

**`WorkingDirectory`** — the absolute path to your cloned `things-api` directory. This is where the server looks for your `.env` file.

```xml
<key>WorkingDirectory</key>
<string>/Users/yourname/things-api</string>
```

**`ProgramArguments`** — the absolute path to `uv`. Find it with `which uv`.

```xml
<key>ProgramArguments</key>
<array>
    <string>/opt/homebrew/bin/uv</string>
    <string>run</string>
    <string>things-api</string>
</array>
```

> **Note:** launchd does not inherit your shell's `PATH`, so you must use the full path to `uv`.

### 2. Install and load

```sh
cp com.things-api.server.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.things-api.server.plist
```

### 3. Verify

```sh
curl -s http://localhost:5225/health -H "Authorization: Bearer YOUR_TOKEN"
```

You should see `{"status":"healthy","read":true,...}`.

### 4. Stop and unload

```sh
launchctl bootout gui/$(id -u)/com.things-api.server
```

To reload after editing the plist, bootout then bootstrap again.

### Logs

```sh
tail -f /tmp/things-api.log
```

### How it works

- **`WorkingDirectory`** — launchd starts the process in your project directory, so `pydantic-settings` automatically loads the `.env` file. No tokens need to be hardcoded in the plist.
- **`KeepAlive: true`** — restarts the process if it crashes.
- **`RunAtLoad: true`** — starts when you log in.

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
