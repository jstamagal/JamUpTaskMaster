#!/bin/bash
# Automated API Test Suite for JamUpTaskMaster

set -e

API_BASE="http://localhost:8000"
FAILED=0
PASSED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 JamUpTaskMaster API Test Suite"
echo "=================================="
echo ""

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_BASE$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_BASE$endpoint" \
            -H "Content-Type: application/json" -d "$data")
    fi

    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status" -eq "$expected_status" ]; then
        pass "$name (HTTP $status)"
        echo "$body" > /tmp/last_response.json
        return 0
    else
        fail "$name (expected $expected_status, got $status)"
        echo "Response: $body"
        return 1
    fi
}

echo "1. Testing Health Endpoint"
echo "--------------------------"
test_endpoint "Health check" "GET" "/health" "" 200
echo ""

echo "2. Testing Task Capture"
echo "----------------------"
test_endpoint "Capture task" "POST" "/api/tasks/capture" '{"raw_input":"automated test task"}' 200
TASK_ID=$(cat /tmp/last_response.json | jq -r '.id')
echo "   Created task ID: $TASK_ID"
echo ""

echo "3. Testing Task Retrieval"
echo "------------------------"
test_endpoint "List tasks" "GET" "/api/tasks?status=captured&limit=50" "" 200
test_endpoint "Get specific task" "GET" "/api/tasks/$TASK_ID" "" 200
echo ""

echo "4. Testing Priority Management"
echo "------------------------------"
test_endpoint "Update priority" "PATCH" "/api/tasks/$TASK_ID" '{"priority_score":0.9}' 200
test_endpoint "Pin task" "PATCH" "/api/tasks/$TASK_ID" '{"pinned":true}' 200

# Verify pinned field
PINNED=$(cat /tmp/last_response.json | jq -r '.pinned')
if [ "$PINNED" = "true" ]; then
    pass "Pinned field set correctly"
else
    fail "Pinned field not set (got: $PINNED)"
fi
echo ""

echo "5. Testing Status Updates"
echo "------------------------"
test_endpoint "Mark as done" "PATCH" "/api/tasks/$TASK_ID" '{"status":"done"}' 200
test_endpoint "Put off" "PATCH" "/api/tasks/$TASK_ID" '{"status":"put_off"}' 200
test_endpoint "Fuck off" "PATCH" "/api/tasks/$TASK_ID" '{"status":"fuck_off"}' 200
echo ""

echo "6. Testing Chat Endpoint"
echo "-----------------------"
test_endpoint "Chat without context" "POST" "/chat" '{"message":"test","include_context":false}' 200
# Note: Chat with gpt-oss will take time and might fail if Ollama isn't running
# Response check
RESPONSE=$(cat /tmp/last_response.json | jq -r '.response')
if [ ! -z "$RESPONSE" ] && [ "$RESPONSE" != "null" ]; then
    pass "Chat response received"
else
    fail "Chat response empty or null"
fi
echo ""

echo "7. Testing Settings Endpoint"
echo "----------------------------"
test_endpoint "Get settings" "GET" "/settings" "" 200
test_endpoint "Update settings" "PATCH" "/settings" '{"display_count":15,"zero_indexed":true}' 200
echo ""

echo "8. Testing Stats"
echo "---------------"
test_endpoint "Get stats" "GET" "/api/tasks/stats/overview" "" 200
echo ""

echo "9. Testing Suggestions"
echo "---------------------"
test_endpoint "Get suggestions" "GET" "/api/tasks/suggestions" "" 200
echo ""

echo "10. Cleanup"
echo "----------"
test_endpoint "Delete test task" "DELETE" "/api/tasks/$TASK_ID" "" 200
echo ""

echo "=================================="
echo "Test Results:"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "=================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
