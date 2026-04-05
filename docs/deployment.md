# Deployment

## Running as a launchd service

A launchd agent keeps Things API running in the background. It starts automatically at login and restarts if it crashes.

### 1. Run the setup wizard

If you haven't already:

```sh
things-api init
```

This creates your config at `~/.config/things-api/config`.

### 2. Edit the plist template

Open `com.things-api.server.plist` in the project root (or [download it from GitHub](https://github.com/jaydenk/things-api/blob/main/com.things-api.server.plist)) and set the path to `uvx`:

```xml
<key>ProgramArguments</key>
<array>
    <string>/opt/homebrew/bin/uvx</string>
    <string>things-api</string>
</array>
```

Find the correct path with `which uvx`. launchd does not inherit your shell's `PATH`, so you must use the full path.

### 3. Grant Full Disk Access

macOS restricts launchd agents from accessing the Things SQLite database in `~/Library/Group Containers/`. You must grant Full Disk Access to `uv`:

1. Open **System Settings > Privacy & Security > Full Disk Access**
2. Click `+`, press `Cmd+Shift+G`, and enter `/opt/homebrew/bin/uv`
3. Toggle it on

Without this, the server will hang on startup trying to read the database.

### 4. Install and load

```sh
cp com.things-api.server.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.things-api.server.plist
```

### 5. Verify

```sh
curl -s http://localhost:5225/health -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Stop and unload

```sh
launchctl bootout gui/$(id -u)/com.things-api.server
```

To reload after editing the plist, bootout then bootstrap again.

### Logs

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

By default, the server binds to `0.0.0.0`, making it accessible on all network interfaces. To restrict to localhost only, add `THINGS_API_HOST=127.0.0.1` to your config file at `~/.config/things-api/config`.

For remote access (e.g. from another machine on your network or via [Tailscale](https://tailscale.com/)), the default `0.0.0.0` binding works — just ensure the port (default `5225`) is accessible and use your machine's IP or Tailscale hostname in requests.
