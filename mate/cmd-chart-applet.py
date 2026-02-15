#!/usr/bin/env python3

import subprocess
import traceback
import sys
import signal
import re
import os
import math
# import json
# import os

import gi
import cairo
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('MatePanelApplet', '4.0')
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, Gdk, MatePanelApplet  # pyright: ignore[reportAttributeAccessIssue] # noqa: E402,E501
from gi.repository import GLib   # pyright: ignore[reportAttributeAccessIssue] # noqa: E402,E501
from gi.repository import Gio    # pyright: ignore[reportAttributeAccessIssue] # noqa: E402,E501
from gi.repository import Pango  # pyright: ignore[reportAttributeAccessIssue] # noqa: E402,E501


SCHEMA_ID = "org.mate.panel.applet.CmdChartApplet"


class CmdChartApplet():
    def __init__(self, applet):

        self.verbose = True
        self.applet = applet
        self.config_path = applet.get_preferences_path()
        self.applet.settings = Gio.Settings.new_with_path(
            SCHEMA_ID, self.config_path)
        # self.log(f"!!! config_file: {self.config_file}")

        # Initialize settings and other properties
        self.load_settings()
        self.log("CmdChartApplet initialized", True)
        self.verbose = self.settings.get_boolean("verbose")

        self.drawing_area = Gtk.DrawingArea()
        panel_height = self.applet.get_size()
        self.drawing_area.set_size_request(
                self.settings.get_int("chart-width"),
                panel_height)

        self.applet.connect("change-size", self.on_size_changed)

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

        # History for graph feature
        self.do_draw_graph = False
        self.history = []
        self.historyFilePath =  os.path.expanduser(
            "~/.local/share/mate-applets/cmd-applet/history.txt")
        self.graphColor = "g"  # default graph color
        self.graph_min = None
        self.graph_max = None

        # Ensure history directory exists
        history_dir = GLib.path_get_dirname(self.historyFilePath)
        if not GLib.file_test(history_dir, GLib.FileTest.EXISTS):
            GLib.mkdir_with_parents(history_dir, 0o755)

        # Load history from file if it exists
        if GLib.file_test(self.historyFilePath, GLib.FileTest.EXISTS):
            try:
                contents = GLib.file_get_contents(self.historyFilePath)[1]
                lines = contents.decode().split('\n')
                for line in lines:
                    try:
                        val = float(line)
                        if not math.isnan(val):
                            self.history.append(val)
                    except Exception:
                        continue
                # Keep only last history-len entries
                if len(self.history) > self.settings.get_int("history-len"):
                    self.history = self.history[-self.settings.get_int("history-len"):]
            except Exception as e:
                self.log(f"Error loading history: {e}", True)

        self.timer_id = None
        self.settings.connect("changed::verbose", lambda s, k: setattr(self, 'verbose', s.get_boolean(k)))
        self.settings.connect("changed::update-interval", self.on_interval_changed)
        self.timer_id = GLib.timeout_add(self.settings.get_int("update-interval")*1000, self.update_chart)
        # set timer
        self.on_interval_changed(self.settings, "update-interval")
        # Redraw whenever any visual key changes
        visual_keys = ["chart-width", "chart-area-transparency", "bar-width", "graph-transparency"]
        for key in visual_keys:
            self.settings.connect(f"changed::{key}", lambda s, k: self.drawing_area.queue_draw())

        self.update_chart()

    def on_size_changed(self, applet, size):
        """Update the drawing area size when the panel is resized or moved."""
        self.drawing_area.set_size_request(
                self.settings.get_int("chart-width"),
                size)
        self.drawing_area.queue_draw()

    def on_interval_changed(self, settings, key):
        # Remove old timer and start a new one with the updated value
        if hasattr(self, 'timer_id') and self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

        new_interval = settings.get_int(key) * 1000
        self.timer_id = GLib.timeout_add(new_interval, self.update_chart)

    def log(self, text, force=False):
        if force or self.verbose:
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

    def draw_overflow(self, widget, cr, x, y):
        ff = self.settings.get_string("font-family")
        if ff is None:
            ff = "Sans"
            self.settings.set_string("font-family", ff)
        fs = self.settings.get_int("font-size")
        if fs is None:
            self.log("Oops! fs is None!", True)
            fs = 12
            self.settings.set_int("font-size", fs)
        self.log(f"overflow: '{ff}' / '{fs}'")
        cr.select_font_face(
            ff,
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(fs)
        cr.move_to(x + 1,
                   y + fs / 3 + 1)
        cr.show_text(">>")

    def on_draw(self, widget, cr):
        """Draw the chart based on parsed command output"""
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height

        # Background with transparency
        transparency = self.settings.get_double("chart-area-transparency")
        cr.set_source_rgba(0, 0, 0, transparency)
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

        # Draw graph first (background)
        self.draw_graph(cr, width, height)

        if not hasattr(self, 'parsed_data') or not self.parsed_data:
            return False

        # Calculate line height
        num_lines = len(self.parsed_data)
        line_height = height / num_lines if num_lines > 0 else height
        line_width = width  # self.applet.settings.get_int("chart-width")

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
                    # Check width
                    if x_offset + radius * 2 + 3 > line_width:
                        self.draw_overflow(
                            widget,
                            cr,
                            x_offset,
                            y_offset + line_height / 2)
                        break
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
                    # Check width
                    if (
                        x_offset + self.applet.settings.get_int("bar-width") >
                        width  # self.applet.settings.get_int("chart-width")
                    ):
                        self.draw_overflow(
                            widget,
                            cr,
                            x_offset,
                            y_offset + line_height / 2)
                        break
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
                                 self.settings.get_int("bar-width"),
                                 line_height)
                    cr.fill()

                    # Bar color
                    cr.set_source_rgb(*color)
                    cr.rectangle(x_offset,
                                 y_offset + line_height - bar_height,
                                 self.settings.get_int("bar-width"),
                                 bar_height)
                    cr.fill()

                    x_offset += self.settings.get_int("bar-width") + 3

                elif item['type'] == 'HBAR':
                    # Check width
                    if (
                        x_offset + line_height >
                        width  # self.applet.settings.get_int("chart-width")
                    ):
                        self.draw_overflow(
                            widget,
                            cr,
                            x_offset,
                            y_offset + line_height / 2)
                        break
                    # Draw bar
                    value = item['value']
                    min_val, max_val = item['range']
                    percentage = (value - min_val) / (max_val - min_val) \
                        if max_val > min_val else 0
                    bar_width = line_height * 0.8 * percentage

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
                                 y_offset + bar_width/2,
                                 line_height,
                                 self.settings.get_int("bar-width"))
                    cr.fill()

                    # Bar color
                    cr.set_source_rgb(*color)
                    cr.rectangle(x_offset,
                                 y_offset + bar_width/2,
                                 bar_width,
                                 self.settings.get_int("bar-width"))
                    cr.fill()

                    x_offset += line_height + 3

                elif item['type'] == 'TXT':
                    # Use custom color if provided, otherwise use default
                    text_color = item.get('color', None)
                    if text_color:
                        color = self.parse_color(text_color)
                    else:
                        color = self.parse_color(
                            self.settings.get_string("font-color"))

                    font_family = self.settings.get_string("font-family")
                    if font_family is None:
                        font_family = "Sans"
                        self.settings.set_string("font-family", font_family)
                    font_size = self.settings.get_int("font-size")
                    if font_size is None:
                        self.log("Oops! font_size is None...", True)
                        font_size = 12
                        self.settings.set_int("font-size", font_size)
                    cr.select_font_face(
                        font_family,
                        cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_NORMAL)
                    cr.set_font_size(font_size)
                    extents = cr.text_extents(item['text'])
                    # Check width
                    if (
                        x_offset + extents.width >
                        width  # self.applet.settings.get_int("chart-width")
                    ):
                        self.draw_overflow(
                            widget,
                            cr,
                            x_offset,
                            y_offset + line_height / 2)
                        break

                    # Shadow if enabled
                    if self.settings.get_boolean("enable-font-shadow"):
                        shadow_color = self.parse_color(
                            self.settings.get_string("font-shadow-color"))
                        cr.set_source_rgb(*shadow_color)
                        cr.move_to(x_offset + 1,
                                   y_offset + line_height / 2 +
                                   font_size / 3 + 1)
                        cr.show_text(item['text'])

                    # Actual text
                    cr.set_source_rgb(*color)
                    cr.move_to(x_offset,
                               y_offset + line_height / 2 +
                               self.settings.get_int("font-size") / 3)
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
        try:
            self.settings = Gio.Settings.new_with_path(
                "org.mate.panel.applet.CmdChartApplet",
                self.config_path)
        except Exception as e:
            self.log(f"Error loading settings: {e}", True)

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
        dialog = Gtk.Dialog(
            title="Cmd Chart Applet Preferences",
            transient_for=None,
            flags=0
        )
        dialog.set_default_size(400, -1)
        dialog.add_buttons(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        
        notebook = Gtk.Notebook()
        notebook.set_border_width(10)
        dialog.get_content_area().add(notebook)

        # --- Tab 1: General (Command & Timing) ---
        grid_gen = Gtk.Grid(column_spacing=12, row_spacing=12, margin=12)
        notebook.append_page(grid_gen, Gtk.Label(label="General"))

        # Command
        entry_cmd = Gtk.Entry()
        self.settings.bind("command", entry_cmd, "text", Gio.SettingsBindFlags.DEFAULT)
        grid_gen.attach(Gtk.Label(label="Command:", xalign=0), 0, 0, 1, 1)
        grid_gen.attach(entry_cmd, 1, 0, 1, 1)

        # Intervals
        spin_update = Gtk.SpinButton.new_with_range(1, 3600, 1)
        self.settings.bind("update-interval", spin_update, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_gen.attach(Gtk.Label(label="Update Interval (s):", xalign=0), 0, 1, 1, 1)
        grid_gen.attach(spin_update, 1, 1, 1, 1)

        spin_timeout = Gtk.SpinButton.new_with_range(1, 60, 1)
        self.settings.bind("cmd-timeout", spin_timeout, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_gen.attach(Gtk.Label(label="Timeout (s):", xalign=0), 0, 2, 1, 1)
        grid_gen.attach(spin_timeout, 1, 2, 1, 1)

        spin_history = Gtk.SpinButton.new_with_range(1, 256, 1)
        self.settings.bind("history-len", spin_history, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_gen.attach(Gtk.Label(label="History points:", xalign=0), 0, 3, 1, 1)
        grid_gen.attach(spin_history, 1, 3, 1, 1)

        verbose = Gtk.CheckButton(label="Verbose logging")
        self.settings.bind("verbose", verbose, "active", Gio.SettingsBindFlags.DEFAULT)
        grid_gen.attach(verbose, 1, 3, 1, 1)

        # --- Tab 2: Appearance ---
        grid_app = Gtk.Grid(column_spacing=12, row_spacing=12, margin=12)
        notebook.append_page(grid_app, Gtk.Label(label="Appearance"))

        # Widths
        spin_width = Gtk.SpinButton.new_with_range(50, 2000, 10)
        self.settings.bind("chart-width", spin_width, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_app.attach(Gtk.Label(label="Applet Width:", xalign=0), 0, 0, 1, 1)
        grid_app.attach(spin_width, 1, 0, 1, 1)

        spin_bar = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.settings.bind("bar-width", spin_bar, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_app.attach(Gtk.Label(label="Bar Width:", xalign=0), 0, 1, 1, 1)
        grid_app.attach(spin_bar, 1, 1, 1, 1)

        # Transparencies
        adj_bg = Gtk.Adjustment(value=0.2, lower=0, upper=1, step_increment=0.05, page_increment=0.1)
        scale_bg = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj_bg)
        self.settings.bind("chart-area-transparency", adj_bg, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_app.attach(Gtk.Label(label="BG Transparency:", xalign=0), 0, 2, 1, 1)
        grid_app.attach(scale_bg, 1, 2, 1, 1)

        adj_graph = Gtk.Adjustment(value=0.3, lower=0, upper=1, step_increment=0.05, page_increment=0.1)
        scale_graph = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj_graph)
        self.settings.bind("graph-transparency", adj_graph, "value", Gio.SettingsBindFlags.DEFAULT)
        grid_app.attach(Gtk.Label(label="Graph Transparency:", xalign=0), 0, 3, 1, 1)
        grid_app.attach(scale_graph, 1, 3, 1, 1)

        # --- Tab 3: Font & Text ---
        grid_font = Gtk.Grid(column_spacing=12, row_spacing=12, margin=12)
        notebook.append_page(grid_font, Gtk.Label(label="Text"))

        # Font Selection (Combined Size/Family)
        font_btn = Gtk.FontButton()
        # Set initial value from current settings
        current_font = f"{self.settings.get_string('font-family')} {self.settings.get_int('font-size')}"
        font_btn.set_font(current_font)
        def on_font_set(button):
            font_desc = button.get_font_desc()
            family = font_desc.get_family()
            # Pango units to points conversion
            size = font_desc.get_size() / Pango.SCALE

            self.settings.set_string("font-family", family)
            self.settings.set_int("font-size", int(size))

        font_btn.connect("font-set", on_font_set)
        grid_font.attach(Gtk.Label(label="Font:", xalign=0), 0, 0, 1, 1)
        grid_font.attach(font_btn, 1, 0, 1, 1)

        # Shadow
        check_shadow = Gtk.CheckButton(label="Enable Shadow")
        self.settings.bind("enable-font-shadow", check_shadow, "active", Gio.SettingsBindFlags.DEFAULT)
        grid_font.attach(check_shadow, 1, 1, 1, 1)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def show_about(self, action):
        """Show the about dialog"""
        about = Gtk.AboutDialog()
        about.set_program_name("Cmd Chart Applet")
        about.set_version("1.0")
        about.set_comments("Draw chart based on command output")
        about.set_website("https://github.com/yourusername/cmd-chart-applet")
        about.set_authors(["Sergey Zhumatiy <sergzhum@gmail.com>"])
        about.run()
        about.destroy()

    def update_chart(self):
        """Execute command, parse output, and trigger redraw"""
        self.log("Updating chart")

        try:
            # Execute the command
            output = self.execute_command()

            # Set the raw command output as a tooltip so you can see the full text on hover
            if output:
                # You can format it with a header if you like
                self.applet.set_tooltip_text(f"Out:\n{output}")
            else:
                self.applet.set_tooltip_text("No command output")

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
                self.settings.get_string("command"),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.settings.get_int("cmd-timeout")
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
        Two lines: TXTC:#29c test || CR:g BAR:0-100=50:k:g TXT:Status OK

        Returns: List of lists, where each inner list represents a line
        """
        self.log("Parsing output...")

        if not output:
            return []

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
                    try:
                        color = part.split(':')[1]
                        parsed_elements.append(
                            {'type': 'CIRCLE', 'color': color}
                            )
                    except Exception:
                        self.log(f"Failed to parse {part}", True)

                elif part.startswith('BAR:') or part.startswith('HBAR:'):
                    # Bar chart: BAR:0-100=50:k:g
                    try:
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
                    except Exception:
                        self.log(f"Failed to parse {part}", True)

                elif part.startswith('TXTC:'):
                    # Text with custom color: TXTC:#29c loading...
                    # Format: TXTC:color rest of text
                    try:
                        [_, color, text] = part.split(':', 3)

                        # text = text.replace('\\|', '|')
                    except Exception:
                        self.log(f"Failed to parse {part}", True)
                        color = "#eee"
                        text = "Parse error"

                    parsed_elements.append({
                        'type': 'TXT',
                        'text': text,
                        'color': color
                    })

                elif part.startswith('TXT:'):
                    try:
                        # Text: collect until next command or end
                        text = part.split(':', 1)[1].replace('\\|', '|')
                    except Exception:
                        self.log(f"Failed to parse {part}", True)
                        text = "Parse error"
                    parsed_elements.append({
                        'type': 'TXT',
                        'text': text,
                        'color': None  # Will use default font_color
                    })

                elif part.startswith('GR:'):
                    # Graph value token
                    try:
                        rest = part[3:]
                        values = rest.split(':')
                        color, value_str = values[0:2]
                        value = float(value_str)
                        if len(values) == 4:
                            self.graph_min = float(values[2])
                            self.graph_max = float(values[3])
                        # Update history
                        self.history.append(value)
                        if len(self.history) > self.settings.get_int("history-len"):
                            self.history.pop(0)
                        # Persist history
                        with open(self.historyFilePath, "a+") as f:
                            f.write(f"{value_str}\n")
                        self.graph_color = color
                        self.do_draw_graph = True
                    except Exception as e:
                        import traceback
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        tb_info = traceback.extract_tb(exc_traceback)[-1]
                        lineno = tb_info[1]
                        filename = tb_info[0]
                        self.log(f"Failed to parse GR token: {e} at {lineno}/{filename}", True)

                i += 1

            if parsed_elements:
                parsed_lines.append(parsed_elements)

        self.log(f"Parsed data: {parsed_lines}")
        return parsed_lines

    def draw_graph(self, cr, width, height):
        """Draw the historical graph in the background."""
        if not self.do_draw_graph or not self.history or len(self.history) < 2:
            return

        color = self.parse_color(self.graph_color or "g")
        alpha = self.settings.get_double("graph-transparency")
        cr.set_line_width(2)
        boundary = 2
        draw_h = height - (boundary*2)

        step = width / (len(self.history) - 1)
        min_val = self.graph_min if self.graph_min is not None else min(self.history)
        max_val = self.graph_max if self.graph_max is not None else max(self.history)
        range_val = max_val - min_val or 1

        points = []
        for i, val in enumerate(self.history):
            x = i * step
            # Scales 0-100% to the current height
            y = (height - boundary) - ((val - min_val) / range_val) * draw_h
            points.append((x, y))

        # Draw the filled area
        cr.set_source_rgba(*color, alpha/2)
        cr.move_to(points[0][0], points[0][1])
        for x, y in points[1:]:
            cr.line_to(x, y)
        cr.line_to(width, height) # Down to bottom-right
        cr.line_to(0, height)     # Across to bottom-left
        cr.close_path()
        cr.fill()

        # Draw the top border line
        cr.set_source_rgba(*color, alpha)
        cr.set_line_width(2)
        cr.move_to(points[0][0], points[0][1])
        for x, y in points[1:]:
            cr.line_to(x, y)
        cr.stroke()

    def on_applet_removed_from_panel(self):
        self.log("CmdChartApplet: Applet removed from panel")
        # No explicit cleanup needed here


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


def applet_factory(applet, iid, data):
    if iid != "CmdChartApplet":
        return False

    CmdChartApplet(applet)
    return True


if __name__ == "__main__":
    main()
