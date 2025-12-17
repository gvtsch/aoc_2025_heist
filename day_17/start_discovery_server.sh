#!/bin/bash

# Day 17: Start Tool Discovery Server

echo "🔧 Starting Tool Discovery Server..."
echo ""

# Check if port 8006 is already in use
if lsof -Pi :8006 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8006 is already in use"
    echo "   Kill existing process? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        lsof -ti:8006 | xargs kill -9
        echo "✅ Killed existing process"
    else
        echo "❌ Aborted"
        exit 1
    fi
fi

# Start discovery server
echo "🚀 Launching Tool Discovery Server on port 8006..."
python3 day_17/tool_discovery_server.py &
DISCOVERY_PID=$!

echo "✅ Tool Discovery Server started (PID: $DISCOVERY_PID)"
echo ""
echo "📋 Endpoints:"
echo "   GET  http://localhost:8006/         - Discover tools"
echo "   GET  http://localhost:8006/health   - Health check"
echo "   GET  http://localhost:8006/stats    - Statistics"
echo "   POST http://localhost:8006/tools/register - Register new tool"
echo ""
echo "🛑 To stop: ./day_17/stop_discovery_server.sh"
echo ""
