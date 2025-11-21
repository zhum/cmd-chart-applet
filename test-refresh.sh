#!/bin/bash
# Simple test script to verify refresh is working
# Configure applet to run this script every 2-5 seconds

# Get current time
current_second=$(date +"%S")
current_minute=$(date +"%M")

# Output format: CR:color TXT:text BAR:...
# Color: green if even second, yellow if odd
if [ $((current_second % 2)) -eq 0 ]; then
    color="CR:g"
else
    color="CR:y"
fi

# Bar showing seconds: 0-60 range
bar="BAR:0-60=${current_second}:k:b"

# Text showing time
text="TXT:${current_minute}:${current_second}"

# Output combined
echo "${color} ${text} ${bar}"

