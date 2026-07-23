# Dockge Docker Status API

A lightweight Python + Bash hybrid service that exposes Docker container
information (name, status, ports, uptime) over a simple HTTP endpoint
for use with [GetHomepage](https://gethomepage.dev) or similar
dashboards.\
Ideal for environments using Dockge that do not have a native API.

<img width="424" height="136" alt="dockge" src="https://github.com/user-attachments/assets/29e8f033-95de-48b2-809a-c9aa68c7e61b" />

------------------------------------------------------------------------

## Features

-   Simple API using Python (http.server)
-   Reads Docker container data via a Bash script
-   Fully self-hosted, minimal dependencies
-   Runs as a `systemd` service (auto-start at boot)
-   **In-memory caching** with configurable TTL (default: 5s) to reduce Docker daemon load
-   **CORS headers** enabled for browser-based dashboards
-   **Threaded HTTP server** for concurrent request handling
-   **Graceful shutdown** on SIGTERM/SIGINT
-   **Proper logging** with timestamps to stdout (integrates with journalctl)

------------------------------------------------------------------------
## Dependencies:
- jq
- curl
- docker (or docker-cli depending on your implementation)

## Installation

``` bash
curl -fsSL https://raw.githubusercontent.com/DarkenLight/dockge-status/main/install.sh | bash
```

This script will: - Create required directories under
`/usr/share/dockge-status` - Place the Python and Bash scripts in
proper locations - Install the `systemd` service - Enable and start it
automatically

------------------------------------------------------------------------

## Default Configuration

**Currently, configuration is done directly via environment variables in the systemd service file.**

| Variable                  | Description                                  | Default                                                   |
|----------------------------|----------------------------------------------|-----------------------------------------------------------|
| `DOCKGE_STATUS_API_PORT`   | Port number to serve the API                 | `9000`                                                    |
| `DOCKGE_STATUS_SCRIPT_PATH`| Path to the bash script that collects Docker info | `/usr/share/dockge-status/docker-status.sh` |
| `DOCKGE_STATUS_CACHE_TTL`  | Cache TTL in seconds (0 to disable)          | `5`                                                       |

If you want to customize these values, edit the systemd unit file:

``` bash
sudo systemctl edit dockge-status-api.service
```

Then Update
``` bash
sudo systemctl edit dockge-status-api.service
```
Reload and restart:
``` bash
sudo systemctl daemon-reload
sudo systemctl restart dockge-status-api
```

## API Usage

Once running, you can access the following endpoints:

| Endpoint | Description |
|---|---|
| `/info` | Full JSON array of all containers |
| `/summary` | Aggregated stack summary (total, running, unhealthy) |
| `/health` | Health check — returns `{"status": "ok"}` |
| `/container/<name>` | Details for a single container by name |

### Examples

``` bash
# All containers
curl http://localhost:9000/info

# Stack summary
curl http://localhost:9000/summary

# Health check
curl http://localhost:9000/health

# Single container by name
curl http://localhost:9000/container/piwigo
```

**Output Example:**

``` json
{
  "container": "piwigo",
  "status": "running",
  "port": "8080",
  "uptime": "3 days"
}
```

------------------------------------------------------------------------

## Logs

Check logs with:

``` bash
journalctl -u dockge-status-api -f
```

------------------------------------------------------------------------

## Uninstall

``` bash
# Interactive (will ask for confirmation)
sudo ./uninstall.sh

# Force uninstall without confirmation
sudo ./uninstall.sh -y
```

Or fetch and run directly from the repository:
``` bash
# Interactive (will ask for confirmation if possible)
curl -fsSL https://raw.githubusercontent.com/DarkenLight/dockge-status/main/uninstall.sh | bash

# Force uninstall without confirmation (non-interactive)
curl -fsSL https://raw.githubusercontent.com/DarkenLight/dockge-status/main/uninstall.sh | bash -s -- -y
```

The script will:
  - Stop and disable the systemd service
  - Remove all installed files from `/usr/share/dockge-status`
  - Remove the systemd unit file
  - Reload systemd daemon
  - Verify the service is no longer active

> **Note:** When piped via `curl ... | bash`, the script runs in non-interactive mode. Use the `-y` flag to skip the confirmation prompt.

------------------------------------------------------------------------

## GetHomepage Integration Example

### Here’s how to display your Docker status summary on GetHomepage:

``` bash
- Dockge:
    icon: /icons/dockge.png
    href: http://<IPADDRESS>:5001
    description: Docker Manager
    siteMonitor: http://<IPADDRESS>:5001
    widget:
      type: customapi
      url: http://<IPADDRESS>:9000/summary
      refreshInterval: 10000
      method: GET
      mappings:
        - field: total_stacks
          label: Total
          format: number
        - field: healthy_stacks
          label: Running
          format: number
        - field: unhealthy_stacks
          label: Unhealthy
          format: number
        - field: error_nodes
          label: Stopped Node
          format: number

```
------------------------------------------------------------------------

## Contributing

Pull requests and issues are welcome!

------------------------------------------------------------------------

## License

MIT License
