#!/bin/bash

# Example: Status monitor using colored text
# Demonstrates practical use of TXTC for system status

# Get system load
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
LOAD_INT=$(echo "$LOAD" | cut -d'.' -f1)

# Determine load status color
if [ "$LOAD_INT" -lt 2 ]; then
    LOAD_COLOR="g"  # Green - OK
elif [ "$LOAD_INT" -lt 4 ]; then
    LOAD_COLOR="o"  # Orange - Warning
else
    LOAD_COLOR="r"  # Red - High
fi

# Get memory usage percentage
MEM_PERCENT=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100}')

# Determine memory status color
if [ "$MEM_PERCENT" -lt 70 ]; then
    MEM_COLOR="g"  # Green - OK
elif [ "$MEM_PERCENT" -lt 85 ]; then
    MEM_COLOR="o"  # Orange - Warning
else
    MEM_COLOR="r"  # Red - High
fi

# Get disk usage
DISK_PERCENT=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')

# Determine disk status color
if [ "$DISK_PERCENT" -lt 80 ]; then
    DISK_COLOR="g"  # Green - OK
elif [ "$DISK_PERCENT" -lt 90 ]; then
    DISK_COLOR="o"  # Orange - Warning
else
    DISK_COLOR="r"  # Red - High
fi

# Output with colored status indicators (using space separator for cleaner syntax)
echo "TXTC:${LOAD_COLOR} Load:${LOAD} | TXTC:${MEM_COLOR} Mem:${MEM_PERCENT}% | TXTC:${DISK_COLOR} Disk:${DISK_PERCENT}%"

