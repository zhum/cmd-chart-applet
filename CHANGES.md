# Changelog

## Version 2.0.0 (2024-11-21)

Complete rewrite of the applet from stock price monitor to versatile command-based chart display.

### Major Changes

#### 1. New Command-Based Architecture
- **Removed:** Stock market API integration (Finnhub)
- **Added:** Execute any shell command periodically
- **Added:** Parse command output for visual elements
- **Result:** Universal monitoring tool instead of stock-only

#### 2. New Simple Notation Format
- **Old format:** Complex regex-based parsing with `[brackets]`, `!bars!`, `~tildes~`
- **New format:** Simple prefix-based parsing
  - `CR:color` for circles
  - `BAR:min-max=value:bg:fg` for bars
  - `TXT:text` for text labels
- **Benefit:** Reliable parsing, no regex issues

#### 3. Text with Spaces Support
- **Problem:** Space-separated format didn't allow spaces in text
- **Solution:** Pipe separator `|` for element separation
- **Result:** Natural text like "Load is 2.3" instead of "Load:2.3"
- **Backward compatible:** Space separator still works

#### 4. Emoji Support
- **Added:** Font selection with emoji-capable fonts
- **Added:** Dropdown with 20+ fonts including:
  - Noto Color Emoji (full color emojis)
  - Symbola (black & white emojis)
  - Noto Sans Symbols
- **Added:** `test-emoji-fonts.sh` utility
- **Note:** Depends on Cairo version support

#### 5. Automatic Height
- **Removed:** Fixed height setting (was 24px default)
- **Added:** Automatic panel height detection
- **Result:** Applet always uses full panel height
- **Benefit:** Works perfectly with any panel size

#### 6. Configurable Bar Width
- **Added:** Bar width setting (8-40 pixels, default 16)
- **Benefit:** Customize bar appearance and fit more/fewer elements

#### 7. Enhanced Settings
- **Added:** Font family dropdown (20+ fonts)
- **Added:** Bar width control
- **Removed:** Fixed chart height (now automatic)
- **Improved:** Chart width range (20-600 pixels, default 200)
- **Improved:** Update interval range (1-3600 seconds)

#### 8. Two-Line Mode
- **Added:** Optional 2-line display mode
- **Format:** `2L| top elements || bottom elements`
- **Feature:** Horizontal bars instead of vertical
- **Benefit:** Display twice as much information
- **Bar length:** Full panel height - 2px (spans entire height)
- **Use case:** Comprehensive system monitoring in limited space

#### 9. Overflow Indicator
- **Added:** Visual indicator when elements don't fit
- **Display:** "»" symbol shown at the end when elements are hidden
- **Benefit:** Clear feedback that width needs to be increased
- **Style:** Semi-transparent to distinguish from regular content
- **Works in:** Both 1-line and 2-line modes

#### 10. Verbose Logging Control
- **Added:** Toggle for verbose logging in settings
- **Default:** Off (logs only errors, start/exit, config changes)
- **When enabled:** Logs all operations (command execution, parsing, drawing)
- **Benefit:** Quieter logs by default, detailed logs when needed for debugging
- **Changed:** Default bar width from 16px to 8px for more compact display

### Bug Fixes

#### Issue #1: Screen Not Refreshing
- **Problem:** Display not updating after command execution
- **Cause:** Missing `queue_repaint()` call in error handler
- **Fix:** Added repaint calls in all code paths
- **Result:** Display updates reliably every interval

#### Issue #2: Only First Element Showing
- **Problem:** Only violet circle visible, other elements missing
- **Root cause:** Complex regex pattern failed to parse bars like `!0-5=4.42!k/o`
- **Fix:** Redesigned notation to use simple split-by-separator parsing
- **Result:** All elements parse correctly

#### Issue #3: Text Drawing Failure
- **Problem:** `TypeError: cr.textExtents is not a function`
- **Cause:** Cairo API differences in GJS
- **Fix:** Try-catch with fallback to text width estimation
- **Result:** Text elements display correctly

#### Issue #4: Default Width Too Small
- **Problem:** Default 80px too narrow for typical 5-element displays
- **Fix:** Increased default to 200px
- **Result:** Most displays work without width adjustment

### New Features

#### Comprehensive Logging
- Command execution logging
- Element parsing count
- Repaint requests
- Elements drawn vs. total
- Width overflow warnings

#### Example Scripts
1. **example-system-monitor.sh** - Full system monitor (5 elements)
2. **example-system-monitor-compact.sh** - Compact version (3 elements)
3. **example-with-text-spaces.sh** - Demonstrates pipe separator
4. **example-with-emojis.sh** - Emoji indicators (Cairo-dependent)
5. **example-two-line.sh** - Two-line mode with horizontal bars
6. **test-examples.sh** - All features demonstration
7. **test-refresh.sh** - Visual refresh verification

#### Utility Scripts
1. **list-fonts.sh** - List available fonts on system
2. **test-emoji-fonts.sh** - Detect emoji-capable fonts

#### Documentation
- **README.md** - Comprehensive single-file documentation
- **CHANGES.md** - This file
- Removed 15 redundant documentation files
- Clean, organized project structure

### Technical Improvements

#### Parsing Engine
- **Old:** Complex regex with multiple alternations
- **New:** Simple split + prefix detection
- **Performance:** Faster and more reliable
- **Maintainability:** Easy to understand and extend

#### Error Handling
- Try-catch around text measurement
- Fallback to estimation if Cairo API unavailable
- Graceful degradation for emoji support
- Comprehensive error logging

#### Code Quality
- **Reduced:** 612 lines → 443 lines
- **Removed:** HTTP library (Soup) dependency
- **Removed:** Data persistence for price history
- **Simplified:** Settings schema (14 → 9 main settings)
- **No linter errors**

### Breaking Changes

⚠️ **This is a major breaking change from v1.x:**

1. **Notation format changed:**
   - Old: `[g] !0-100=75!r/g ~text~`
   - New: `CR:g BAR:0-100=75:r:g TXT:text`

2. **Settings removed:**
   - API token
   - Stock symbol
   - Show current price
   - Show daily range
   - Show symbol on panel
   - Chart height (now automatic)

3. **Functionality changed:**
   - No longer monitors stocks automatically
   - Must configure command for monitoring
   - No data history storage

4. **Migration required:**
   - Remove old applet
   - Install new version
   - Restart Cinnamon
   - Configure with new command format

### Performance

- **Startup:** Faster (no HTTP initialization)
- **Memory:** Lower (no history storage)
- **CPU:** Minimal (depends on command execution)
- **Recommended minimum interval:** 5 seconds

### Known Limitations

1. **Synchronous execution:** Commands block UI briefly
2. **No history:** Only last execution stored
3. **Width-dependent:** Element count limited by width
4. **No multi-line text:** Text labels are single-line
5. **Fixed bar width:** Bar width is configurable but uniform
6. **Emoji support:** Depends on Cairo version (may not work on all systems)

### Compatibility

- **Cinnamon:** 4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 6.0
- **Dependencies:** Built-in (GJS, Cairo, St)
- **Optional:** sensors, fontconfig, fonts-noto-color-emoji

### Migration Guide

**From v1.x (Stock Monitor):**

1. Remove old applet from panel
2. Install new version: `./install-cinnamon.sh`
3. Restart Cinnamon: Alt+F2, type 'r', Enter
4. Add applet from Applets menu
5. Configure with new command format

**Example stock monitoring replacement:**
```bash
# Create custom script that fetches stock data
# Format output as: CR:color BAR:... TXT:...
# Set as command in applet
```

### Future Enhancements

Potential features for future versions:
- Asynchronous command execution
- Command output history/logging
- Configurable element spacing
- Animation for value changes
- Click actions for secondary commands
- Image/icon element support
- Multi-line text support
- Custom color themes

### Contributors

- CMD Chart Applet Team

### Acknowledgments

Thanks to:
- Cinnamon Desktop team for the excellent applet framework
- Cairo graphics library
- All testers and users providing feedback

---

**For detailed usage instructions, see README.md**

