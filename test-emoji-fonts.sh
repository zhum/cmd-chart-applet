#!/bin/bash
# Test which fonts can display emojis
# This script tests common fonts with emoji characters

echo "=== Testing Fonts for Emoji Support ==="
echo ""

# Emoji test characters
EMOJI_TEST="✅ ❌ 🔴 🟢 🟡 🔵 ⚠️ 📊 💾 🌡️"

echo "Test emojis: $EMOJI_TEST"
echo ""

# Check if we can use pango to test fonts
if command -v pango-view &> /dev/null; then
    echo "Using pango-view to test fonts..."
    echo ""
    
    # Test a few common fonts
    FONTS=(
        "Sans"
        "Noto Sans"
        "Noto Color Emoji"
        "Noto Emoji"
        "Symbola"
        "DejaVu Sans"
        "Ubuntu"
        "Segoe UI Emoji"
        "Apple Color Emoji"
        "Twemoji"
        "EmojiOne"
    )
    
    for font in "${FONTS[@]}"; do
        # Check if font exists
        if fc-list | grep -qi "$font"; then
            echo "✓ Font '$font' is installed"
            # Note: In GUI, test by setting this font in applet
        else
            echo "✗ Font '$font' not found"
        fi
    done
    
else
    echo "pango-view not available, using fc-list to find emoji fonts..."
    echo ""
fi

echo ""
echo "=== Emoji-Capable Fonts on Your System ==="
echo ""

# Find fonts that specifically support emoji
fc-list | grep -i -E "emoji|symbol|noto.*color" | cut -d: -f2 | cut -d, -f1 | sort -u

echo ""
echo "=== How to Test ==="
echo "1. Note the font names above"
echo "2. Configure applet with: echo 'CR:g | TXT:Test ✅ ❌ 🟢'"
echo "3. Change font in settings to each emoji font"
echo "4. See which one displays emojis correctly"
echo ""
echo "=== Recommended Emoji Fonts ==="
echo "  - Noto Color Emoji (best, full color)"
echo "  - Noto Emoji (black & white)"
echo "  - Symbola (comprehensive symbol coverage)"
echo "  - Twemoji (Twitter emoji style)"
echo ""
echo "=== Install Emoji Fonts ==="
echo "If you don't have emoji fonts installed:"
echo "  sudo apt install fonts-noto-color-emoji    # Ubuntu/Debian"
echo "  sudo dnf install google-noto-emoji-fonts   # Fedora"
echo ""

