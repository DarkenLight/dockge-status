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

**Environment Variables (set in `/usr/share/dockge-status/.env`):**

| Variable                  | Description                                  | Default                                                   |
|----------------------------|----------------------------------------------|-----------------------------------------------------------|
| `DOCKGE_STATUS_PORT`       | Port number to serve the API                 | `9000`                                                    |
| `DOCKGE_STATUS_SCRIPT_PATH`| Path to the bash script that collects Docker info | `/usr/share/dockge-status/docker-status.sh` |


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

## After Installation

-   The service will start automatically.

-   API available at: `http://<your_ip>:9000`

-   You can adjust configuration in `.env` and restart the service with:

    ``` bash
    systemctl restart dockge-status
    ```

------------------------------------------------------------------------

## Contributing

Pull requests and issues are welcome!

------------------------------------------------------------------------

## License

MIT License
