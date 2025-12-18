#!/bin/bash

# Day 18: Stop Analytics API Server

echo "🛑 Stopping Analytics API Server..."

if lsof -Pi :8007 -sTCP:LISTEN -t >/dev/null ; then
    lsof -ti:8007 | xargs kill -9
    echo "✅ Analytics API Server stopped"
else
    echo "⚠️  Analytics API Server was not running"
fi
