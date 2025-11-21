#!/bin/bash
# List available fonts on the system
# This helps users choose a font for the applet

echo "=== Available Fonts on Your System ==="
echo ""

if command -v fc-list &> /dev/null; then
    echo "Using fc-list to find fonts..."
    echo ""
    
    # Get unique font families, sorted
    fc-list : family | sort -u 
    
    echo ""
    echo "Showing first 50 fonts. For complete list, run: fc-list : family | sort -u"
    echo ""
    echo "Common fonts you can use:"
    echo "  - Sans (default)"
    echo "  - Serif"
    echo "  - Monospace"
    echo "  - Ubuntu"
    echo "  - DejaVu Sans"
    echo "  - Liberation Sans"
    echo "  - Noto Sans"
    echo "  - Roboto"
    echo ""
    echo "To use a font, enter its name in the 'Font family' setting."
    
else
    echo "fc-list command not found!"
    echo ""
    echo "Install fontconfig to list fonts:"
    echo "  sudo apt install fontconfig  # Debian/Ubuntu"
    echo "  sudo dnf install fontconfig  # Fedora"
    echo ""
    echo "Common fonts you can try:"
    echo "  - Sans (default)"
    echo "  - Serif"
    echo "  - Monospace"
    echo "  - Ubuntu"
    echo "  - DejaVu Sans"
fi

