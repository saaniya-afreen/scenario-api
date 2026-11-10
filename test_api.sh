#!/bin/sh
# Usage: ./test_api.sh https://your-service-url
BASE="${1:-http://localhost:8000}"
echo "1. health:";   curl -s "$BASE/health"; echo
echo "2. assign:";   curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{"call_id":"test-001"}'; echo
echo "3. same call:"; curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{"call_id":"test-001"}'; echo
echo "4. no call id:"; curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{}'; echo
echo "5. no body:";    curl -s -X POST "$BASE/scenario/assign"; echo
echo "6. placeholder id (should get auto- id, different each time):"
curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{"call_id":"<call ID variable from the platform>"}'; echo
curl -s -X POST "$BASE/scenario/assign" -H "Content-Type: application/json" -d '{"call_id":"{{call_id}}"}'; echo
echo "7. forced scenario (IN-01c):"
curl -s -X POST "$BASE/scenario/assign?scenario=IN-01c" | head -c 300; echo
echo "8. unknown scenario (should be 400):"
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$BASE/scenario/assign?scenario=NOPE"
