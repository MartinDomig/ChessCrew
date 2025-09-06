#!/bin/bash

# Chess Crew Selective Test Runner
# Run specific tests by pattern or name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
export FLASK_SECRET_KEY="test-secret-key-$(date +%s)"
TEST_DIR="/home/martin/chesscrew/backend/tests"

# Help function
show_help() {
    echo -e "${BLUE}Chess Crew Selective Test Runner${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo "Usage: $0 [pattern|test_name]"
    echo ""
    echo "Examples:"
    echo "  $0 baseline           # Run baseline test"
    echo "  $0 U10               # Run U10 test"
    echo "  $0 bugfix            # Run bugfix tests"
    echo "  $0 team              # Run team tournament test"
    echo "  $0 all               # Run all tests (same as ./run_all_tests.sh)"
    echo ""
    echo "Available tests:"
    cd "$TEST_DIR" 2>/dev/null || exit 1
    for test_file in test_*.py; do
        if [ -f "$test_file" ]; then
            test_name=$(echo "$test_file" | sed 's/test_//' | sed 's/.py//')
            echo "  - $test_name ($test_file)"
        fi
    done
}

# Check arguments
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

PATTERN="$1"

# Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -f "/home/martin/chesscrew/venv/bin/activate" ]; then
        source "/home/martin/chesscrew/venv/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    fi
fi

echo -e "${BLUE}🎯 Running tests matching pattern: '$PATTERN'${NC}"
echo ""

# Change to test directory
cd "$TEST_DIR"

# Special case: run all tests
if [ "$PATTERN" = "all" ]; then
    echo "Running all tests..."
    exec ../run_all_tests.sh
fi

# Find matching test files
FOUND_TESTS=()
for test_file in test_*.py; do
    if [ -f "$test_file" ]; then
        # Check if pattern matches the test file name
        if echo "$test_file" | grep -i "$PATTERN" > /dev/null; then
            FOUND_TESTS+=("$test_file")
        fi
    fi
done

# Check if any tests found
if [ ${#FOUND_TESTS[@]} -eq 0 ]; then
    echo -e "${RED}❌ No tests found matching pattern: '$PATTERN'${NC}"
    echo ""
    echo "Available tests:"
    for test_file in test_*.py; do
        if [ -f "$test_file" ]; then
            echo "  - $test_file"
        fi
    done
    exit 1
fi

# Run found tests
TOTAL=0
PASSED=0
FAILED=0

for test_file in "${FOUND_TESTS[@]}"; do
    echo -e "${YELLOW}🔄 Running: $test_file${NC}"
    TOTAL=$((TOTAL + 1))
    
    if python "$test_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED: $test_file${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ FAILED: $test_file${NC}"
        echo "   Running with output for debugging:"
        python "$test_file"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

# Summary
echo -e "${BLUE}📊 Results for pattern '$PATTERN'${NC}"
echo "================================"
echo "Total: $TOTAL | Passed: $PASSED | Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All matching tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED test(s) failed${NC}"
    exit 1
fi
