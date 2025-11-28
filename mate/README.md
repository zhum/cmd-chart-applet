# CMD Chart Applet for Mate

## Features

- **Periodic Command Execution** - Run any shell command at configurable intervals (1-3600 seconds)
- **Visual Elements** - Display circles, bars, and text labels based on command output
- **Color Support** - Named colors (r, g, b, y, etc.) and hex RGB values (#RGB, #RRGGBB)
- **Text with Spaces** - Use pipe separator `|` to allow natural text with spaces
- **Customizable Appearance** - Font selection, colors, transparency, dimensions
- **Auto-sizing** - Automatically uses full panel height

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

## Command Output Format

Commands output **space-separated** or **pipe-separated** elements:

### Element Types

#### 1. Circle: `CR:color`

Displays a colored circle as a status indicator.

**Colors:**

- Single letter: `r` (red), `o` (orange), `y` (yellow), `g` (green), `b` (blue), `v` (violet), `p` (pink), `w` (white), `k` (black)
- Hex: `#f00` or `#ff0000`


#### 2. Vertical Bar: `BAR:min-max=value:bg:fg`

Displays a vertical bar with fill level.

**Format:** `BAR:minimum-maximum=currentvalue:background:foreground`

#### 3. Text Label: `TXT:text`

Displays text on the panel with default font color, text may contain ':' or spaces

#### 4. Colored Text Label: `TXTC:color:text` or `TXTC:color text`

Displays text with a custom color. The separator between color and text is optional (colon or space). Text can contain colons.

#### 5. Two-Line Mode: `2L|`

Displays elements in two rows with horizontal bars instead of vertical.

**Format:** `2L| top line elements || bottom line elements`

- Starts with `2L|` marker
- Top and bottom lines separated by `||`
- Bars are horizontal (length = full panel height - 2px)
- Allows twice as much information
- Bars span full height for maximum visibility

### Separator Options

**Space Separator (simple):**

```bash
echo "CR:g TXT:OK BAR:0-100=50:k:g"
```

Note: Text cannot contain spaces with this method.

**Pipe Separator (allows spaces in text):**

```bash
echo "CR:g | TXT:Status is OK | BAR:0-100=50:k:g"
```

Note: Pipe `|` allows natural text with spaces.
