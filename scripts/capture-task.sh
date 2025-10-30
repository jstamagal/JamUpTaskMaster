#!/bin/bash
# Input capture script - works with fuzzel, rofi, wofi, etc.
# Bind this to a hotkey in your compositor (Niri)

API_BASE="${JAMUP_API_BASE:-http://localhost:8000}"

# Detect which launcher is available
if command -v fuzzel &> /dev/null; then
    LAUNCHER="fuzzel --dmenu"
elif command -v rofi &> /dev/null; then
    LAUNCHER="rofi -dmenu -p 'Task:'"
elif command -v wofi &> /dev/null; then
    LAUNCHER="wofi --dmenu"
elif command -v bemenu &> /dev/null; then
    LAUNCHER="bemenu -p 'Task:'"
else
    # Fallback to terminal input if no launcher available
    echo "No launcher found. Enter task:"
    read -r input
    LAUNCHER=""
fi

# Get input from launcher
if [ -n "$LAUNCHER" ]; then
    input=$(echo "" | $LAUNCHER -p "Task:")
else
    # Already got input above
    :
fi

# If no input, exit silently
if [ -z "$input" ]; then
    exit 0
fi

# Send to API (silent, no feedback)
curl -s -X POST "$API_BASE/api/tasks/capture" \
    -H "Content-Type: application/json" \
    -d "{\"raw_input\": \"$input\"}" \
    > /dev/null 2>&1 &

# Exit immediately - don't wait for response
exit 0
