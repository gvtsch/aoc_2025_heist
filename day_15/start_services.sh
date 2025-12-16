#!/bin/bash
# Day 15: Start All Services
# Starts OAuth and all Tool Services in background

echo "🚀 Starting Day 15 Services..."

# Kill any existing services on these ports
echo "🧹 Cleaning up existing services..."
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
lsof -ti:8004 | xargs kill -9 2>/dev/null

sleep 1

# Start OAuth Service (Port 8001)
echo "🔐 Starting OAuth Service (Port 8001)..."
python day_15/oauth_service.py > /tmp/oauth_service.log 2>&1 &
OAUTH_PID=$!

sleep 1

# Start Calculator Service (Port 8002)
echo "🧮 Starting Calculator Service (Port 8002)..."
python day_15/tool_services.py calculator > /tmp/calculator_service.log 2>&1 &
CALC_PID=$!

sleep 1

# Start File Reader Service (Port 8003)
echo "📄 Starting File Reader Service (Port 8003)..."
python day_15/tool_services.py file_reader > /tmp/file_reader_service.log 2>&1 &
FILE_PID=$!

sleep 1

# Start Database Service (Port 8004)
echo "🗄️  Starting Database Service (Port 8004)..."
python day_15/tool_services.py database > /tmp/database_service.log 2>&1 &
DB_PID=$!

sleep 2

# Check if services are running
echo ""
echo "✅ Services Started:"
echo "   OAuth Service:     http://localhost:8001 (PID: $OAUTH_PID)"
echo "   Calculator:        http://localhost:8002 (PID: $CALC_PID)"
echo "   File Reader:       http://localhost:8003 (PID: $FILE_PID)"
echo "   Database Query:    http://localhost:8004 (PID: $DB_PID)"
echo ""
echo "📋 Logs in /tmp/*_service.log"
echo "🛑 To stop: ./day_15/stop_services.sh"
echo ""
echo "🎯 Ready to run: python day_15/dynamic_agent_system.py"
