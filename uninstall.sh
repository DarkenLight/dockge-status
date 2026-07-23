#!/bin/bash
# Dockge Status API Uninstaller
# Stops, disables, and removes all installed files
#
# Usage:
#   sudo ./uninstall.sh              # Interactive (asks for confirmation)
#   curl ... | bash                  # Non-interactive (skips prompt when piped)
#   sudo ./uninstall.sh -y           # Force skip confirmation

set -e

INSTALL_DIR="/usr/share/dockge-status"
SERVICE_FILE="/etc/systemd/system/dockge-status-api.service"

# Detect if running interactively (has a real terminal) or piped
if [ -t 0 ]; then
    # Interactive terminal — ask for confirmation
    echo "⚠️  This will remove Dockge Status API completely."
    read -rp "Are you sure you want to continue? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[yY](es)?$ ]]; then
        echo "Aborted."
        exit 1
    fi
else
    # Piped / non-interactive — skip prompt unless -y was passed
    if [ "$1" != "-y" ]; then
        # Still try to read from /dev/tty if available
        if exec </dev/tty 2>/dev/null; then
            echo "⚠️  This will remove Dockge Status API completely."
            read -rp "Are you sure you want to continue? [y/N] " confirm
            if [[ ! "$confirm" =~ ^[yY](es)?$ ]]; then
                echo "Aborted."
                exit 1
            fi
        else
            echo "⚠️  Non-interactive mode detected."
            echo "   To force uninstall without confirmation, run:"
            echo "     curl -fsSL https://raw.githubusercontent.com/DarkenLight/dockge-status/main/uninstall.sh | bash -s -- -y"
            echo "Aborted."
            exit 1
        fi
    fi
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