#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Help message
show_help() {
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo "Run tests for LoadApp.AI"
    echo
    echo "Options:"
    echo "  -a, --all       Run all tests"
    echo "  -b, --backend   Run backend tests only"
    echo "  -f, --frontend  Run frontend tests only"
    echo "  -p, --pattern   Run tests matching pattern (e.g., -p 'hello')"
    echo "  -v, --verbose   Run with verbose output"
    echo "  -h, --help      Show this help message"
    echo
    echo "Examples:"
    echo "  ./run_tests.sh -a        # Run all tests"
    echo "  ./run_tests.sh -b -v     # Run backend tests with verbose output"
    echo "  ./run_tests.sh -p hello  # Run tests matching 'hello'"
}

# Activate virtual environment
activate_venv() {
    if [ -d "venv" ]; then
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found!${NC}"
        echo "Please create a virtual environment first:"
        echo "python -m venv venv"
        exit 1
    fi
}

# Default values
VERBOSE=""
PATTERN=""
TEST_PATH="tests"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            TEST_PATH="tests"
            shift
            ;;
        -b|--backend)
            TEST_PATH="tests/backend"
            shift
            ;;
        -f|--frontend)
            TEST_PATH="tests/frontend"
            shift
            ;;
        -p|--pattern)
            PATTERN="-k $2"
            shift
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Activate virtual environment
activate_venv

# Run tests
echo -e "${GREEN}Running tests...${NC}"
if [ -n "$PATTERN" ]; then
    echo -e "${YELLOW}Running tests matching pattern: $PATTERN${NC}"
fi

pytest $TEST_PATH $VERBOSE $PATTERN

# Check test result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi 