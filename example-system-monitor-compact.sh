#!/bin/bash
# Compact system monitor script for CMD Chart Applet
# This script shows only essential info in minimal space
#
# NOTE: This produces 3 elements (circle, text, bar)
# Recommended chart width: 100 pixels minimum

output=""

# 1. System Load indicator (color coded)
if command -v uptime &> /dev/null; then
    load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
    load_int=$(echo "$load" | cut -d. -f1)
    
    if [ "$load_int" -lt 1 ]; then
        output+="CR:g"
    elif [ "$load_int" -lt 2 ]; then
        output+="CR:y"
    else
        output+="CR:r"
    fi
fi

# 2. CPU Temperature (just the value, no bar)
if command -v sensors &> /dev/null; then
    temp=$(sensors 2>/dev/null | grep -i 'Core 0' | head -1 | awk '{print $3}' | tr -d '+°C')
    if [ -n "$temp" ]; then
        temp_int=$(echo "$temp" | cut -d. -f1)
        output+=" TXT:${temp_int}°"
    fi
fi

# 3. Memory Usage (bar only)
if command -v free &> /dev/null; then
    mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
    if [ -n "$mem_pct" ]; then
        # Color based on usage
        if [ "$mem_pct" -lt 70 ]; then
            output+=" BAR:0-100=${mem_pct}:k:g"
        elif [ "$mem_pct" -lt 85 ]; then
            output+=" BAR:0-100=${mem_pct}:k:y"
        else
            output+=" BAR:0-100=${mem_pct}:k:r"
        fi
    fi
fi

# Output the result
echo "$output"

