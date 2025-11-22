const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const St = imports.gi.St;
const GLib = imports.gi.GLib;
const Util = imports.misc.util;
const Lang = imports.lang;
const Settings = imports.ui.settings;
const Mainloop = imports.mainloop;
const Cairo = imports.cairo;
const Clutter = imports.gi.Clutter;

function CmdChartApplet(orientation, panel_height, instance_id) {
    this._init(orientation, panel_height, instance_id);
}

CmdChartApplet.prototype = {
    __proto__: Applet.Applet.prototype,

    _init: function(orientation, panel_height, instance_id) {
        Applet.Applet.prototype._init.call(this, orientation, panel_height, instance_id);

        try {
            // Store panel height to use full available height
            this.panel_height = panel_height;
            
            this.set_applet_tooltip(_("CMD Chart Applet"));

            // Initialize settings
            this.settings = new Settings.AppletSettings(this, "cmd-chart-applet@cinnamon", instance_id);
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

            // Data storage for parsed elements
            this.chartElements = [];
            this.lastOutput = "";

            // Create panel chart - use full panel height
            this.panelChartActor = new St.DrawingArea({
                width: this.chartWidth || 200,
                height: this.panel_height
            });
            this.panelChartActor.connect('repaint', Lang.bind(this, this.drawPanelChart));
            this.actor.add_child(this.panelChartActor);

            // Setup context menu
            this.menuManager = new PopupMenu.PopupMenuManager(this);
            this.menu = new Applet.AppletPopupMenu(this, orientation);
            this.menuManager.addMenu(this.menu);

            this._contentSection = new PopupMenu.PopupMenuSection();
            this.menu.addMenuItem(this._contentSection);

            // Add preferences menu item
            let prefsItem = new PopupMenu.PopupMenuItem(_("Preferences"));
            prefsItem.connect('activate', Lang.bind(this, this.openPreferences));
            this.menu.addMenuItem(prefsItem);

            // Start monitoring
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
        this.setupTimer();
        this.rebuildPanelChart();
        this.executeCommand();
    },

    rebuildPanelChart: function() {
        // Remove existing panel chart
        if (this.panelChartActor) {
            this.actor.remove_child(this.panelChartActor);
            this.panelChartActor = null;
        }

        // Create new panel chart with updated dimensions - use full panel height
        this.panelChartActor = new St.DrawingArea({
            width: this.chartWidth || 200,
            height: this.panel_height
        });
        this.panelChartActor.connect('repaint', Lang.bind(this, this.drawPanelChart));
        this.actor.add_child(this.panelChartActor);
    },

    parseColor: function(colorCode) {
        // Parse color codes: r, o, y, g, b, v, p, w, k, or #RRGGBB
        let colors = {
            'r': { r: 1.0, g: 0.0, b: 0.0, a: 1.0 },      // red
            'o': { r: 1.0, g: 0.5, b: 0.0, a: 1.0 },      // orange
            'y': { r: 1.0, g: 1.0, b: 0.0, a: 1.0 },      // yellow
            'g': { r: 0.0, g: 0.8, b: 0.0, a: 1.0 },      // green
            'b': { r: 0.0, g: 0.0, b: 1.0, a: 1.0 },      // blue
            'v': { r: 0.5, g: 0.0, b: 1.0, a: 1.0 },      // violet
            'p': { r: 1.0, g: 0.0, b: 0.5, a: 1.0 },      // pink
            'w': { r: 1.0, g: 1.0, b: 1.0, a: 1.0 },      // white
            'k': { r: 0.0, g: 0.0, b: 0.0, a: 1.0 }       // black
        };

        if (colorCode in colors) {
            return colors[colorCode];
        }

        // Parse hex color #RGB or #RRGGBB
        if (colorCode.startsWith('#')) {
            let hex = colorCode.substring(1);
            if (hex.length === 3) {
                // #RGB format
                let r = parseInt(hex[0] + hex[0], 16) / 255;
                let g = parseInt(hex[1] + hex[1], 16) / 255;
                let b = parseInt(hex[2] + hex[2], 16) / 255;
                return { r: r, g: g, b: b, a: 1.0 };
            } else if (hex.length === 6) {
                // #RRGGBB format
                let r = parseInt(hex.substring(0, 2), 16) / 255;
                let g = parseInt(hex.substring(2, 4), 16) / 255;
                let b = parseInt(hex.substring(4, 6), 16) / 255;
                return { r: r, g: g, b: b, a: 1.0 };
            }
        }

        // Default to white if parsing fails
        return { r: 1.0, g: 1.0, b: 1.0, a: 1.0 };
    },

    parseRGBAColor: function(colorString) {
        // Parse rgba color string like "rgba(51, 204, 51, 1.0)"
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
        // Default white color
        return { r: 1.0, g: 1.0, b: 1.0, a: 1.0 };
    },

    parseCommandOutput: function(output) {
        // Parse command output for chart elements with new simple format:
        // CR:color - circle with color (r,o,y,g,b,v,p,w,k, or #RGB/#RRGGBB)
        // BAR:min-max=value:bg:fg - vertical bar (or horizontal in 2-line mode)
        // TXT:text - text label (can contain spaces!)
        // Elements are separated by pipe '|' (or whitespace for backward compatibility)
        // 2-line mode: 2L| top elements || bottom elements

        let elements = [];
        let twoLineMode = false;
        let topLineElements = [];
        let bottomLineElements = [];
        
        // Check for 2-line mode marker
        if (output.trim().startsWith('2L|')) {
            twoLineMode = true;
            output = output.trim().substring(3); // Remove '2L|' marker
            
            // Split into top and bottom lines using '||' separator
            let lines = output.split('||');
            if (lines.length >= 2) {
                topLineElements = this.parseElementLine(lines[0]);
                bottomLineElements = this.parseElementLine(lines[1]);
                
                return {
                    twoLineMode: true,
                    topLine: topLineElements,
                    bottomLine: bottomLineElements
                };
            }
        }
        
        // Single line mode (original behavior)
        elements = this.parseElementLine(output);
        return {
            twoLineMode: false,
            elements: elements
        };
    },

    parseElementLine: function(output) {
        // Parse a single line of elements
        let elements = [];
        
        // Split by pipe first (new format), or whitespace (old format for compatibility)
        let separator = output.includes('|') ? '|' : /\s+/;
        let tokens = output.trim().split(separator);
        
        for (let token of tokens) {
            // Trim whitespace from each token
            token = token.trim();
            if (!token) continue; // Skip empty tokens
            
            if (token.startsWith('CR:')) {
                // Circle: CR:color
                let color = token.substring(3);
                if (color) {
                    elements.push({
                        type: 'circle',
                        color: color
                    });
                }
            } else if (token.startsWith('BAR:')) {
                // Bar: BAR:min-max=value:bg:fg
                let parts = token.substring(4).split(':');
                if (parts.length >= 3) {
                    // Parse min-max=value
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
            } else if (token.startsWith('TXT:')) {
                // Text: TXT:text
                let text = token.substring(4);
                if (text) {
                    elements.push({
                        type: 'text',
                        text: text
                    });
                }
            }
        }

        return elements;
    },  // End of parseElementLine

    executeCommand: function() {
        try {
            let cmd = this.command || 'echo "CR:g"';
            
            global.log("CMD Chart Applet: Executing command: " + cmd);
            
            // Execute command synchronously
            let [success, stdout, stderr] = GLib.spawn_command_line_sync(cmd);

            if (success && stdout) {
                this.lastOutput = stdout.toString().trim();
                let parsed = this.parseCommandOutput(this.lastOutput);
                
                // Store parsed data
                this.twoLineMode = parsed.twoLineMode;
                if (parsed.twoLineMode) {
                    this.topLineElements = parsed.topLine;
                    this.bottomLineElements = parsed.bottomLine;
                    global.log("CMD Chart Applet: Command output: " + this.lastOutput);
                    global.log("CMD Chart Applet: 2-line mode: top=" + this.topLineElements.length + " elements, bottom=" + this.bottomLineElements.length + " elements");
                } else {
                    this.chartElements = parsed.elements;
                    global.log("CMD Chart Applet: Command output: " + this.lastOutput);
                    global.log("CMD Chart Applet: Parsed " + this.chartElements.length + " elements");
                }
                
                // Update tooltip with command output
                this.set_applet_tooltip("Command: " + cmd + "\nOutput: " + this.lastOutput);
                
                // Redraw panel chart
                if (this.panelChartActor) {
                    global.log("CMD Chart Applet: Requesting repaint");
                    this.panelChartActor.queue_repaint();
                }
            } else {
                global.log("CMD Chart Applet: Command failed");
                this.set_applet_tooltip("Command failed: " + cmd);
                this.chartElements = [];
                if (this.panelChartActor) {
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

        return true; // Continue the timer
    },

    drawPanelChart: function(area) {
        let cr = area.get_context();
        let [width, height] = area.get_surface_size();

        // Clear background with transparency setting
        let backgroundTransparency = this.chartAreaTransparency !== undefined ? this.chartAreaTransparency : 0.3;
        cr.setSourceRGBA(0.0, 0.0, 0.0, backgroundTransparency);
        cr.rectangle(0, 0, width, height);
        cr.fill();

        // Check for 2-line mode
        if (this.twoLineMode) {
            global.log("CMD Chart Applet: 2-line mode, top=" + (this.topLineElements ? this.topLineElements.length : 0) + 
                      ", bottom=" + (this.bottomLineElements ? this.bottomLineElements.length : 0));
            this.drawTwoLineChart(cr, width, height);
            return;
        }

        // Single line mode (original)
        global.log("CMD Chart Applet: Single-line mode, elements: " + (this.chartElements ? this.chartElements.length : 0));

        if (!this.chartElements || this.chartElements.length === 0) {
            // No elements to draw
            global.log("CMD Chart Applet: No elements to draw");
            return;
        }

        // Calculate spacing for elements
        let spacing = 4;
        let currentX = spacing;
        let drawnElements = 0;

        for (let i = 0; i < this.chartElements.length; i++) {
            let element = this.chartElements[i];

            if (element.type === 'circle') {
                // Draw circle
                let radius = Math.min(height / 2 - 2, 10);
                let centerX = currentX + radius;
                let centerY = height / 2;

                if (centerX + radius > width) {
                    global.log("CMD Chart Applet: Out of space for circle at element " + i + "/" + this.chartElements.length);
                    break; // Out of space
                }

                let color = this.parseColor(element.color);
                cr.setSourceRGBA(color.r, color.g, color.b, color.a);
                cr.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                cr.fill();

                currentX = centerX + radius + spacing;
                drawnElements++;

            } else if (element.type === 'bar') {
                // Draw vertical bar
                let barWidth = this.barWidth || 16;
                let barHeight = height - 4;
                let barX = currentX;
                let barY = 2;

                if (barX + barWidth > width) {
                    global.log("CMD Chart Applet: Out of space for bar at element " + i + "/" + this.chartElements.length);
                    break; // Out of space
                }

                // Calculate bar fill height based on value
                let range = element.max - element.min;
                let normalizedValue = 0;
                if (range > 0) {
                    normalizedValue = Math.max(0, Math.min(1, (element.value - element.min) / range));
                }
                let fillHeight = normalizedValue * barHeight;

                // Draw background
                let bgColor = this.parseColor(element.bgColor);
                cr.setSourceRGBA(bgColor.r, bgColor.g, bgColor.b, bgColor.a);
                cr.rectangle(barX, barY, barWidth, barHeight);
                cr.fill();

                // Draw foreground (filled portion from bottom)
                let fgColor = this.parseColor(element.fgColor);
                cr.setSourceRGBA(fgColor.r, fgColor.g, fgColor.b, fgColor.a);
                cr.rectangle(barX, barY + barHeight - fillHeight, barWidth, fillHeight);
                cr.fill();

                // Draw border
                cr.setSourceRGBA(0.5, 0.5, 0.5, 0.8);
                cr.setLineWidth(1);
                cr.rectangle(barX, barY, barWidth, barHeight);
                cr.stroke();

                currentX = barX + barWidth + spacing;
                drawnElements++;

            } else if (element.type === 'text') {
                // Draw text
                let fontFamily = this.fontFamily || "Sans";
                cr.selectFontFace(fontFamily, Cairo.FontSlant.NORMAL, Cairo.FontWeight.NORMAL);
                let fontSize = this.fontSize || 10;
                cr.setFontSize(fontSize);

                // Try to get actual text width, fall back to estimation if not available
                let textWidth;
                let textHeight;
                try {
                    // Try Cairo's text measurement (might not be available in all GJS versions)
                    let extents = cr.textExtents(element.text);
                    textWidth = extents.width;
                    textHeight = extents.height;
                } catch (e) {
                    // Fall back to estimation
                    textWidth = element.text.length * (fontSize * 0.6);
                    textHeight = fontSize;
                }

                let textX = currentX;
                let textY = height / 2 + textHeight / 2;

                if (textX + textWidth > width) {
                    global.log("CMD Chart Applet: Out of space for text '" + element.text + "' at element " + i + "/" + this.chartElements.length);
                    break; // Out of space
                }

                this.drawTextWithShadow(cr, element.text, textX, textY);

                currentX = textX + textWidth + spacing;
                drawnElements++;
            }
        }

        global.log("CMD Chart Applet: Drew " + drawnElements + " of " + this.chartElements.length + " elements");
        
        if (drawnElements < this.chartElements.length) {
            global.log("CMD Chart Applet: WARNING - Not all elements fit! Increase chart width in settings.");
        }
    },

    drawTwoLineChart: function(cr, width, height) {
        // Draw chart with two lines (top and bottom)
        let lineHeight = height / 2;
        let spacing = 4;
        
        // Draw top line (bars use full height)
        if (this.topLineElements && this.topLineElements.length > 0) {
            this.drawElementLine(cr, this.topLineElements, width, height, lineHeight, 0, spacing, true);
        }
        
        // Draw bottom line (bars use full height)
        if (this.bottomLineElements && this.bottomLineElements.length > 0) {
            this.drawElementLine(cr, this.bottomLineElements, width, height, lineHeight, lineHeight, spacing, true);
        }
    },

    drawElementLine: function(cr, elements, width, fullHeight, lineHeight, yOffset, spacing, horizontalBars) {
        // Draw a line of elements (for 2-line mode or regular mode)
        // fullHeight - total applet height (for bar length in 2-line mode)
        // lineHeight - height of current line (for element vertical positioning)
        // yOffset - vertical offset for this line
        let currentX = spacing;
        let drawnElements = 0;
        
        for (let i = 0; i < elements.length; i++) {
            let element = elements[i];
            
            if (element.type === 'circle') {
                // Draw circle
                let radius = Math.min(lineHeight / 2 - 2, 8);
                let centerX = currentX + radius;
                let centerY = yOffset + lineHeight / 2;
                
                if (centerX + radius > width) {
                    global.log("CMD Chart Applet: Out of space for circle");
                    break;
                }
                
                let color = this.parseColor(element.color);
                cr.setSourceRGBA(color.r, color.g, color.b, color.a);
                cr.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                cr.fill();
                
                currentX = centerX + radius + spacing;
                drawnElements++;
                
            } else if (element.type === 'bar') {
                if (horizontalBars) {
                    // Horizontal bar for 2-line mode - use full applet height
                    let maxBarLength = fullHeight - 2;  // Full height minus margins
                    let barHeight = 8;
                    let barX = currentX;
                    let barY = yOffset + (lineHeight - barHeight) / 2;
                    
                    // Calculate bar length based on value
                    let range = element.max - element.min;
                    let normalizedValue = 0;
                    if (range > 0) {
                        normalizedValue = Math.max(0, Math.min(1, (element.value - element.min) / range));
                    }
                    let barLength = normalizedValue * maxBarLength;
                    
                    if (barX + maxBarLength > width) {
                        global.log("CMD Chart Applet: Out of space for horizontal bar");
                        break;
                    }
                    
                    // Draw background
                    let bgColor = this.parseColor(element.bgColor);
                    cr.setSourceRGBA(bgColor.r, bgColor.g, bgColor.b, bgColor.a);
                    cr.rectangle(barX, barY, maxBarLength, barHeight);
                    cr.fill();
                    
                    // Draw foreground (filled portion from left)
                    let fgColor = this.parseColor(element.fgColor);
                    cr.setSourceRGBA(fgColor.r, fgColor.g, fgColor.b, fgColor.a);
                    cr.rectangle(barX, barY, barLength, barHeight);
                    cr.fill();
                    
                    // Draw border
                    cr.setSourceRGBA(0.5, 0.5, 0.5, 0.8);
                    cr.setLineWidth(1);
                    cr.rectangle(barX, barY, maxBarLength, barHeight);
                    cr.stroke();
                    
                    currentX = barX + maxBarLength + spacing;
                    drawnElements++;
                } else {
                    // Vertical bar (original mode - shouldn't happen in 2-line mode)
                    // Keep for potential future use
                }
                
            } else if (element.type === 'text') {
                // Draw text
                let fontFamily = this.fontFamily || "Sans";
                cr.selectFontFace(fontFamily, Cairo.FontSlant.NORMAL, Cairo.FontWeight.NORMAL);
                let fontSize = this.fontSize || 10;
                cr.setFontSize(fontSize);
                
                // Try to get actual text width
                let textWidth;
                let textHeight;
                try {
                    let extents = cr.textExtents(element.text);
                    textWidth = extents.width;
                    textHeight = extents.height;
                } catch (e) {
                    textWidth = element.text.length * (fontSize * 0.6);
                    textHeight = fontSize;
                }
                
                let textX = currentX;
                let textY = yOffset + lineHeight / 2 + textHeight / 2;
                
                if (textX + textWidth > width) {
                    global.log("CMD Chart Applet: Out of space for text");
                    break;
                }
                
                this.drawTextWithShadow(cr, element.text, textX, textY);
                
                currentX = textX + textWidth + spacing;
                drawnElements++;
            }
        }
        
        global.log("CMD Chart Applet: Drew " + drawnElements + " of " + elements.length + " elements in line");
    },

    drawTextWithShadow: function(cr, text, x, y) {
        // Draw shadow first if enabled
        if (this.enableFontShadow) {
            let shadowColor = this.parseRGBAColor(this.fontShadowColor || "rgba(0, 0, 0, 0.8)");
            cr.setSourceRGBA(shadowColor.r, shadowColor.g, shadowColor.b, shadowColor.a);
            cr.moveTo(x + 1, y + 1); // Offset shadow by 1 pixel right and down
            cr.showText(text);
        }

        // Draw main text
        let fontColor = this.parseRGBAColor(this.fontColor || "rgba(255, 255, 255, 1.0)");
        cr.setSourceRGBA(fontColor.r, fontColor.g, fontColor.b, fontColor.a);
        cr.moveTo(x, y);
        cr.showText(text);
    },

    openPreferences: function() {
        Util.spawn(['cinnamon-settings', 'applets', 'cmd-chart-applet@cinnamon']);
    },

    on_applet_removed_from_panel: function() {
        if (this.timeout) {
            Mainloop.source_remove(this.timeout);
        }
    }
};

function main(metadata, orientation, panel_height, instance_id) {
    return new CmdChartApplet(orientation, panel_height, instance_id);
}
