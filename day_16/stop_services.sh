#!/bin/bash
# Day 16: Stop All Services

echo "🛑 Stopping Day 16 Services..."

# Kill services on all ports
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "   ✓ OAuth Service stopped (Port 8001)"
lsof -ti:8002 | xargs kill -9 2>/dev/null && echo "   ✓ Calculator stopped (Port 8002)"
lsof -ti:8003 | xargs kill -9 2>/dev/null && echo "   ✓ File Reader stopped (Port 8003)"
lsof -ti:8004 | xargs kill -9 2>/dev/null && echo "   ✓ Database stopped (Port 8004)"
lsof -ti:8005 | xargs kill -9 2>/dev/null && echo "   ✓ Memory Service stopped (Port 8005)"

echo ""
echo "✅ All services stopped"
