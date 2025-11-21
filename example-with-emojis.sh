#!/bin/bash
# System monitor with emoji indicators
# Use with "Noto Color Emoji" font for best results

output=""

# 1. System Load with emoji status
if command -v uptime &> /dev/null; then
    load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
    load_int=$(echo "$load" | cut -d. -f1)
    
    # Emoji status based on load
    if [ "$load_int" -lt 1 ]; then
        load_emoji="🟢"
        color="CR:g"
    elif [ "$load_int" -lt 2 ]; then
        load_emoji="🟡"
        color="CR:y"
    else
        load_emoji="🔴"
        color="CR:r"
    fi
    
    output="$color | TXT:$load_emoji Load ${load}"
fi

# 2. CPU Temperature with thermometer emoji
if command -v sensors &> /dev/null; then
    temp=$(sensors 2>/dev/null | grep -i 'Core 0' | head -1 | awk '{print $3}' | tr -d '+°C')
    if [ -n "$temp" ]; then
        temp_int=$(echo "$temp" | cut -d. -f1)
        
        # Thermometer emoji + value
        output+=" | TXT:🌡️  ${temp_int}°C"
        
        # Bar with color based on temp
        if [ "$temp_int" -lt 60 ]; then
            output+=" | BAR:0-100=${temp_int}:k:g"
        elif [ "$temp_int" -lt 80 ]; then
            output+=" | BAR:0-100=${temp_int}:k:y"
        else
            output+=" | BAR:0-100=${temp_int}:k:r"
        fi
    fi
fi

# 3. Memory Usage with disk emoji
if command -v free &> /dev/null; then
    mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
    if [ -n "$mem_pct" ]; then
        # Memory emoji + percentage
        if [ "$mem_pct" -lt 80 ]; then
            output+=" | TXT:💾 ${mem_pct}%"
        else
            output+=" | TXT:⚠️  Mem ${mem_pct}%"
        fi
    fi
fi

# Output the result
echo "$output"

