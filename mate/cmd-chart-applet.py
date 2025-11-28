#!/usr/bin/env python3

import subprocess
import traceback
import sys
import signal
import os
import re
import json

import gi
import cairo
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('MatePanelApplet', '4.0')
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, Gdk, MatePanelApplet  # pyright: ignore[reportAttributeAccessIssue] # noqa: E402,E501
from gi.repository import GLib  # pyright: ignore[reportAttributeAccessIssue] # noqa: E402,E501


class CmdChartApplet():
    def __init__(self, applet):

        self.applet = applet
        self.config_file = os.path.expanduser(
            "~/.config/mate-cmd-chart-applet.json")

        # Initialize settings and other properties
        self.load_settings()
        self.log("CmdChartApplet initialized")  # Debug statement

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(self.chart_width, 50)
        self.drawing_area.connect("draw", self.on_draw)

        # Enable events on the applet itself
        self.applet.add_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

        # Connect hover events to applet
        self.applet.connect("enter-notify-event", self.on_applet_enter)
        self.applet.connect("leave-notify-event", self.on_applet_leave)

        self.applet.add(self.drawing_area)
        self.setup_menu()
        self.is_hovered = False
        self.applet.show_all()

        GLib.timeout_add(self.update_interval*1000, self.update_chart)
        self.update_chart()

    def log(self, text, force=False):
        if self.enable_log or force:
            print(text, flush=True)

    def on_applet_enter(self, widget, event):
        """Highlight applet on mouse enter"""
        # Change background color
        self.is_hovered = True
        self.drawing_area.queue_draw()
        return False

    def on_applet_leave(self, widget, event):
        """Remove highlight on mouse leave"""
        # Reset background
        self.is_hovered = False
        self.drawing_area.queue_draw()
        return False

    def on_draw(self, widget, cr):
        """Draw the chart based on parsed command output"""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        # Background with transparency
        cr.set_source_rgba(0, 0, 0, self.chart_area_transparency)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Add glow effect when hovering
        if self.is_hovered:
            # Create a subtle glow
            gradient = cairo.LinearGradient(0, 0, 0, height)
            gradient.add_color_stop_rgba(0, 1, 1, 1, 0.3)
            gradient.add_color_stop_rgba(0.5, 1, 1, 1, 0.1)
            gradient.add_color_stop_rgba(1, 1, 1, 1, 0.3)
            cr.set_source(gradient)
            cr.rectangle(0, 0, width, height)
            cr.fill()

        if not hasattr(self, 'parsed_data') or not self.parsed_data:
            return False

        # Calculate line height
        num_lines = len(self.parsed_data)
        line_height = height / num_lines if num_lines > 0 else height

        # Draw each line
        for line_idx, line_elements in enumerate(self.parsed_data):
            y_offset = line_idx * line_height
            x_offset = 3
            cr.set_source_rgba(128, 128, 128, 0.3)
            cr.set_line_width(1)
            cr.move_to(x_offset, y_offset)
            cr.line_to(width, y_offset)
            cr.stroke()

            # Draw each element in the line
            for item in line_elements:
                if item['type'] == 'CIRCLE':
                    # Draw circle indicator
                    radius = line_height / 3
                    color = self.parse_color(item['color'])
                    cr.set_source_rgb(*color)
                    cr.arc(x_offset + radius,
                           y_offset + line_height / 2,
                           radius - 2,
                           0,
                           2 * 3.14159)
                    cr.fill()
                    x_offset += radius * 2 + 3

                elif item['type'] == 'BAR':
                    # Draw bar
                    value = item['value']
                    min_val, max_val = item['range']
                    percentage = (value - min_val) / (max_val - min_val) \
                        if max_val > min_val else 0
                    bar_height = line_height * 0.8 * percentage

                    color = self.parse_color(item['colors'][0])
                    if len(item['colors']) > 1:
                        background = self.parse_color(item['colors'][1])
                    else:
                        background = (1.0 - color[0],
                                      1.0 - color[1],
                                      1.0 - color[2],
                                      0.2)
                    # Draw background
                    cr.set_source_rgba(*background)
                    cr.rectangle(x_offset,
                                 y_offset,
                                 self.bar_width, line_height)
                    cr.fill()

                    # Bar color
                    cr.set_source_rgb(*color)
                    cr.rectangle(x_offset,
                                 y_offset + line_height - bar_height,
                                 self.bar_width, bar_height)
                    cr.fill()

                    x_offset += self.bar_width + 3

                elif item['type'] == 'HBAR':
                    # Draw bar
                    value = item['value']
                    min_val, max_val = item['range']
                    percentage = (value - min_val) / (max_val - min_val) \
                        if max_val > min_val else 0
                    bar_widht = line_height * 0.8 * percentage

                    color = self.parse_color(item['colors'][0])
                    if len(item['colors']) > 1:
                        background = self.parse_color(item['colors'][1])
                    else:
                        background = (1.0 - color[0],
                                      1.0 - color[1],
                                      1.0 - color[2],
                                      0.2)
                    # Draw background
                    cr.set_source_rgba(*background)
                    cr.rectangle(x_offset,
                                 y_offset + bar_widht/2,
                                 line_height, self.bar_width)
                    cr.fill()

                    # Bar color
                    cr.set_source_rgb(*color)
                    cr.rectangle(x_offset,
                                 y_offset + bar_widht/2,
                                 bar_widht,
                                 self.bar_width)
                    cr.fill()

                    x_offset += line_height + 3

                elif item['type'] == 'TXT':
                    # Use custom color if provided, otherwise use default
                    text_color = item.get('color', None)
                    if text_color:
                        color = self.parse_color(text_color)
                    else:
                        color = self.parse_color(self.font_color)

                    # Shadow if enabled
                    if self.enable_font_shadow:
                        shadow_color = self.parse_color(self.font_shadow_color)
                        cr.set_source_rgb(*shadow_color)
                        cr.select_font_face(self.font_family,
                                            cairo.FONT_SLANT_NORMAL,
                                            cairo.FONT_WEIGHT_NORMAL)
                        cr.set_font_size(self.font_size)
                        cr.move_to(x_offset + 1,
                                   y_offset + line_height / 2 +
                                   self.font_size / 3 + 1)
                        cr.show_text(item['text'])

                    # Actual text
                    cr.set_source_rgb(*color)
                    cr.select_font_face(self.font_family,
                                        cairo.FONT_SLANT_NORMAL,
                                        cairo.FONT_WEIGHT_NORMAL)
                    cr.set_font_size(self.font_size)
                    cr.move_to(x_offset,
                               y_offset + line_height / 2 +
                               self.font_size / 3)
                    cr.show_text(item['text'])

                    # Update offset based on text width
                    extents = cr.text_extents(item['text'])
                    x_offset += extents.width + 5

        return False

    def parse_color(self, color_code):
        """Parse color code like 'g' or '#FFFFFF' or '#29c' to RGB tuple"""
        color_map = {
            'r': (1, 0, 0),    # red
            'g': (0, 1, 0),    # green
            'b': (0, 0, 1),    # blue
            'y': (1, 1, 0),    # yellow
            'k': (0, 0, 0),    # black
            'w': (1, 1, 1),    # white
            'c': (0, 1, 1),    # cyan
            'm': (1, 0, 1),    # magenta
            'o': (1, 0.7, 0),  # orange
        }

        if color_code in color_map:
            return color_map[color_code]
        elif color_code.startswith('#'):
            # Parse hex color
            color_code = color_code.lstrip('#')

            # Handle 3-character shorthand (#29c -> #2299cc)
            if len(color_code) == 3:
                color_code = ''.join([c*2 for c in color_code])

            # Parse 6-character hex
            if len(color_code) == 6:
                return tuple(
                    int(color_code[i:i+2], 16) / 255.0 for i in (0, 2, 4))

        return (1, 1, 1)  # default white

    def load_settings(self):
        """Load settings from config file or use defaults"""
        defaults = {
            'command': "echo '2L| TXTC:#29c loading.... ||"
                       " CR:g BAR:0-100=50:k:g TXT:Status is OK'",
            'update_interval': 60,
            'chart_width': 100,
            'bar_width': 8,
            'chart_area_transparency': 0.3,
            'font_family': 'Sans',
            'font_size': 10,
            'font_color': '#FFFFFF',
            'enable_font_shadow': True,
            'font_shadow_color': '#000000',
            'enable_log': False,
            'cmd_timeout': 10
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults (in case new settings were added)
                    defaults.update(settings)
        except Exception as e:
            self.log(f"Error loading settings: {e}", True)

        # Apply settings
        self.command = defaults['command']
        self.update_interval = defaults['update_interval']
        self.chart_width = defaults['chart_width']
        self.bar_width = defaults['bar_width']
        self.chart_area_transparency = defaults['chart_area_transparency']
        self.font_family = defaults['font_family']
        self.font_size = defaults['font_size']
        self.font_color = defaults['font_color']
        self.enable_font_shadow = defaults['enable_font_shadow']
        self.font_shadow_color = defaults['font_shadow_color']
        self.enable_log = defaults['enable_log']
        self.cmd_timeout = defaults['cmd_timeout']

    def save_settings(self):
        """Save settings to config file"""
        settings = {
            'command': self.command,
            'update_interval': self.update_interval,
            'chart_width': self.chart_width,
            'bar_width': self.bar_width,
            'chart_area_transparency': self.chart_area_transparency,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'enable_font_shadow': self.enable_font_shadow,
            'font_shadow_color': self.font_shadow_color,
            'enable_log': self.enable_log,
            'cmd_timeout': self.cmd_timeout
        }

        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
            self.log("Settings saved")
            self.update_chart()
        except Exception as e:
            self.log(f"Error saving settings: {e}", True)

    def setup_menu(self):
        """Setup the context menu for the applet"""
        # Create action group
        action_group = Gtk.ActionGroup(name="CmdChartApplet Actions")

        # Add preferences action
        action_group.add_actions([
            ("Preferences", Gtk.STOCK_PREFERENCES, "_Preferences",
             None, "Configure the applet", self.show_preferences),
            ("About", Gtk.STOCK_ABOUT, "_About",
             None, "About this applet", self.show_about)
        ])

        # Setup the menu
        self.applet.setup_menu(
            """
            <menuitem name="Preferences" action="Preferences" />
            <menuitem name="About" action="About" />
            """,
            action_group
        )

    def show_preferences(self, action):
        """Show the preferences dialog"""
        dialog = Gtk.Dialog(
            title="Cmd Chart Applet Preferences",
            parent=None,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(500, 400)

        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)

        # Create a grid for settings
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)

        row = 0

        # Command
        label = Gtk.Label(label="Command:", xalign=0)
        command_entry = Gtk.Entry()
        command_entry.set_text(self.command)
        command_entry.set_hexpand(True)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(command_entry, 1, row, 1, 1)
        row += 1

        # Update interval
        label = Gtk.Label(label="Update Interval (sec):", xalign=0)
        cmd_spin = Gtk.SpinButton()
        cmd_spin.set_range(1, 30000)
        cmd_spin.set_increments(1, 5)
        cmd_spin.set_value(self.cmd_timeout)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(cmd_spin, 1, row, 1, 1)
        row += 1

        # Update timeout
        label = Gtk.Label(label="Command timeout (sec):", xalign=0)
        interval_spin = Gtk.SpinButton()
        interval_spin.set_range(1, 30000)
        interval_spin.set_increments(1, 5)
        interval_spin.set_value(self.cmd_timeout)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(interval_spin, 1, row, 1, 1)
        row += 1

        # Chart width
        label = Gtk.Label(label="Chart Width:", xalign=0)
        width_spin = Gtk.SpinButton()
        width_spin.set_range(50, 1000)
        width_spin.set_increments(10, 50)
        width_spin.set_value(self.chart_width)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(width_spin, 1, row, 1, 1)
        row += 1

        # Bar width
        label = Gtk.Label(label="Bar Width:", xalign=0)
        bar_width_spin = Gtk.SpinButton()
        bar_width_spin.set_range(2, 50)
        bar_width_spin.set_increments(1, 5)
        bar_width_spin.set_value(self.bar_width)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(bar_width_spin, 1, row, 1, 1)
        row += 1

        # Transparency
        label = Gtk.Label(label="Background Transparency:", xalign=0)
        transparency_spin = Gtk.SpinButton()
        transparency_spin.set_range(0, 1)
        transparency_spin.set_increments(0.1, 0.1)
        transparency_spin.set_digits(1)
        transparency_spin.set_value(self.chart_area_transparency)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(transparency_spin, 1, row, 1, 1)
        row += 1

        # Font family
        label = Gtk.Label(label="Font Family:", xalign=0)
        font_entry = Gtk.Entry()
        font_entry.set_text(self.font_family)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(font_entry, 1, row, 1, 1)
        row += 1

        # Font size
        label = Gtk.Label(label="Font Size:", xalign=0)
        font_size_spin = Gtk.SpinButton()
        font_size_spin.set_range(6, 48)
        font_size_spin.set_increments(1, 2)
        font_size_spin.set_value(self.font_size)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(font_size_spin, 1, row, 1, 1)
        row += 1

        # Font color
        label = Gtk.Label(label="Font Color:", xalign=0)
        font_color_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse(self.font_color)
        font_color_button.set_rgba(rgba)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(font_color_button, 1, row, 1, 1)
        row += 1

        # Enable shadow
        label = Gtk.Label(label="Enable Font Shadow:", xalign=0)
        shadow_check = Gtk.CheckButton()
        shadow_check.set_active(self.enable_font_shadow)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(shadow_check, 1, row, 1, 1)
        row += 1

        # Shadow color
        label = Gtk.Label(label="Shadow Color:", xalign=0)
        shadow_color_button = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse(self.font_shadow_color)
        shadow_color_button.set_rgba(rgba)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(shadow_color_button, 1, row, 1, 1)
        row += 1

        # Enable logging
        label = Gtk.Label(label="Enable Logging:", xalign=0)
        shadow_check = Gtk.CheckButton()
        shadow_check.set_active(self.enable_log)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(shadow_check, 1, row, 1, 1)
        row += 1

        content.pack_start(grid, True, True, 0)
        dialog.show_all()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            # Save new settings
            self.command = command_entry.get_text()
            self.update_interval = int(interval_spin.get_value())
            self.cmd_timeout = int(cmd_spin.get_value())
            self.chart_width = int(width_spin.get_value())
            self.bar_width = int(bar_width_spin.get_value())
            self.chart_area_transparency = transparency_spin.get_value()
            self.font_family = font_entry.get_text()
            self.font_size = int(font_size_spin.get_value())

            # Get colors as hex
            rgba = font_color_button.get_rgba()
            self.font_color = "#{:02x}{:02x}{:02x}".format(
                int(rgba.red * 255),
                int(rgba.green * 255),
                int(rgba.blue * 255))

            self.enable_font_shadow = shadow_check.get_active()

            rgba = shadow_color_button.get_rgba()
            self.font_shadow_color = "#{:02x}{:02x}{:02x}".format(
                int(rgba.red * 255),
                int(rgba.green * 255),
                int(rgba.blue * 255))

            # Save to file
            self.save_settings()

            # Apply changes
            self.drawing_area.set_size_request(self.chart_width, 50)
            self.drawing_area.queue_draw()

            # Restart timer with new interval
            # (you may want to store the timer ID and remove the old one first)

        dialog.destroy()

    def show_about(self, action):
        """Show the about dialog"""
        about = Gtk.AboutDialog()
        about.set_program_name("Cmd Chart Applet")
        about.set_version("1.0")
        about.set_comments("Draw chart based on command output")
        about.set_website("https://github.com/yourusername/cmd-chart-applet")
        about.set_authors(["Your Name"])
        about.run()
        about.destroy()

    def update_chart(self):
        """Execute command, parse output, and trigger redraw"""
        self.log("Updating chart")

        try:
            # Execute the command
            output = self.execute_command()

            # Parse the output and store it
            self.parsed_data = self.parse_output(output)

            # Trigger a redraw of the drawing area
            if hasattr(self, 'drawing_area'):
                self.drawing_area.queue_draw()

        except Exception as e:
            self.log(f"Error updating chart: {e}", True)
            traceback.print_exc()
            sys.stdout.flush()

        return True  # Keep the timer running

    def execute_command(self):
        """Execute the configured command and return output"""
        self.log("Executing command...")

        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.cmd_timeout
            )
            output = result.stdout.strip()
            self.log(f"Command output: {output}")
            return output
        except subprocess.TimeoutExpired:
            self.log("Command timeout", True)
            return ""
        except Exception as e:
            self.log(f"Command error: {e}", True)
            return ""

    def parse_output(self, output):
        """Parse command output into structured data

        Format examples:
        Single line: CR:g BAR:0-100=50:k:g TXT:Status is OK
        Two lines: 2L| TXTC:#29c test || CR:g BAR:0-100=50:k:g TXT:Status OK

        Returns: List of lists, where each inner list represents a line
        """
        self.log("Parsing output...")

        if not output:
            return []

        # Check for line count directive (e.g., "2L|")
        # num_lines = 1
        if output.startswith(('1L|', '2L|', '3L|', '4L|')):
            # num_lines = int(output[0])
            output = output[3:]  # Remove "NL|" prefix

        # Split by || to get individual lines
        lines = output.split('||')
        parsed_lines = []

        for line in lines:
            line = line.strip()
            parsed_elements = []

            if not line:
                # Empty line - add empty list
                parsed_lines.append([])
                continue

            # parts = re.split(r'(?:[^\\])\|', line)
            parts = re.split(r'(?:[^\\])\| *', line)
            self.log(f"PARTS: {parts}")
            i = 0
            while i < len(parts):
                part = parts[i]

                if part.startswith('CR:'):
                    # Circle/color indicator
                    color = part.split(':')[1]
                    parsed_elements.append({'type': 'CIRCLE', 'color': color})

                elif part.startswith('BAR:') or part.startswith('HBAR:'):
                    # Bar chart: BAR:0-100=50:k:g
                    info = part.split(':')
                    bar_info = info[1]
                    range_part, val_part = bar_info.split('=')
                    min_val, max_val = map(int, range_part.split('-'))

                    value = float(val_part)
                    colors = info[2:] \
                        if len(info) > 2 else ['g']

                    type_str = 'HBAR' if part[0] == 'H' else 'BAR'
                    parsed_elements.append({
                        'type': type_str,
                        'range': (min_val, max_val),
                        'value': value,
                        'colors': colors,
                    })

                elif part.startswith('TXTC:'):
                    # Text with custom color: TXTC:#29c loading....
                    # Format: TXTC:color rest of text
                    color_and_text = part.split(':', 1)[1]
                    # Split on first space to get color
                    parts_of_text = color_and_text.split(' ', 1)
                    color = parts_of_text[0]
                    text_part = parts_of_text[1].replace('\\|', '|')

                    parsed_elements.append({
                        'type': 'TXT',
                        'text': text_part,
                        'color': color
                    })

                elif part.startswith('TXT:'):
                    # Text: collect until next command or end
                    text_part = part.split(':', 1)[1].replace('\\|', '|')

                    parsed_elements.append({
                        'type': 'TXT',
                        'text': text_part,
                        'color': None  # Will use default font_color
                    })

                i += 1

            if parsed_elements:
                parsed_lines.append(parsed_elements)

        self.log(f"Parsed data: {parsed_lines}")
        return parsed_lines


def applet_factory(applet, iid, data):
    if iid != "CmdChartApplet":
        return False

    CmdChartApplet(applet)
    return True


def main():
    # Handle SIGINT and SIGTERM gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

    try:
        MatePanelApplet.Applet.factory_main(
            "CmdChartAppletFactory",
            # ^^ factory_id (must match .mate-panel-applet)
            True,
            MatePanelApplet.Applet.__gtype__,  # applet_type
            applet_factory,                    # callback function
            None                               # user_data
        )
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
