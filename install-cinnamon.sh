#!/bin/bash

# CMD Chart Applet Cinnamon Installation Script

set -e

APPLET_UUID="cmd-chart-applet@cinnamon"
APPLET_DIR="$HOME/.local/share/cinnamon/applets/$APPLET_UUID"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing CMD Chart Applet for Cinnamon..."

# Check if Cinnamon is installed
if ! command -v cinnamon &> /dev/null; then
    echo "Error: Cinnamon desktop environment not found."
    echo "This applet is designed for the Cinnamon desktop environment."
    exit 1
fi

# Create applet directory
echo "Creating applet directory: $APPLET_DIR"
mkdir -p "$APPLET_DIR"

# Copy applet files
echo "Copying applet files..."
cp "$SCRIPT_DIR/$APPLET_UUID/applet.js" "$APPLET_DIR/"
cp "$SCRIPT_DIR/$APPLET_UUID/metadata.json" "$APPLET_DIR/"
cp "$SCRIPT_DIR/$APPLET_UUID/settings-schema.json" "$APPLET_DIR/"

echo "Installation completed successfully!"
echo
echo "IMPORTANT: Restart Cinnamon to load the new applet:"
echo "  Press Alt+F2, type 'r', press Enter"
echo
echo "To add the applet to your panel:"
echo "1. Right-click on the Cinnamon panel"
echo "2. Select 'Applets'"
echo "3. Click on 'Installed' tab and look for 'CMD Chart Applet'"
echo "4. Click the '+' button to add it to your panel"
echo
echo "To configure the applet:"
echo "- Right-click on the applet and select 'Configure'"
echo "- Set your command (default: echo \"[g]\")"
echo "- Set update interval in seconds (default: 60)"
echo
echo "For monitoring logs:"
echo "  journalctl -f | grep 'CMD Chart Applet'"