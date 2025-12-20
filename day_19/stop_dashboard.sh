#!/bin/bash

# Day 19: Stop Dashboard Server

echo "🛑 Stopping Dashboard Server..."

if lsof -Pi :8007 -sTCP:LISTEN -t >/dev/null ; then
    lsof -ti:8007 | xargs kill -9
    echo "✅ Dashboard Server stopped"
else
    echo "⚠️  Dashboard Server was not running"
fi
