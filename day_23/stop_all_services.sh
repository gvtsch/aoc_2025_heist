#!/bin/bash

# Day 23: Master Stop Script for All Services

echo "🛑 Stopping Complete Heist System..."
echo ""

docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "💾 Data preserved in ./data directory"
echo "🔄 To restart: ./day_23/start_all_services.sh"
