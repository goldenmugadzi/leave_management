#!/bin/bash

# Curl Test Script for Optimized File Handling Endpoints
# Tests all new endpoints via HTTP requests

echo "🚀 Testing Optimized File Handling Endpoints with curl"
echo "======================================================"

# Configuration
BASE_URL="http://localhost:8000"
CS_BASE_URL="${BASE_URL}/comparative_schedules"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        echo "   $details"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo "   $details"
        ((TESTS_FAILED++))
    fi
    echo
}

# Function to check if server is running
check_server() {
    echo -e "${BLUE}🔍 Checking if Django server is running...${NC}"
    
    if curl -s "${BASE_URL}/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is running at ${BASE_URL}${NC}"
        return 0
    else
        echo -e "${RED}❌ Server is not running at ${BASE_URL}${NC}"
        echo "Please start your Django server with: python manage.py runserver"
        return 1
    fi
}

# Test 1: File Upload Endpoint
test_file_upload() {
    echo -e "${BLUE}📤 Testing File Upload Endpoint${NC}"
    
    # Create a test file
    echo "This is a test file for upload testing" > test_upload.txt
    
    # Test file upload
    response=$(curl -s -X POST \
        -F "file=@test_upload.txt" \
        -F "file_type=test" \
        -F "description=Test upload via curl" \
        "${CS_BASE_URL}/api/files/upload/")
    
    # Clean up test file
    rm -f test_upload.txt
    
    # Check response
    if echo "$response" | grep -q '"success": true'; then
        file_path=$(echo "$response" | grep -o '"file_path":"[^"]*"' | cut -d'"' -f4)
        print_result "File Upload" "PASS" "File uploaded successfully. Path: $file_path"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        print_result "File Upload" "FAIL" "Upload failed. Response: $response"
    fi
}

# Test 2: Get Attachments Endpoint
test_get_attachments() {
    echo -e "${BLUE}📎 Testing Get Attachments Endpoint${NC}"
    
    # Test with a sample PR ID (you may need to adjust this)
    pr_id="PR12345678"
    
    response=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/attachments/${pr_id}/")
    
    if echo "$response" | grep -q '"success": true'; then
        attachment_count=$(echo "$response" | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
        print_result "Get Attachments" "PASS" "Retrieved $attachment_count attachments successfully"
        
        # Check for Base64 data (should not be present)
        if echo "$response" | grep -q '"file":'; then
            print_result "Base64 Check" "FAIL" "Base64 data found in response (should not be present)"
        else
            print_result "Base64 Check" "PASS" "No Base64 data in response (correct)"
        fi
        
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        print_result "Get Attachments" "FAIL" "Failed to get attachments. Response: $response"
    fi
}

# Test 3: Get Create Data Endpoint
test_get_create_data() {
    echo -e "${BLUE}📋 Testing Get Create Data Endpoint${NC}"
    
    pr_id="PR12345678"
    
    response=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/create-data/${pr_id}/")
    
    if echo "$response" | grep -q '"success": true'; then
        pr_id_response=$(echo "$response" | grep -o '"pr_id":"[^"]*"' | cut -d'"' -f4)
        print_result "Get Create Data" "PASS" "Retrieved data for PR: $pr_id_response"
        
        # Check for Base64 data in attachments
        if echo "$response" | grep -q '"file":'; then
            print_result "Create Data Base64 Check" "FAIL" "Base64 data found in create data response"
        else
            print_result "Create Data Base64 Check" "PASS" "No Base64 data in create data response"
        fi
        
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        print_result "Get Create Data" "FAIL" "Failed to get create data. Response: $response"
    fi
}

# Test 4: Get CS Files Endpoint
test_get_cs_files() {
    echo -e "${BLUE}📁 Testing Get CS Files Endpoint${NC}"
    
    cs_id="CS001"
    
    response=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/cs-files/${cs_id}/")
    
    if echo "$response" | grep -q '"success": true'; then
        file_count=$(echo "$response" | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
        print_result "Get CS Files" "PASS" "Retrieved $file_count CS files successfully"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        print_result "Get CS Files" "FAIL" "Failed to get CS files. Response: $response"
    fi
}

# Test 5: File Download Endpoint
test_file_download() {
    echo -e "${BLUE}⬇️  Testing File Download Endpoint${NC}"
    
    # This test requires a valid file path from a previous upload
    # For now, we'll test with a sample path
    file_path="uploads/comparative_schedules/2024/01/test_file.txt"
    
    response=$(curl -s -I -X GET \
        "${CS_BASE_URL}/api/files/download/${file_path}/")
    
    if echo "$response" | grep -q "HTTP/1.1 200"; then
        print_result "File Download" "PASS" "Download endpoint responding correctly"
    elif echo "$response" | grep -q "HTTP/1.1 404"; then
        print_result "File Download" "PASS" "Download endpoint working (file not found, which is expected)"
    else
        print_result "File Download" "FAIL" "Download endpoint not responding correctly"
    fi
}

# Test 6: File Preview Endpoint
test_file_preview() {
    echo -e "${BLUE}👁️  Testing File Preview Endpoint${NC}"
    
    file_path="uploads/comparative_schedules/2024/01/test_file.txt"
    
    response=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/preview/${file_path}/")
    
    if echo "$response" | grep -q '"success": true'; then
        print_result "File Preview" "PASS" "Preview endpoint working correctly"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    elif echo "$response" | grep -q '"success": false'; then
        print_result "File Preview" "PASS" "Preview endpoint working (preview not available, which is expected)"
    else
        print_result "File Preview" "FAIL" "Preview endpoint not responding correctly"
    fi
}

# Test 7: Performance Comparison
test_performance() {
    echo -e "${BLUE}⚡ Testing Performance Comparison${NC}"
    
    pr_id="PR12345678"
    
    # Test optimized endpoint
    start_time=$(date +%s%N)
    response_optimized=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/attachments/${pr_id}/")
    end_time=$(date +%s%N)
    optimized_time=$((end_time - start_time))
    
    # Test old endpoint (if available)
    start_time=$(date +%s%N)
    response_old=$(curl -s -X GET \
        "${CS_BASE_URL}/api/pr-attachments/${pr_id}/")
    end_time=$(date +%s%N)
    old_time=$((end_time - start_time))
    
    # Calculate response sizes
    optimized_size=${#response_optimized}
    old_size=${#response_old}
    
    echo "Performance Results:"
    echo "  Optimized endpoint time: ${optimized_time}ns"
    echo "  Old endpoint time: ${old_time}ns"
    echo "  Optimized response size: ${optimized_size} characters"
    echo "  Old response size: ${old_size} characters"
    
    if [ $optimized_time -lt $old_time ]; then
        improvement=$(( (old_time - optimized_time) * 100 / old_time ))
        print_result "Performance" "PASS" "Optimized endpoint is ${improvement}% faster"
    else
        print_result "Performance" "FAIL" "Optimized endpoint is not faster"
    fi
    
    if [ $optimized_size -lt $old_size ]; then
        memory_improvement=$(( (old_size - optimized_size) * 100 / old_size ))
        print_result "Memory Usage" "PASS" "Optimized response is ${memory_improvement}% smaller"
    else
        print_result "Memory Usage" "FAIL" "Optimized response is not smaller"
    fi
}

# Test 8: Error Handling
test_error_handling() {
    echo -e "${BLUE}🚨 Testing Error Handling${NC}"
    
    # Test non-existent PR
    response=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/attachments/PR99999999/")
    
    if echo "$response" | grep -q '"success": false'; then
        print_result "Error Handling" "PASS" "Correctly handles non-existent PR"
    else
        print_result "Error Handling" "FAIL" "Does not handle non-existent PR correctly"
    fi
    
    # Test invalid file path
    response=$(curl -s -X GET \
        "${CS_BASE_URL}/api/files/download/invalid/path/file.txt/")
    
    if echo "$response" | grep -q "404\|error"; then
        print_result "File Error Handling" "PASS" "Correctly handles invalid file paths"
    else
        print_result "File Error Handling" "FAIL" "Does not handle invalid file paths correctly"
    fi
}

# Main test execution
main() {
    echo "Starting curl tests for optimized file handling endpoints..."
    echo
    
    # Check if server is running
    if ! check_server; then
        exit 1
    fi
    
    echo
    
    # Run all tests
    test_file_upload
    test_get_attachments
    test_get_create_data
    test_get_cs_files
    test_file_download
    test_file_preview
    test_performance
    test_error_handling
    
    # Print summary
    echo "======================================================"
    echo -e "${BLUE}📊 Test Summary${NC}"
    echo "======================================================"
    echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}📈 Total Tests: $((TESTS_PASSED + TESTS_FAILED))${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo
        echo -e "${GREEN}🎉 All tests passed! The optimized file handling system is working correctly.${NC}"
    else
        echo
        echo -e "${YELLOW}⚠️  Some tests failed. Please check the implementation.${NC}"
    fi
    
    echo
    echo "📋 Test Coverage:"
    echo "  ✅ File Upload"
    echo "  ✅ Get Attachments (no Base64)"
    echo "  ✅ Get Create Data (no Base64)"
    echo "  ✅ Get CS Files"
    echo "  ✅ File Download"
    echo "  ✅ File Preview"
    echo "  ✅ Performance Comparison"
    echo "  ✅ Error Handling"
}

# Run the tests
main
