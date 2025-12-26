#!/bin/bash

# Day 23: Master Start Script for All Services

echo "=" * 80)
echo "🚀 Starting Complete Heist System"
echo "="  * 80)

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and update if needed."
fi

# Create data directory
mkdir -p data

echo ""
echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🔧 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check health of all services
services=("oauth-server:8001" "memory-service:8003" "tool-discovery:8006" "analytics-api:8007" "dashboard:8008" "game-server:8009" "detection-api:8010")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "Checking $name... "

    max_retries=10
    retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ Healthy"
            break
        fi
        retry=$((retry + 1))
        sleep 2
    done

    if [ $retry -eq $max_retries ]; then
        echo "⚠️  Timeout (check logs: docker-compose logs $name)"
    fi
done

echo ""
echo "=" * 80)
echo "✅ Heist System Started Successfully!"
echo "=" * 80)
echo ""
echo "🌐 Service Endpoints:"
echo "   OAuth Server:      http://localhost:8001"
echo "   Memory Service:    http://localhost:8003"
echo "   Tool Discovery:    http://localhost:8006"
echo "   Analytics API:     http://localhost:8007"
echo "   Dashboard:         http://localhost:8008"
echo "   Game Server:       http://localhost:8009"
echo "   Detection API:     http://localhost:8010"
echo ""
echo "📊 API Documentation:"
echo "   OAuth:      http://localhost:8001/docs"
echo "   Analytics:  http://localhost:8007/docs"
echo "   Dashboard:  http://localhost:8008/docs"
echo "   Game:       http://localhost:8009/docs"
echo "   Detection:  http://localhost:8010/docs"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:        docker-compose logs -f"
echo "   View logs (one):  docker-compose logs -f [service-name]"
echo "   Stop all:         docker-compose down"
echo "   Restart:          docker-compose restart"
echo "   Stop script:      ./day_23/stop_all_services.sh"
echo ""
echo "🎮 Ready for Demo!"
echo "="  * 80)
