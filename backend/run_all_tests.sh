#!/bin/bash

# Chess Crew Test Suite Runner
# This script runs all tests for the chesscrew backend system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
export FLASK_SECRET_KEY="test-secret-key-$(date +%s)"
TEST_DIR="/home/martin/chesscrew/backend/tests"
BACKEND_DIR="/home/martin/chesscrew/backend"

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🧪 Chess Crew Test Suite Runner${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo "Test Directory: $TEST_DIR"
echo "Backend Directory: $BACKEND_DIR"
echo "Flask Secret Key: Set"
echo ""

# Function to run a test
run_test() {
    local test_name="$1"
    local test_file="$2"
    local description="$3"
    
    echo -e "${YELLOW}📋 Running: $test_name${NC}"
    echo "   Description: $description"
    echo "   File: $test_file"
    echo ""
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Change to test directory
    cd "$TEST_DIR"
    
    # Run the test and capture output
    if python "$test_file" > "/tmp/test_output_$TOTAL_TESTS.log" 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        echo -e "${RED}   Error output:${NC}"
        tail -20 "/tmp/test_output_$TOTAL_TESTS.log" | sed 's/^/   /'
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# Function to run a unittest
run_unittest() {
    local test_name="$1"
    local test_file="$2"
    local description="$3"
    
    echo -e "${YELLOW}🔬 Running: $test_name (unittest)${NC}"
    echo "   Description: $description"
    echo "   File: $test_file"
    echo ""
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Change to test directory
    cd "$TEST_DIR"
    
    # Run the unittest and capture output
    if python -m unittest "$test_file" -v > "/tmp/test_output_$TOTAL_TESTS.log" 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        echo -e "${RED}   Error output:${NC}"
        tail -20 "/tmp/test_output_$TOTAL_TESTS.log" | sed 's/^/   /'
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment is activated: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not detected. Attempting to activate...${NC}"
    if [ -f "$BACKEND_DIR/../venv/bin/activate" ]; then
        source "$BACKEND_DIR/../venv/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ Virtual environment not found. Please activate manually.${NC}"
        exit 1
    fi
fi
echo ""

# Check if we're in the right directory
if [ ! -d "$TEST_DIR" ]; then
    echo -e "${RED}❌ Test directory not found: $TEST_DIR${NC}"
    exit 1
fi

# Start testing
echo -e "${BLUE}🚀 Starting Test Execution${NC}"
echo -e "${BLUE}=========================${NC}"
echo ""

# Core Tournament Import Tests
run_test "Baseline Tournament Test" \
         "test_tournament_import_baseline.py" \
         "Tests the baseline tournament import functionality with known working data"

run_test "U10 Tournament Test" \
         "test_U10_tournament.py" \
         "Tests importing a U10 age category tournament"

run_test "U8 Tournament Test" \
         "test_Vbg_Landesmeisterschaft_2025_U8.py" \
         "Tests importing a U8 age category tournament"

run_test "U12 Tournament Test" \
         "test_Vbg_Landesmeisterschaft_2025_U12.py" \
         "Tests importing a U12 age category tournament"

# Special Format Tests
run_test "Best of 3 Tournament Test" \
         "test_Best_of_3_MU16.py" \
         "Tests importing Best of 3 format tournaments"

run_test "Team Tournament Test" \
         "test_team_tournament.py" \
         "Tests importing team tournament format"

# Specific Tournament Tests
run_test "Bodenseeopen 2025 Test" \
         "test_Bodenseeopen_2025.py" \
         "Tests importing Bodenseeopen 2025 tournament"

run_test "Rallye Lustenau 2025 U8 Test" \
         "test_Rallye_Lustenau_2025_U8.py" \
         "Tests importing Rallye Lustenau 2025 U8 tournament"

# Live Importer Tests
run_test "Live Importer 19h Test" \
         "test_live_importer_19h.py" \
         "Tests the live tournament importer functionality"

# Rating Detection Tests
run_test "Unrated Detection Test" \
         "test_unrated_detection.py" \
         "Tests detection of unrated players"

# Bugfix Tests (New)
echo -e "${BLUE}🔧 Bugfix and Regression Tests${NC}"
echo -e "${BLUE}==============================${NC}"
echo ""

run_test "Pts./TB Column Detection Bugfix" \
         "test_pts_tb_column_detection.py" \
         "Tests the fix for tournaments with both Pts. and TB columns"

run_test "Benjamin Hoefel Pkt./Wtg Bugfix" \
         "test_benjamin_hoefel_bugfix.py" \
         "Tests the fix for tournaments with Pkt. and Wtg columns (Benjamin Hoefel scenario)"

run_test "Quick Bugfix Verification" \
         "test_bugfix_verification.py" \
         "Quick verification that the Pts./TB bugfix is working"

run_test "Comprehensive Column Detection Test" \
         "test_comprehensive_column_detection.py" \
         "Comprehensive test covering all column detection scenarios and bugfixes"

# Unit Tests
# Extract module name for unittest
unittest_module=$(basename "test_regression_pts_tb_columns.py" .py)
run_unittest "Pts./TB Regression Unit Tests" \
             "$unittest_module" \
             "Unit tests for the Pts./TB column detection regression"

# Comprehensive Test (if exists)
if [ -f "$TEST_DIR/comprehensive_tournament_test.py" ]; then
    run_test "Comprehensive Tournament Test" \
             "comprehensive_tournament_test.py" \
             "Comprehensive test covering multiple tournament scenarios"
fi

# Clean up temporary files
echo -e "${BLUE}🧹 Cleaning up temporary files...${NC}"
rm -f /tmp/test_output_*.log

# Final Results
echo ""
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo -e "${BLUE}======================${NC}"
echo ""
echo "Total Tests Run: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}The chesscrew system is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS TEST(S) FAILED${NC}"
    echo -e "${RED}Please review the failed tests and fix any issues.${NC}"
    exit 1
fi
