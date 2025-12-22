#!/bin/bash

# Day 20: Stop Interactive Dashboard Server

echo "🛑 Stopping Interactive Dashboard Server..."

if lsof -Pi :8008 -sTCP:LISTEN -t >/dev/null ; then
    lsof -ti:8008 | xargs kill -9
    echo "✅ Interactive Dashboard Server stopped"
else
    echo "⚠️  Interactive Dashboard Server was not running"
fi
