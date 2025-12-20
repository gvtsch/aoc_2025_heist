#!/bin/bash

# Day 19: Start Dashboard Server

echo "🔧 Starting Dashboard Server..."
echo ""

# Check if port 8007 is already in use
if lsof -Pi :8007 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8007 is already in use"
    echo "   Kill existing process? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        lsof -ti:8007 | xargs kill -9
        echo "✅ Killed existing process"
    else
        echo "❌ Aborted"
        exit 1
    fi
fi

# Start Dashboard server
echo "🚀 Launching Dashboard Server on port 8007..."
cd "$(dirname "$0")"
python3 dashboard_server.py &
DASHBOARD_PID=$!

echo "✅ Dashboard Server started (PID: $DASHBOARD_PID)"
echo ""
echo "📋 Dashboard:"
echo "   🌐 http://localhost:8007"
echo "   📊 http://localhost:8007/docs - API Documentation"
echo ""
echo "📋 Key Features:"
echo "   • Real-time session monitoring"
echo "   • Agent activity charts"
echo "   • Tool usage statistics"
echo "   • WebSocket live updates"
echo "   • Interactive mole detection"
echo ""
echo "🛑 To stop: ./day_19/stop_dashboard.sh"
echo ""
