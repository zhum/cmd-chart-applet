#!/bin/bash
# Example demonstrating text with spaces using pipe separator
# Uses | to separate elements, allowing spaces in TXT: elements

output=""

# 1. System Load
if command -v uptime &> /dev/null; then
    load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
    load_int=$(echo "$load" | cut -d. -f1)
    
    if [ "$load_int" -lt 1 ]; then
        output+="CR:#0d0"
    elif [ "$load_int" -lt 4 ]; then
        output+="CR:#dd0"
    else
        output+="CR:#d00"
    fi
    
    # Note: Using pipes allows spaces in text!
    output+=" | TXT:Load ${load}"
    output+=" | BAR:0-5=${load}:k:o"
fi

# 2. CPU Temperature
if command -v sensors &> /dev/null; then
    temp=$(sensors 2>/dev/null | grep -i 'Core 0' | head -1 | awk '{print $3}' | tr -d '+°C')
    if [ -n "$temp" ]; then
        temp_int=$(echo "$temp" | cut -d. -f1)
        
        # Text with spaces!
        output+=" | TXT:Temp: ${temp_int}°C"
        
        if [ "$temp_int" -lt 60 ]; then
            output+=" | BAR:0-100=${temp_int}:k:g"
        elif [ "$temp_int" -lt 80 ]; then
            output+=" | BAR:0-100=${temp_int}:k:y"
        else
            output+=" | BAR:0-100=${temp_int}:k:r"
        fi
    fi
fi

# 3. Memory Usage
if command -v free &> /dev/null; then
    mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
    if [ -n "$mem_pct" ]; then
        # Natural text with spaces!
        output+=" | TXT:Mem: ${mem_pct}%"
    fi
fi

# Output the result
echo "$output"

