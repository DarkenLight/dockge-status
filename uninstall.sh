#!/bin/bash
# Dockge Status API Uninstaller
# Stops, disables, and removes all installed files

set -e

INSTALL_DIR="/usr/share/dockge-status"
SERVICE_FILE="/etc/systemd/system/dockge-status-api.service"

echo "⚠️  This will remove Dockge Status API completely."
read -rp "Are you sure you want to continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[yY](es)?$ ]]; then
    echo "Aborted."
    exit 1
fi

# --- Stop and disable the service ---
echo "🛑 Stopping and disabling dockge-status-api.service..."
sudo systemctl stop dockge-status-api.service 2>/dev/null || true
sudo systemctl disable dockge-status-api.service 2>/dev/null || true

# --- Remove files ---
echo "🗑️  Removing service file: $SERVICE_FILE"
sudo rm -f "$SERVICE_FILE"

echo "🗑️  Removing installation directory: $INSTALL_DIR"
sudo rm -rf "$INSTALL_DIR"

# --- Reload systemd ---
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# --- Verify removal ---
if systemctl is-active dockge-status-api.service &>/dev/null; then
    echo "⚠️  Warning: Service is still active. Check with: systemctl status dockge-status-api.service"
else
    echo "✅ Service is stopped and removed."
fi

echo ""
echo "✅ Uninstall complete!"
echo "To also uninstall optional dependencies (jq), run:"
echo "  sudo apt remove -y jq"