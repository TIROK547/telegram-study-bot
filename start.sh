#!/bin/bash

# Study Bot Auto-Restart Script
# This script will continuously run the bot and restart it if it stops


echo "🤖 Starting Study Bot with auto-restart..."
echo "📝 Press Ctrl+C to stop the script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Counter for restart attempts
RESTART_COUNT=0

# Infinite loop to keep the bot running
while true; do
    echo ""
    echo "▶️  Starting bot... (Restart count: $RESTART_COUNT)"
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi

    # Run the bot
    python3 bot.py

    # Capture exit code
    EXIT_CODE=$?

    # Increment restart counter
    RESTART_COUNT=$((RESTART_COUNT + 1))

    echo ""
    echo "⚠️  Bot stopped with exit code: $EXIT_CODE"
    echo "🔄 Waiting 5 seconds before restart..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Wait before restarting (prevents rapid restart loops)
    sleep 5
done
