#!/bin/sh
# Usage: ./test_api.sh https://your-service-url
BASE="${1:-http://localhost:8000}"
echo "1. health:";   curl -s "$BASE/health"; echo
echo "2. assign:";   curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{"call_id":"test-001"}'; echo
echo "3. same call:"; curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{"call_id":"test-001"}'; echo
echo "4. no call id:"; curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{}'; echo
echo "5. no body:";    curl -s -X POST "$BASE/scenario/assign"; echo
