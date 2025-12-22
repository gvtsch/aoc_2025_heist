#!/bin/bash

# Day 20: Start Interactive Dashboard Server

echo "🔧 Starting Interactive Dashboard Server..."
echo ""

# Check if port 8008 is already in use
if lsof -Pi :8008 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8008 is already in use"
    echo "   Kill existing process? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        lsof -ti:8008 | xargs kill -9
        echo "✅ Killed existing process"
    else
        echo "❌ Aborted"
        exit 1
    fi
fi

# Start Interactive Dashboard server
echo "🚀 Launching Interactive Dashboard Server on port 8008..."
python3 day_20/interactive_dashboard_server.py &
DASHBOARD_PID=$!

echo "✅ Interactive Dashboard Server started (PID: $DASHBOARD_PID)"
echo ""
echo "📋 Interactive Dashboard:"
echo "   🌐 http://localhost:8008"
echo "   📊 http://localhost:8008/docs - API Documentation"
echo ""
echo "🎮 New Interactive Features:"
echo "   • ⏸️  Pause/Resume heist control"
echo "   • 📡 Send commands to agents"
echo "   • 🏦 Interactive bank layout"
echo "   • 🕵️  Enhanced mole detection"
echo "   • 📋 Real-time activity log"
echo "   • 🔄 Live status updates"
echo ""
echo "🛑 To stop: ./day_20/stop_interactive_dashboard.sh"
echo ""
