/* eslint-disable no-undef */
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const St = imports.gi.St;
const GLib = imports.gi.GLib;
const Util = imports.misc.util;
const Lang = imports.lang;
const Settings = imports.ui.settings;
const Mainloop = imports.mainloop;
const Cairo = imports.cairo;

function CmdChartApplet(orientation, panel_height, instance_id, metadata) {
    this._init(orientation, panel_height, instance_id, metadata);
}

CmdChartApplet.prototype = {
    __proto__: Applet.Applet.prototype,

    _init: function(orientation, panel_height, instance_id, metadata) {
        Applet.Applet.prototype._init.call(this, orientation, panel_height, instance_id, metadata);

        try {
            this.panel_height = panel_height;
            this.uuid = metadata.uuid;
            this.instance_id = instance_id;

            this.set_applet_tooltip(_("CMD Chart Applet"));

            this.settings = new Settings.AppletSettings(this, this.uuid, instance_id);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "command", "command", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "update-interval", "updateInterval", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "chart-width", "chartWidth", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "bar-width", "barWidth", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "chart-area-transparency", "chartAreaTransparency", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "font-family", "fontFamily", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "font-size", "fontSize", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "font-color", "fontColor", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "enable-font-shadow", "enableFontShadow", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "font-shadow-color", "fontShadowColor", this.on_settings_changed, null);
            this.settings.bindProperty(Settings.BindingDirection.BIDIRECTIONAL,
                                     "verbose-logging", "verboseLogging", this.on_settings_changed, null);

            this.chartElements = [];
            this.lastOutput = "";

            // History for graph feature
            this.history = [];
            this.historyFilePath = GLib.get_user_data_dir() + "/cmd-chart-applet/history.txt";
            this.graphColor = "g"; // default graph color

            // Ensure history directory exists
            let historyDir = GLib.path_get_dirname(this.historyFilePath);
            if (!GLib.file_test(historyDir, GLib.FileTest.EXISTS)) {
                GLib.mkdir_with_parents(historyDir, 0o755);
            }

            // Load history from file if it exists
            let [success, contents] = GLib.file_get_contents(this.historyFilePath);
            if (success) {
                let lines = contents.toString().split('\n');
                for (let line of lines) {
                    let val = parseFloat(line);
                    if (!isNaN(val)) {
                        this.history.push(val);
                    }
                }
                // Keep only last 128 entries
                if (this.history.length > 128) {
                    this.history = this.history.slice(this.history.length - 128);
                }
            }

            global.log("CMD Chart Applet: Starting applet (instance " + instance_id + ")");

            this.panelChartActor = new St.DrawingArea({
                width: this.chartWidth || 200,
                height: this.panel_height
            });
            this.panelChartActor.connect('repaint', Lang.bind(this, this.drawPanelChart));
            this.actor.add_child(this.panelChartActor);

            this.menuManager = new PopupMenu.PopupMenuManager(this);
            this.menu = new Applet.AppletPopupMenu(this, orientation);
            this.menuManager.addMenu(this.menu);

            this._contentSection = new PopupMenu.PopupMenuSection();
            this.menu.addMenuItem(this._contentSection);

            let prefsItem = new PopupMenu.PopupMenuItem(_("Preferences"));
            prefsItem.connect('activate', Lang.bind(this, this.openPreferences));
            this.menu.addMenuItem(prefsItem);

            this.executeCommand();
            this.setupTimer();

        } catch (e) {
            global.logError(e);
        }
    },

    setupTimer: function() {
        if (this.timeout) {
            Mainloop.source_remove(this.timeout);
        }
        let intervalSeconds = this.updateInterval || 60;
        this.timeout = Mainloop.timeout_add_seconds(intervalSeconds, Lang.bind(this, this.executeCommand));
    },

    on_applet_clicked: function() {
        this.menu.toggle();
    },

    on_settings_changed: function() {
        global.log("CMD Chart Applet: Settings changed");
        this.setupTimer();
        this.rebuildPanelChart();
        this.executeCommand();
    },

    rebuildPanelChart: function() {
        if (this.panelChartActor) {
            this.actor.remove_child(this.panelChartActor);
            this.panelChartActor = null;
        }

        this.panelChartActor = new St.DrawingArea({
            width: this.chartWidth || 200,
            height: this.panel_height
        });
        this.panelChartActor.connect('repaint', Lang.bind(this, this.drawPanelChart));
        this.actor.add_child(this.panelChartActor);
    },

    parseColor: function(colorCode) {
        let colors = {
            'r': { r: 1.0, g: 0.0, b: 0.0, a: 1.0 },
            'o': { r: 1.0, g: 0.5, b: 0.0, a: 1.0 },
            'y': { r: 1.0, g: 1.0, b: 0.0, a: 1.0 },
            'g': { r: 0.0, g: 0.8, b: 0.0, a: 1.0 },
            'b': { r: 0.0, g: 0.0, b: 1.0, a: 1.0 },
            'v': { r: 0.5, g: 0.0, b: 1.0, a: 1.0 },
            'p': { r: 1.0, g: 0.0, b: 0.5, a: 1.0 },
            'w': { r: 1.0, g: 1.0, b: 1.0, a: 1.0 },
            'k': { r: 0.0, g: 0.0, b: 0.0, a: 1.0 }
        };

        if (colorCode in colors) {
            return colors[colorCode];
        }

        if (colorCode.startsWith('#')) {
            let hex = colorCode.substring(1);
            if (hex.length === 3) {
                let r = parseInt(hex[0] + hex[0], 16) / 255;
                let g = parseInt(hex[1] + hex[1], 16) / 255;
                let b = parseInt(hex[2] + hex[2], 16) / 255;
                return { r: r, g: g, b: b, a: 1.0 };
            } else if (hex.length === 6) {
                let r = parseInt(hex.substring(0, 2), 16) / 255;
                let g = parseInt(hex.substring(2, 4), 16) / 255;
                let b = parseInt(hex.substring(4, 6), 16) / 255;
                return { r: r, g: g, b: b, a: 1.0 };
            }
        }

        return { r: 1.0, g: 1.0, b: 1.0, a: 1.0 };
    },

    parseRGBAColor: function(colorString) {
        let match = colorString.match(/rgba?\(([^)]+)\)/);
        if (match) {
            let values = match[1].split(',').map(v => parseFloat(v.trim()));
            if (values.length >= 3) {
                return {
                    r: values[0] / 255,
                    g: values[1] / 255,
                    b: values[2] / 255,
                    a: values.length > 3 ? values[3] : 1.0
                };
            }
        }
        return { r: 1.0, g: 1.0, b: 1.0, a: 1.0 };
    },

    parseCommandOutput: function(output) {
        let usePipeSeparator = output.includes('|');
        let lines = output.split('||');
        return lines.map(l => this.parseElementLine(l, usePipeSeparator));
    },

    parseElementLine: function(output, usePipeSeparator) {
        let elements = [];
        if (usePipeSeparator === undefined) {
            usePipeSeparator = output.includes('|');
        }
        let separator = usePipeSeparator ? '|' : /\s+/;
        let tokens = output.trim().split(separator);

        for (let token of tokens) {
            token = token.trim();
            if (!token) continue;

            if (token.startsWith('CR:')) {
                let color = token.substring(3);
                if (color) {
                    elements.push({ type: 'circle', color: color });
                }
            } else if (token.startsWith('BAR:')) {
                let parts = token.substring(4).split(':');
                if (parts.length >= 3) {
                    let rangeValue = parts[0].split('=');
                    if (rangeValue.length === 2) {
                        let minMax = rangeValue[0].split('-');
                        if (minMax.length === 2) {
                            elements.push({
                                type: 'bar',
                                min: parseFloat(minMax[0]),
                                max: parseFloat(minMax[1]),
                                value: parseFloat(rangeValue[1]),
                                bgColor: parts[1],
                                fgColor: parts[2]
                            });
                        }
                    }
                }
            } else if (token.startsWith('HBAR:')) {
                let parts = token.substring(5).split(':');
                if (parts.length >= 3) {
                    let rangeValue = parts[0].split('=');
                    if (rangeValue.length === 2) {
                        let minMax = rangeValue[0].split('-');
                        if (minMax.length === 2) {
                            elements.push({
                                type: 'hbar',
                                min: parseFloat(minMax[0]),
                                max: parseFloat(minMax[1]),
                                value: parseFloat(rangeValue[1]),
                                bgColor: parts[1],
                                fgColor: parts[2]
                            });
                        }
                    }
                }
            } else if (token.startsWith('TXTC:')) {
                let rest = token.substring(5);
                let color, text;
                let textStartIndex;
                if (rest.startsWith('#')) {
                    let hexMatch = rest.match(/^(#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{6})/);
                    if (hexMatch) {
                        color = hexMatch[1];
                        textStartIndex = color.length;
                    } else {
                        continue;
                    }
                } else {
                    color = rest.charAt(0);
                    textStartIndex = 1;
                }
                if (textStartIndex < rest.length) {
                    let separator = rest.charAt(textStartIndex);
                    if (separator === ':' || separator === ' ') {
                        textStartIndex++;
                    }
                }
                text = rest.substring(textStartIndex);
                if (text) {
                    elements.push({ type: 'text', text: text, color: color });
                }
            } else if (token.startsWith('TXT:')) {
                let text = token.substring(4);
                if (text) {
                    elements.push({ type: 'text', text: text, color: null });
                }
            } else if (token.startsWith('GR:')) {
                let rest = token.substring(3);
                let parts = rest.split(':');
                if (parts.length >= 2) {
                    let color = parts[0];
                    let value = parseInt(parts[1], 10);
                    if (!isNaN(value)) {
                        this.history.push(value);
                        if (this.history.length > 128) {
                            this.history.shift();
                        }
                        let historyText = this.history.join('\n');
                        GLib.file_set_contents(this.historyFilePath, historyText);
                        this.graphColor = color;
                    }
                }
            }
        }

        return elements;
    },

    executeCommand: function() {
        try {
            let cmd = this.command || 'echo "CR:g"';

            if (this.verboseLogging) {
                global.log("CMD Chart Applet: Executing command: " + cmd);
            }

            let [success, stdout, stderr] = GLib.spawn_command_line_sync(cmd);
            if (stderr != "") {
                global.log("CMD Chart Applet: command '" + cmd + "' error: '" + stderr + "'");
            }

            if (success && stdout) {
                this.lastOutput = stdout.toString().trim();
                this.chartElements = this.parseCommandOutput(this.lastOutput);

                if (this.verboseLogging) {
                    global.log("CMD Chart Applet: Command output: " + this.lastOutput);
                    global.log("CMD Chart Applet: parsed " +
                        this.chartElements.length +
                        " elements: " +
                        this.chartElements.map(e => JSON.stringify(e)));
                }

                if (this.panelChartActor) {
                    if (this.verboseLogging) {
                        global.log("CMD Chart Applet: Requesting repaint");
                    }
                    this.panelChartActor.queue_repaint();
                }
            }

        } catch (e) {
            global.logError("CMD Chart Applet: Error executing command: " + e);
            this.set_applet_tooltip("Error executing command");
            this.chartElements = [];
            if (this.panelChartActor) {
                this.panelChartActor.queue_repaint();
            }
        }

        this.set_applet_tooltip(_("CMD: " + this.lastOutput));
        return true;
    },

    drawPanelChart: function(area) {
        let cr = area.get_context();
        let [width, height] = area.get_surface_size();

        let backgroundTransparency = this.chartAreaTransparency !== undefined ? this.chartAreaTransparency : 0.3;
        cr.setSourceRGBA(0.0, 0.0, 0.0, backgroundTransparency);
        cr.rectangle(0, 0, width, height);
        cr.fill();

        // Draw graph first (background)
        this.drawGraph(cr, width, height);

        if (!this.chartElements || this.chartElements.length === 0) {
            if (this.verboseLogging) {
                global.log("CMD Chart Applet: No elements to draw");
            }
            return;
        }

        let num_lines = this.chartElements.length;
        if (this.verboseLogging) {
            global.log("CMD Chart Applet: draw lines: " + num_lines);
        }

        let spacing = 4;
        let currentX = spacing;
        let drawnElements = 0;
        let overflowIndicatorWidth = 20;
        let hasOverflow = false;
        let lineHeight = height / num_lines;

        for (let l = 0; l < num_lines; l++) {
            let y_offset = l * lineHeight;
            let line = this.chartElements[l];
            currentX = spacing;
            global.log("CMD Chart Applet: line "+ l + ": " + JSON.stringify(line));
            for (let i = 0; i < line.length; i++) {
                let element = line[i];
                global.log("CMD Chart Applet: line " + l + " element "+ i + ": " + JSON.stringify(element));
                if (element.type === 'circle') {
                    let radius = Math.min(lineHeight / 2 - 2, 10);
                    let centerX = currentX + radius;
                    let centerY = y_offset + lineHeight / 2;

                    if (centerX + radius + overflowIndicatorWidth > width) {
                        if (this.verboseLogging) {
                            global.log("CMD Chart Applet: Out of space for circle at element " + i + "/" + this.chartElements.length);
                        }
                        hasOverflow = true;
                        break;
                    }

                    let color = this.parseColor(element.color);
                    cr.setSourceRGBA(color.r, color.g, color.b, 0.5);
                    cr.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                    cr.fill();

                    currentX = centerX + radius + spacing;
                    drawnElements++;

                } else if (element.type === 'bar' || element.type === 'hbar') {
                    let elWidth = this.barWidth || 16;
                    let barHeight = lineHeight - 2;
                    let barX = currentX;
                    let barY = y_offset + 2;

                    if (element.type[0] === 'h') {
                        elWidth = lineHeight;
                        barHeight = Math.min(this.barWidth, lineHeight - 2);
                    }
                    if (barX + elWidth + overflowIndicatorWidth > width) {
                        if (this.verboseLogging) {
                            global.log(
                                "CMD Chart Applet: Out of space for bar line " + l + 
                                "element " + i + "/" + this.chartElements.length);
                        }
                        hasOverflow = true;
                        break;
                    }

                    let range = element.max - element.min;
                    let normalizedValue = 0;
                    if (range > 0) {
                        normalizedValue = Math.max(0, Math.min(1, (element.value - element.min) / range));
                    }

                    let bgColor = this.parseColor(element.bgColor);
                    let fgColor = this.parseColor(element.fgColor);
                    if (element.type[0] === 'h') {
                        elWidth = Math.round(barHeight * 2);
                        let fillWidth = normalizedValue * elWidth;
                        cr.setSourceRGBA(bgColor.r, bgColor.g, bgColor.b, 0.5);
                        cr.rectangle(
                            barX,
                            barY + (lineHeight - elWidth) / 2,
                            elWidth,
                            barHeight);
                        cr.fill();

                        cr.setSourceRGBA(fgColor.r, fgColor.g, fgColor.b, 0.5);
                        cr.rectangle(
                            barX,
                            barY + (lineHeight - elWidth) / 2,
                            fillWidth,
                            barHeight);
                        cr.fill();

                        cr.setSourceRGBA(0.5, 0.5, 0.5, 0.8);
                        cr.setLineWidth(1);
                        cr.rectangle(
                            barX,
                            barY + (lineHeight - elWidth) / 2,
                            elWidth,
                            barHeight);
                        cr.stroke();
                    }
                    else {
                        let fillHeight = normalizedValue * barHeight;
                        cr.setSourceRGBA(bgColor.r, bgColor.g, bgColor.b, 0.5);
                        cr.rectangle(barX, barY, elWidth, barHeight);
                        cr.fill();

                        cr.setSourceRGBA(fgColor.r, fgColor.g, fgColor.b, 0.5);
                        cr.rectangle(barX, barY + barHeight - fillHeight, elWidth, fillHeight);
                        cr.fill();

                        cr.setSourceRGBA(0.5, 0.5, 0.5, 0.8);
                        cr.setLineWidth(1);
                        cr.rectangle(barX, barY, elWidth, barHeight);
                        cr.stroke();
                    }

                    currentX = barX + elWidth + spacing;
                    drawnElements++;

                } else if (element.type === 'text') {
                    let fontFamily = this.fontFamily || "Sans";
                    cr.selectFontFace(fontFamily, Cairo.FontSlant.NORMAL, Cairo.FontWeight.NORMAL);
                    let fontSize = this.fontSize || 10;
                    cr.setFontSize(fontSize);

                    let textWidth;
                    let textHeight;
                    try {
                        let extents = cr.textExtents(element.text);
                        textWidth = extents.width;
                        textHeight = extents.height;
                    } catch {
                        textWidth = element.text.length * (fontSize * 0.6);
                        textHeight = fontSize;
                    }

                    let textX = currentX;
                    let textY = y_offset + lineHeight / 2 + textHeight / 2;

                    if (textX + textWidth + overflowIndicatorWidth > width) {
                        if (this.verboseLogging) {
                            global.log("CMD Chart Applet: Out of space for text '" + 
                                element.text + 
                                "', line " +
                                l +
                                " at element " + 
                                i + 
                                " of " + 
                                this.chartElements.length);
                        }
                        hasOverflow = true;
                        break;
                    }

                    this.drawTextWithShadow(cr, element.text, textX, textY, element.color);

                    currentX = textX + textWidth + spacing;
                    drawnElements++;
                }
            }
        }

        if (this.verboseLogging) {
            if (drawnElements < this.chartElements.length) {
                global.log("CMD Chart Applet: WARNING - Not all elements fit! Increase chart width in settings.");
            }
        }

        if (hasOverflow && currentX < width) {
            this.drawOverflowIndicator(cr, currentX, width, height);
        }
    },

    drawGraph: function(cr, width, height) {
        if (!this.history || this.history.length < 2) {
            return;
        }

        let color = this.parseColor(this.graphColor || "g");
        cr.setSourceRGBA(color.r, color.g, color.b, color.a);
        cr.setLineWidth(2);

        let step = width / (this.history.length - 1);
        let minVal = Math.min(...this.history);
        let maxVal = Math.max(...this.history);
        let range = maxVal - minVal || 1;

        cr.moveTo(0, height - ((this.history[0] - minVal) / range) * height);
        for (let i = 1; i < this.history.length; i++) {
            let x = i * step;
            let y = height - ((this.history[i] - minVal) / range) * height;
            cr.lineTo(x, y);
        }
        cr.stroke();
    },

    drawOverflowIndicator: function(cr, x, width, height) {
        let fontSize = this.fontSize || 10;
        cr.selectFontFace("Sans", Cairo.FontSlant.NORMAL, Cairo.FontWeight.BOLD);
        cr.setFontSize(fontSize + 2);

        let indicator = "»";
        let textY = height / 2 + fontSize / 2;
        let textX = Math.min(x + 4, width - 15);

        let fontColor = this.parseRGBAColor(this.fontColor || "rgba(255, 255, 255, 1.0)");
        cr.setSourceRGBA(fontColor.r, fontColor.g, fontColor.b, 0.6);
        cr.moveTo(textX, textY);
        cr.showText(indicator);
    },

    drawTextWithShadow: function(cr, text, x, y, customColor) {
        if (this.enableFontShadow) {
            let shadowColor = this.parseRGBAColor(this.fontShadowColor || "rgba(0, 0, 0, 0.8)");
            cr.setSourceRGBA(shadowColor.r, shadowColor.g, shadowColor.b, shadowColor.a);
            cr.moveTo(x + 1, y + 1);
            cr.showText(text);
        }

        let fontColor;
        if (customColor) {
            fontColor = this.parseColor(customColor);
        } else {
            fontColor = this.parseRGBAColor(this.fontColor || "rgba(255, 255, 255, 1.0)");
        }
        cr.setSourceRGBA(fontColor.r, fontColor.g, fontColor.b, fontColor.a);
        cr.moveTo(x, y);
        cr.showText(text);
    },

    openPreferences: function() {
        Util.spawn(['cinnamon-settings', 'applets', this.uuid, this.instance_id]);
    },

    on_applet_removed_from_panel: function() {
        global.log("CMD Chart Applet: Applet removed from panel");
        if (this.timeout) {
            Mainloop.source_remove(this.timeout);
        }
    }
};

function main(metadata, orientation, panel_height, instance_id) {
    return new CmdChartApplet(orientation, panel_height, instance_id, metadata);
}
