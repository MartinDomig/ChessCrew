#!/bin/bash

# Chess Crew Quick Test Runner
# Runs essential tests for rapid feedback during development

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

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}⚡ Chess Crew Quick Test Runner${NC}"
echo -e "${BLUE}==============================${NC}"
echo ""

# Function to run a test quickly
run_quick_test() {
    local test_name="$1"
    local test_file="$2"
    
    echo -e "${YELLOW}🔄 $test_name...${NC}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    cd "$TEST_DIR"
    
    if python "$test_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ $test_name${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -f "/home/martin/chesscrew/venv/bin/activate" ]; then
        source "/home/martin/chesscrew/venv/bin/activate"
    fi
fi

echo "Running essential tests..."
echo ""

# Essential tests only
run_quick_test "Baseline Tournament Import" "test_tournament_import_baseline.py"
run_quick_test "U10 Tournament Import" "test_U10_tournament.py"
run_quick_test "Pts./TB Bugfix Verification" "test_bugfix_verification.py"
run_quick_test "Pts./TB Column Detection" "test_pts_tb_column_detection.py"

# Results
echo ""
echo -e "${BLUE}📊 Quick Test Results${NC}"
echo "===================="
echo "Total: $TOTAL_TESTS | Passed: $PASSED_TESTS | Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All essential tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS test(s) failed. Run './run_all_tests.sh' for details.${NC}"
    exit 1
fi
