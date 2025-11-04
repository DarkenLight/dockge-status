#!/bin/bash
# Dockge Status API installer
# Installs Bash + Python API system-wide under /usr/share/dockge-status

set -e

REPO_URL="https://raw.githubusercontent.com/DarkenLight/dockge-status/main"
INSTALL_DIR="/usr/share/dockge-status"
SERVICE_FILE="/etc/systemd/system/dockge-status-api.service"

echo "📦 Installing Dockge Status API..."

# Create install directory
sudo mkdir -p "$INSTALL_DIR"

# Download main files
sudo curl -fsSL "$REPO_URL/docker-status.sh" -o "$INSTALL_DIR/docker-status.sh"
sudo curl -fsSL "$REPO_URL/docker-status-api.py" -o "$INSTALL_DIR/docker-status-api.py"

# Make executable
sudo chmod +x "$INSTALL_DIR"/*.sh "$INSTALL_DIR"/*.py

# Download and place systemd service
sudo curl -fsSL "$REPO_URL/dockge-status-api.service" -o "$SERVICE_FILE"

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable --now dockge-status-api.service

echo "✅ Installation complete!"
echo "Service: dockge-status-api"
echo "Check logs: journalctl -u dockge-status-api -f"
echo "API available at: http://<server-ip>:9000/info or /summary"
