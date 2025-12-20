#!/bin/bash

# Day 19: Run Heist Session Script
# Wrapper for run_heist.py with optional config parameter

# Default values
CONFIG="agents_config.yaml"  # Local config in day_19/
TURNS=5
DISCOVERY_URL="http://localhost:8006"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG="$2"
            shift 2
            ;;
        -t|--turns)
            TURNS="$2"
            shift 2
            ;;
        -d|--discovery-url)
            DISCOVERY_URL="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --config PATH        Path to config file (default: day_19/agents_config.yaml)"
            echo "  -t, --turns NUM          Number of turns (default: 5)"
            echo "  -d, --discovery-url URL  Discovery server URL (default: http://localhost:8006)"
            echo "  -v, --verbose            Enable verbose output"
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Use default config"
            echo "  $0 -c my_config.yaml                  # Use custom config"
            echo "  $0 -t 10 -v                           # Run 10 turns with verbose output"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Run the heist
echo "🎯 Running heist session..."
echo ""

cd "$(dirname "$0")"
python3 run_heist.py --config "$CONFIG" --turns "$TURNS" --discovery-url "$DISCOVERY_URL" $VERBOSE
