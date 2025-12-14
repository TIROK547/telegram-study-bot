#!/bin/bash

# Study Bot Startup Script
# This script runs both the Telegram bot and the web API server

echo "🚀 Starting Study Bot System..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one with: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your BOT_TOKEN"
fi

# Install/update requirements
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Start both services in the background
echo ""
echo "🤖 Starting Telegram Bot..."
python bot.py &
BOT_PID=$!

echo "🌐 Starting Web API Server..."
python api.py &
API_PID=$!

echo ""
echo "✅ System started successfully!"
echo ""
echo "📊 Web Panel: http://localhost:8000"
echo "🤖 Bot PID: $BOT_PID"
echo "🌐 API PID: $API_PID"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to stop all services on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BOT_PID $API_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Wait for processes
wait
