#!/bin/bash
# Example system monitor script for CMD Chart Applet
# This script shows system load, CPU temperature, and memory usage
#
# NOTE: This produces 5 elements (circle, 2 bars, 2 texts)
# Recommended chart width: 200 pixels minimum
# Right-click applet → Configure → Chart width: 200+

output=""

# 1. System Load (green if < 1.0, yellow if < 2.0, violet if >= 2.0)
if command -v uptime &> /dev/null; then
    load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
    load_int=$(echo "$load" | cut -d. -f1)
    
    if [ "$load_int" -lt 1 ]; then
        output+="CR:g"
    elif [ "$load_int" -lt 2 ]; then
        output+="CR:y"
    else
        output+="CR:v"
    fi
    output+=" BAR:0-5=${load}:k:o"
fi

# 2. CPU Temperature (if available)
if command -v sensors &> /dev/null; then
    temp=$(sensors 2>/dev/null | grep -i 'Core 0' | head -1 | awk '{print $3}' | tr -d '+°C')
    if [ -n "$temp" ]; then
        temp_int=$(echo "$temp" | cut -d. -f1)
        output+=" TXT:${temp_int}°C"
        
        # Temperature bar: 0-100°C, changes color based on temp
        if [ "$temp_int" -lt 60 ]; then
            output+=" BAR:0-100=${temp_int}:k:g"
        elif [ "$temp_int" -lt 80 ]; then
            output+=" BAR:0-100=${temp_int}:k:y"
        else
            output+=" BAR:0-100=${temp_int}:k:r"
        fi
    fi
fi

# 3. Memory Usage
if command -v free &> /dev/null; then
    mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
    if [ -n "$mem_pct" ]; then
        output+=" TXT:M${mem_pct}%"
    fi
fi

# Output the result
echo "$output"

