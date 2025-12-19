#!/usr/bin/env bash

echo "Installing MATE CMD Chart Applet..."

pushd mate || { echo "No mate directory! Exiting."; exit 1; }

# Copy files to system directories
sudo cp cmd-chart-applet.py /usr/lib/mate-applets/
sudo cp org.mate.panel.CmdChartApplet.mate-panel-applet /usr/share/mate-panel/applets/
sudo cp cmd-chart-applet.desktop /usr/share/applications/
sudo cp org.mate.panel.applet.CmdChartAppletFactory.service /usr/share/dbus-1/services/
sudo cp org.mate.panel.applet.CmdChartApplet.gschema.xml /usr/share/glib-2.0/schemas/
sudo glib-compile-schemas /usr/share/glib-2.0/schemas/

# Set proper permissions
sudo chmod +x /usr/lib/mate-applets/cmd-chart-applet.py

echo "Installation complete!"
echo "Restart MATE panel: mate-panel --replace &"
echo "You can now add the MATE CMD Chart applet to your MATE panel by:"
echo "1. Right-clicking on the panel"
echo "2. Selecting 'Add to Panel...'"
echo "3. Finding 'CMD Chart Monitor' in the list"

popd || exit 2

