#!/bin/bash
# Day 15: Stop All Services

echo "🛑 Stopping Day 15 Services..."

# Kill services on all ports
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8002 | xargs kill -9 2>/dev/null
lsof -ti:8003 | xargs kill -9 2>/dev/null
lsof -ti:8004 | xargs kill -9 2>/dev/null

echo "✅ All services stopped"
