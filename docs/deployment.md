# Deployment

## Running as a launchd service

Create a launchd agent so Things API starts automatically at login.

### 1. Copy the plist template

```sh
cp com.things-api.server.plist ~/Library/LaunchAgents/
```

### 2. Edit the plist

Open `~/Library/LaunchAgents/com.things-api.server.plist` and set:
- The path to `uvx` (run `which uvx` to find it)
- Your `THINGS_API_TOKEN`
- Your `THINGS_AUTH_TOKEN` (if you want write access)

### 3. Load the agent

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.things-api.server.plist
```

### 4. Stop and unload

```sh
launchctl bootout gui/$(id -u)/com.things-api.server
```

### Logs

The plist template writes logs to `/tmp/things-api.log`. Check them with:

```sh
tail -f /tmp/things-api.log
```

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
