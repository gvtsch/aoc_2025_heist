#!/bin/bash

# Day 17: Stop Tool Discovery Server

echo "🛑 Stopping Tool Discovery Server..."

if lsof -Pi :8006 -sTCP:LISTEN -t >/dev/null ; then
    lsof -ti:8006 | xargs kill -9
    echo "✅ Tool Discovery Server stopped"
else
    echo "⚠️  Tool Discovery Server was not running"
fi
