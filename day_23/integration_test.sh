#!/bin/bash

# Day 23: Integration Testing Script
# Tests all services end-to-end

echo "=" * 80)
echo "🧪 Integration Testing - Complete Heist System"
echo "=" * 80)
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((passed++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $response)"
        ((failed++))
    fi
}

echo "1️⃣  Service Health Checks"
echo "─────────────────────────"
test_endpoint "OAuth Server Health" "http://localhost:8001/health"
test_endpoint "Memory Service Health" "http://localhost:8003/health"
test_endpoint "Tool Discovery Health" "http://localhost:8006/health"
test_endpoint "Analytics API Health" "http://localhost:8007/health"
test_endpoint "Dashboard Health" "http://localhost:8008/health"
test_endpoint "Game Server Health" "http://localhost:8009/health"
test_endpoint "Detection API Health" "http://localhost:8010/health"

echo ""
echo "2️⃣  OAuth Flow"
echo "─────────────────────────"
# Test token generation
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8001/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass&scope=read:memory+write:memory")

if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ PASS${NC} OAuth token generation"
    ((passed++))

    # Extract token
    TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

    if [ ! -z "$TOKEN" ]; then
        echo -e "${GREEN}✓ PASS${NC} Token extraction"
        ((passed++))
    else
        echo -e "${RED}✗ FAIL${NC} Token extraction"
        ((failed++))
    fi
else
    echo -e "${RED}✗ FAIL${NC} OAuth token generation"
    ((failed++))
    TOKEN=""
fi

echo ""
echo "3️⃣  Analytics API"
echo "─────────────────────────"
test_endpoint "List Sessions" "http://localhost:8007/api/sessions"
test_endpoint "Summary Stats" "http://localhost:8007/api/stats/summary"
test_endpoint "Tool Stats" "http://localhost:8007/api/tool-stats"

echo ""
echo "4️⃣  Tool Discovery"
echo "─────────────────────────"
test_endpoint "Discover Tools" "http://localhost:8006/"
test_endpoint "Tool Registry" "http://localhost:8006/tools"

echo ""
echo "5️⃣  Game System"
echo "─────────────────────────"
test_endpoint "Game Stats" "http://localhost:8009/api/game/stats"

echo ""
echo "6️⃣  Detection API"
echo "─────────────────────────"
test_endpoint "Detection Info" "http://localhost:8010/"

echo ""
echo "=" * 80)
echo "📊 Test Results"
echo "=" * 80)
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$failed${NC}"
echo -e "Total:  $((passed + failed))"

if [ $failed -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo "🎉 System is production-ready!"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed${NC}"
    echo "📋 Check logs: docker-compose logs"
    exit 1
fi
