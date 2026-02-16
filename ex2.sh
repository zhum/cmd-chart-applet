#!/bin/bash
# Example: 2-line chart mode
# Format: 2L| top line elements || bottom line elements
# Bars in 2-line mode are horizontal

# Get system information
load=$(uptime | awk '{print $(NF-2)}' | tr -d ',' 2>/dev/null || echo "0")
load_int=$(echo "$load" | cut -d. -f1)

# CPU temperature
temp=$(sensors 2>/dev/null | grep -i 'Tctl' | head -1 | awk '{print $2}' | tr -d '+°C' | cut -d. -f1)
if [ -z "$temp" ]; then temp="0"; fi

# # Memory usage
# mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')

# Disk usage
disk_pct=$(df -h / | awk 'NR==2{gsub(/%/,"",$5); print $5}')

# Color for load indicator
if [ "$load_int" -lt 1 ]; then
    load_color="CR:g"
elif [ "$load_int" -lt 2 ]; then
    load_color="CR:y"
else
    load_color="CR:r"
fi

# Color for temperature indicator
if [ "$temp" -lt 50 ]; then
    temp_color="g"
elif [ "$temp" -lt 70 ]; then
    temp_color="o"
else
    temp_color="r"
fi

# TOP LINE: System load and CPU temperature
top_line="$load_color | TXT:Load | BAR:0-5=${load}:b:o | CR:$temp_color | TXTC:$temp_color:${temp}°C | BAR:0-100=${temp}:k:r"

# BOTTOM LINE: Memory and disk usage
bottom_line="TXT:Disk | HBAR:0-100=${disk_pct}:k:y | TXT:${disk_pct}%"

# Output in 2-line mode format
echo "${top_line}||${bottom_line}"
