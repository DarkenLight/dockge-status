# Dockge Docker Status API

A lightweight Python + Bash hybrid service that exposes Docker container
information (name, status, ports, uptime) over a simple HTTP endpoint
for use with [GetHomepage](https://gethomepage.dev) or similar
dashboards.\
Ideal for environments using Dockge that do not have a native API.

------------------------------------------------------------------------

## Features

-   Simple API using Python (http.server)
-   Reads Docker container data via a Bash script
-   Fully self-hosted, minimal dependencies
-   Runs as a `systemd` service (auto-start at boot)

------------------------------------------------------------------------

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
| `DOCKGE_STATUS_PORT`       | Port number to serve the API                 | `9000`                                                    |
| `DOCKGE_STATUS_SCRIPT_PATH`| Path to the bash script that collects Docker info | `/usr/share/dockge-status/docker-status.sh` |

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

Once running, you can access:

``` bash
curl http://localhost:9000/info
curl http://localhost:9000/summary
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
journalctl -u dockge-status -f
```

------------------------------------------------------------------------

## Uninstall

``` bash
systemctl stop dockge-status-api
systemctl disable dockge-status-api
rm -rf /usr/share/dockge-status
rm /etc/systemd/system/dockge-status-api.service
systemctl daemon-reload
```

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
