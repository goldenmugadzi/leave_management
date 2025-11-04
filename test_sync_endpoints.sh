#!/bin/bash
# Manual Testing Script for Inspection Sync APIs
# Usage: ./test_sync_endpoints.sh <BASE_URL> <JWT_TOKEN>
#
# Example:
#   ./test_sync_endpoints.sh http://localhost:8000 eyJ0eXAiOiJKV1QiLCJhbGc...

BASE_URL="${1:-http://localhost:8000}"
TOKEN="$2"

if [ -z "$TOKEN" ]; then
    echo "Error: JWT token required"
    echo "Usage: $0 <BASE_URL> <JWT_TOKEN>"
    echo ""
    echo "To get a token, first login:"
    echo "curl -X POST ${BASE_URL}/api/auth/token/ \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"username\":\"your_username\",\"password\":\"your_password\"}'"
    exit 1
fi

echo "=== Testing Inspection Sync API Endpoints ==="
echo "Base URL: $BASE_URL"
echo "Using JWT Token: ${TOKEN:0:20}..."
echo ""

# Test 1: Download Inspection Batch
echo "1. Testing E117 Inspection Download Endpoint"
echo "   GET ${BASE_URL}/inspections/api/sync/download-inspection-batch/"
curl -X GET "${BASE_URL}/inspections/api/sync/download-inspection-batch/?limit=5" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | python3 -m json.tool 2>/dev/null || echo "Response received"
echo ""
echo "---"
echo ""

# Test 2: Download E1 Defects
echo "2. Testing E1 Defect Reports Download Endpoint"
echo "   GET ${BASE_URL}/inspections/api/sync/defects/e1/"
curl -X GET "${BASE_URL}/inspections/api/sync/defects/e1/?limit=10" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | python3 -m json.tool 2>/dev/null || echo "Response received"
echo ""
echo "---"
echo ""

# Test 3: Download E6 Certificates
echo "3. Testing E6 Certificates Download Endpoint"
echo "   GET ${BASE_URL}/inspections/api/sync/certificates/e6/"
curl -X GET "${BASE_URL}/inspections/api/sync/certificates/e6/?limit=10" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | python3 -m json.tool 2>/dev/null || echo "Response received"
echo ""
echo "---"
echo ""

# Test 4: Download General Defects
echo "4. Testing General Defects Download Endpoint"
echo "   GET ${BASE_URL}/inspections/api/sync/defects/"
curl -X GET "${BASE_URL}/inspections/api/sync/defects/?limit=10" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | python3 -m json.tool 2>/dev/null || echo "Response received"
echo ""
echo "---"
echo ""

# Test 5: Test without authentication (should fail with 401)
echo "5. Testing Authentication Requirement (should fail with 401)"
echo "   GET ${BASE_URL}/inspections/api/sync/download-inspection-batch/ (no auth)"
curl -X GET "${BASE_URL}/inspections/api/sync/download-inspection-batch/" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | python3 -m json.tool 2>/dev/null || echo "Response received"
echo ""
echo "---"
echo ""

# Test 6: Test incremental sync with modified_after
echo "6. Testing Incremental Sync with modified_after"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" -d "1 hour ago")
echo "   GET ${BASE_URL}/inspections/api/sync/download-inspection-batch/?modified_after=${TIMESTAMP}"
curl -X GET "${BASE_URL}/inspections/api/sync/download-inspection-batch/?modified_after=${TIMESTAMP}&limit=5" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | python3 -m json.tool 2>/dev/null || echo "Response received"
echo ""
echo "---"
echo ""

echo "=== Testing Complete ==="
echo ""
echo "Expected Results:"
echo "  - Tests 1-4, 6: HTTP 200 with JSON response containing 'success': true"
echo "  - Test 5: HTTP 401 with authentication error"
echo ""
echo "Check CORS headers with:"
echo "  curl -I -H 'Origin: http://localhost:3000' ${BASE_URL}/inspections/api/sync/download-inspection-batch/"

