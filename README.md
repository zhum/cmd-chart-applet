# CMD Chart Applet for Cinnamon and MATE DE

A versatile Cinnamon/Mate desktop applet that executes shell commands periodically and displays visual charts based on command output. Perfect for system monitoring, status displays, and custom information panels.

## Features

- 🔄 **Periodic Command Execution** - Run any shell command at configurable intervals (1-3600 seconds)
- 📊 **Visual Elements** - Display graph, circles, bars, and text labels based on command output
- 🎨 **Color Support** - Named colors (r, g, b, y, etc.) and hex RGB values (#RGB, #RRGGBB)
- 🌐 **Text with Spaces** - Use pipe separator ` |` (note space!) to allow natural text with spaces
- 😀 **Emoji Support** - Full emoji support with proper fonts (Noto Color Emoji, Symbola, but depends on cairo verion!)
- 🎨 **Customizable Appearance** - Font selection, colors, transparency, dimensions
- 📝 **Multiple Examples** - Includes system monitor, compact, and emoji examples

## Installation

### Quick Install

```bash
./install-cinnamon.sh  # for cinnamon DE
./install-mate.shi     # for mate DE
```

### Activate

For cinnamon:
1. **Restart Cinnamon**: Press `Alt+F2`, type `r`, press `Enter`
2. **Add Applet**: Right-click panel → Applets → Find "CMD Chart Applet" → Click `+`
3. **Configure**: Right-click applet → Configure

For mate:
1. **Add Applet**: Right-click panel → Add to panel → Find "CMD Chart Applet" → Click `+`
2. **Configure**: Right-click applet → Preferences

## Configuration

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| **Command** | `echo "CR:g"` | Shell command to execute |
| **Update Interval** | 60 seconds | How often to run the command |
| **Chart Width** | 200 pixels | Width of the applet (height is automatic). If elements don't fit, a "»" indicator is shown |
| **Bar Width** | 8 pixels | Width of vertical bars |
| **Verbose Logging** | Off | Enable detailed logging. When off, only errors, start/exit, and config changes are logged |
| **Font Family** | Sans | Font for text labels (dropdown with 20+ fonts) |
| **Font Size** | 10 pixels | Size of text |
| **Font Color** | White | Color for text |
| **Font Shadow** | Enabled | Text shadow for readability |
| **Background Transparency** | 0.3 | Chart background opacity |
| **Graph Transparency** | 0.3 | Graph background opacity |
| **Graph Pionts** | 16 | Graph points to display |

## Command Output Format

Commands output **pipe-separated** elements:

### Element Types

#### 1. Circle: `CR:color`

Displays a colored circle as a status indicator.

**Colors:**

- Single letter: `r` (red), `o` (orange), `y` (yellow), `g` (green), `b` (blue), `v` (violet), `p` (pink), `w` (white), `k` (black)
- Hex: `#f00` or `#ff0000`

**Example:**

```bash
echo "CR:g"              # Green circle
echo "CR:r CR:y CR:g"    # Multiple circles (red, yellow, green)
```

#### 2. Vertical Bar: `BAR:min-max=value:bg:fg`

Displays a vertical bar with fill level.

**Format:** `BAR:minimum-maximum=currentvalue:background:foreground`

**Example:**

```bash
echo "BAR:0-100=75:k:g"     # 75% filled, black background, green fill
echo "BAR:0-5=2.3:w:o"      # Value 2.3 in 0-5 range, white bg, orange fill
```

#### 3. Text Label: `TXT:text`

Displays text on the panel with default font color.

**Example:**

```bash
echo "TXT:CPU:45%"          # Simple text (no spaces)
echo "TXT:Hello World"      # With spaces (use pipe separator, see below)
```

#### 4. Colored Text Label: `TXTC:color:text` or `TXTC:color text`

Displays text with a custom color. The separator between color and text is optional (colon or space). Text can contain colons.

**Example:**

```bash
echo "TXTC:r:ERROR"            # Red error message (with colon)
echo "TXTC:g OK"               # Green OK status (with space)
echo "TXTC:o Warning"          # Orange warning (with space)
echo "TXTC:r a:103"            # Text can contain colons - shows "a:103" in red
echo "TXTC:g Load:2.5"         # Shows "Load:2.5" in green
echo "TXTC:#FF00FF Custom"     # Custom magenta color (hex)
```

#### 5. Graph: `GR:color:value` or `GR:color:value:min:max`

Draws graph on the background of the chart. Values are saved in a history file, by default last 16 are shown.

!! IMPORTANT !! Only one graph is supported, multiple GR elemets will be shown incorrectly.

**Example:**

```bash
echo "GR:r:25"                 # Red graph, last value = 25
echo "GR:#005500:17:0:100"     # Light green graph, last value is 17, min/max = 0/100
```

#### 5. Multi-Line Mode

Displays elements in two or more rows with horizontal bars instead of vertical. More than 2 rows are not recommended.

**Format:** `top line elements || bottom line elements`

- Top and bottom lines separated by `||`
- Bars are horizontal (length = full panel height - 2px)
- Allows twice as much information
- Bars span full height for maximum visibility

**Example:**

```bash
echo "CR:g | TXT:Load | BAR:0-5=2.3:k:o || TXT:Mem | BAR:0-100=60:k:b | TXT:60%"
```

**Result:**
```
Top:    🟢 Load ▓▓▓▓▓░░░░░░░
Bottom: Mem ▓▓▓▓▓▓░░░░ 60%
```

## Usage Examples

### Example 1: System Load Monitor

```bash
#!/bin/bash
load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
load_int=$(echo "$load" | cut -d. -f1)

if [ "$load_int" -lt 1 ]; then
    echo "CR:g | BAR:0-5=${load}:k:g | TXT:Load ${load}"
else
    echo "CR:y | BAR:0-5=${load}:k:y | TXT:Load ${load}"
fi
```

### Example 2: CPU Temperature

```bash
#!/bin/bash
temp=$(sensors | grep 'Core 0' | awk '{print $3}' | tr -d '+°C' | cut -d. -f1)

if [ "$temp" -lt 60 ]; then
    echo "TXT:${temp}°C | BAR:0-100=${temp}:k:g"
elif [ "$temp" -lt 80 ]; then
    echo "TXT:${temp}°C | BAR:0-100=${temp}:k:y"
else
    echo "TXT:${temp}°C | BAR:0-100=${temp}:k:r"
fi
```

### Example 3: Memory Usage

```bash
#!/bin/bash
mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
echo "TXT:Mem ${mem_pct}% | BAR:0-100=${mem_pct}:k:b"
```

### Example 4: Network Status

```bash
#!/bin/bash
ping -c 1 -W 1 8.8.8.8 &>/dev/null && \
    echo "CR:g | TXT:Online" || \
    echo "CR:r | TXT:Offline"
```

### Example 5: With Emojis

```bash
#!/bin/bash
# Use "Noto Color Emoji" font for best results
load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
temp=$(sensors | grep 'Core 0' | awk '{print $3}' | tr -d '+°C' | cut -d. -f1)
mem=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')

echo "CR:g | TXT:🟢 Load ${load} | TXT:🌡️ ${temp}°C | TXT:💾 ${mem}%"
```

### Example 6: Two-Line Mode

```bash
#!/bin/bash
# Display in two lines with horizontal bars
load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
temp=$(sensors | grep 'Core 0' | awk '{print $3}' | tr -d '+°C' | cut -d. -f1)
mem=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
disk=$(df -h / | awk 'NR==2{gsub(/%/,"",$5); print $5}')

# Top line: Load and temperature
top="CR:g | TXT:Load | BAR:0-5=${load}:k:o | TXT:${temp}°C | BAR:0-100=${temp}:k:r"

# Bottom line: Memory and disk
bottom="TXT:Mem | BAR:0-100=${mem}:k:b | TXT:${mem}% | TXT:Disk | BAR:0-100=${disk}:k:y"

echo "${top}||${bottom}"
```

## Included Example Scripts

### 1. System Monitor (Full)

**File:** `example-system-monitor.sh`

```bash
./example-system-monitor.sh
```

Shows: Load indicator, load bar, CPU temperature, temp bar, memory usage.

### 2. System Monitor (Compact)

**File:** `example-system-monitor-compact.sh`  
Shows: Load indicator, temperature text, memory bar (3 elements, ~100px).

### 3. With Text Spaces

**File:** `example-with-text-spaces.sh`  
Demonstrates using pipe separator for natural text with spaces.

### 4. With Emojis

**File:** `example-with-emojis.sh`  
System monitor with emoji indicators (may not be supported by your Cairo version!).

### 5. Test Examples

**File:** `test-examples.sh`  
Demonstrates all element types and features.

### 6. Refresh Test

**File:** `test-refresh.sh`  
Shows time updating every 2-5 seconds to verify refresh is working.

### 7. Overflow Indicator Test

**File:** `test-overflow.sh`  
Outputs many elements to demonstrate the overflow indicator "»" when elements don't fit within the chart width.

### 8. Colored Text Test

**File:** `test-colored-text.sh`  
Demonstrates colored text labels using `TXTC:color:text` format with various colors.

### 9. Status Monitor with Colors

**File:** `example-status-monitor.sh`  
Practical example using colored text for system status monitoring. Text color changes based on thresholds:
- Green: Normal
- Orange: Warning
- Red: Critical

### 10. Two-Line Chart

**File:** `example-two-line.sh`  
```bash
./example-two-line.sh
```
Demonstrates 2-line mode with horizontal bars.  
**Top line:** System load and CPU temperature  
**Bottom line:** Memory and disk usage

## Using Emojis

### Setup for Emojis

1. **Select Emoji Font:**
   - Configure applet → Font family → "Noto Color Emoji (✅ emojis, full color)"

2. **Test Emoji Support:**

```bash
./test-emoji-fonts.sh
```

### Recommended Emoji Fonts

- **Noto Color Emoji** - Full color emojis (best!)
- **Symbola** - Black & white emojis and symbols
- **Noto Sans Symbols** - Symbol coverage

### Useful Emojis

**Status:** ✅ ❌ ⚠️  ℹ️ 
**Levels:** 🟢 🟡 🔴 🔵
**System:** 💾 🌡️ 📊 ⚡ 🔋 📈 📉 🖥️ 🌐

## Logging

The applet uses different logging levels:

### Default Logging (Verbose Off)
- Applet start/exit events
- Configuration changes
- Command execution errors
- Exceptions

### Verbose Logging (Verbose On)
When enabled in settings, logs all operations:
- Command execution details
- Output parsing results
- Element drawing operations
- Space constraints and overflow warnings

### View Logs

```bash
# Monitor logs in real-time
journalctl -f | grep "CMD Chart" # Cinnamon version
journalctl -f | grep "CmdChartApplet" # Mate version
```

## Troubleshooting

### Only First Element Shows

**Problem:** Chart width too small for all elements.

**Solution:**

1. Right-click applet → Configure
2. Increase "Chart width"
3. Click OK
4. Restart Cinnamon or Mate panel

Enable verbose logging and monitor logs:

```bash
# Enable verbose logging in settings, then:
journalctl -f | grep "CMD Chart"
# Look for: "Drew X of X elements"
```

### Elements Not Showing

**Check command output:**

```bash
your-command-here
```

Should produce valid format like: `CR:g | TXT:OK | BAR:0-100=50:k:g`

**Common issues:**

- Missing separators (note space before pipe!)
- Invalid color codes
- Malformed BAR syntax

### Emojis Show as Boxes

**Problem:** Font doesn't support emojis.

**Solution:**

- Change font to "Noto Color Emoji"
- Install emoji fonts: `sudo apt install fonts-noto-color-emoji`

### Refresh Not Working

**Solutions:**

1. Check "Update interval" setting
2. Ensure command completes successfully
3. Restart Cinnamon (Alt+F2, 'r', Enter) or Mate panel (mate-panel --replace &)
4. Check logs for errors

## Utility Scripts

### List Available Fonts

```bash
./list-fonts.sh
```

### Test Emoji Fonts

```bash
./test-emoji-fonts.sh
```

## Development

### File Structure

```text
cmd-chart-applet@cinnamon/
├── applet.js              # Main applet code
├── metadata.json          # Applet metadata
├── settings-schema.json   # Configuration schema
└── README.md             # This file
```

### Key Functions

**`parseCommandOutput(output)`** - Parses command output into elements  
**`executeCommand()`** - Runs command and updates display  
**`drawPanelChart(area)`** - Renders visual elements  

### Parsing Logic

1. Detect separator: pipe `|` or whitespace
2. Split output into tokens
3. Parse each token by prefix:
   - `CR:` → Circle
   - `BAR:` → Vertical bar
   - `TXT:` → Text label
4. Draw elements left-to-right

### Adding New Element Types

To add a new element type:

1. Add parsing logic in `parseCommandOutput()`
2. Add drawing logic in `drawPanelChart()`
3. Update documentation

### Testing

```bash
# Install changes
./install-cinnamon.sh

# Restart Cinnamon
# Press Alt+F2, type 'r', Enter

# Monitor logs
journalctl -f | grep "CMD Chart"

# Test with examples
./test-examples.sh
```

## Technical Notes

- **Height:** Automatically uses full panel height
- **Width:** Configurable (20-600 pixels)
- **Element spacing:** 4 pixels between elements
- **Circle radius:** `Math.min(height/2 - 2, 10)` pixels (single-line), `Math.min(height/2 - 2, 8)` pixels (2-line)
- **Vertical bar width:** Configurable (8-40 pixels, default 16)
- **Horizontal bar length (2-line mode):** Full panel height - 2 pixels
- **Horizontal bar height (2-line mode):** 8 pixels
- **Text width:** Estimated at `length * (fontSize * 0.6)` pixels
- **Update frequency:** 1-3600 seconds
- **Command execution:** Synchronous (GLib.spawn_command_line_sync)

## Color Reference

**Named Colors:**
- `r` = Red
- `o` = Orange
- `y` = Yellow
- `g` = Green
- `b` = Blue
- `v` = Violet
- `p` = Pink
- `w` = White
- `k` = Black

**Hex Colors:**
- `#f00` = Red (3-digit)
- `#ff0000` = Red (6-digit)
- `#0f0` = Green
- `#00f` = Blue
- Any valid RGB hex code

## Requirements

- **Desktop:** Cinnamon 4.0+
- **Dependencies:** Built into Cinnamon (GJS, Cairo, St)
- **Optional:** 
  - `sensors` for temperature monitoring
  - `fonts-noto-color-emoji` for emoji support
  - `fontconfig` for font listing

## Version History

See [CHANGES.md](CHANGES.md) for detailed changelog.

**Current version:** 2.0.0 - Complete rewrite with command-based architecture

## License

Apache-2.0 License

## Support

**Logs:**
```bash
journalctl -f | grep "CMD Chart"
```

**Test command:**
```bash
echo "CR:g | TXT:Test | BAR:0-100=50:k:g"
```

**Verify installation:**
```bash
ls -la ~/.local/share/cinnamon/applets/cmd-chart-applet@cinnamon/
```

---

**Transform command output into beautiful visual displays on your Cinnamon desktop!** 🎨
