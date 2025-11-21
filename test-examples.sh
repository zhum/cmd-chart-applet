#!/bin/bash
# Test examples for CMD Chart Applet with NEW notation

echo "=== CMD Chart Applet Test Examples (NEW NOTATION) ==="
echo ""

echo "1. Simple green circle:"
echo "CR:g"
echo ""

echo "2. Multiple colored circles:"
echo "CR:r CR:y CR:g CR:b"
echo ""

echo "3. Circle with text:"
echo "CR:g TXT:Status:OK"
echo ""

echo "4. Vertical bar (0-100, value 75):"
echo "BAR:0-100=75:r:g"
echo ""

echo "5. Bar with label:"
echo "TXT:CPU: BAR:0-100=45:k:o"
echo ""

echo "6. Combined elements:"
echo "CR:g TXT:Load: BAR:0-5=2.3:w:y TXT:OK"
echo ""

echo "7. Hex colors:"
echo "CR:#f00 CR:#0f0 CR:#00f"
echo ""

echo "8. System load example (requires uptime):"
if command -v uptime &> /dev/null; then
    load=$(uptime | awk '{print $(NF-2)}' | tr -d ',')
    echo "CR:g TXT:Load: BAR:0-5=${load}:k:o"
else
    echo "CR:y TXT:uptime_not_found"
fi
echo ""

echo "9. Memory usage example (requires free):"
if command -v free &> /dev/null; then
    mem_pct=$(free | awk 'NR==2{printf "%.0f", 100*$3/$2}')
    echo "TXT:Mem: BAR:0-100=${mem_pct}:k:b TXT:${mem_pct}%"
else
    echo "CR:y TXT:free_not_found"
fi
echo ""

echo "10. Network status example (requires ping):"
if ping -c 1 -W 1 8.8.8.8 &> /dev/null; then
    echo "CR:g TXT:Online"
else
    echo "CR:r TXT:Offline"
fi
