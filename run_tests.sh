#!/bin/bash
# Enhanced Sales Dashboard - Test Runner (Linux/Mac)
# Automatically checks environment, creates venv, installs dependencies, and runs tests

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Enhanced Sales Dashboard - Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or later.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Check if version is at least 3.8
REQUIRED_VERSION="3.8"
if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo -e "${RED}Python $REQUIRED_VERSION or later is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo -e "${BLUE}Project directory: $PROJECT_DIR${NC}"

# Check for virtual environment
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "\n${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}Virtual environment activated${NC}"

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip --quiet
echo -e "${GREEN}pip upgraded${NC}"

# Install dependencies
echo -e "\n${YELLOW}Installing main dependencies...${NC}"
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements.txt" --quiet
    echo -e "${GREEN}Main dependencies installed${NC}"
fi

echo -e "\n${YELLOW}Installing development dependencies...${NC}"
if [ -f "$PROJECT_DIR/requirements-dev.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements-dev.txt" --quiet
    echo -e "${GREEN}Development dependencies installed${NC}"
fi

# Run tests
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}Running Tests${NC}"
echo -e "${BLUE}================================================${NC}"

cd "$PROJECT_DIR"

# Run pytest with coverage
python -m pytest tests/ -v --tb=short

# Capture exit code
TEST_EXIT_CODE=$?

# Display results summary
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}Test Results Summary${NC}"
echo -e "${BLUE}================================================${NC}"

if [ -f "$PROJECT_DIR/htmlcov/index.html" ]; then
    echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
fi

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}✓ Project is ready for use${NC}"
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    echo -e "${RED}✗ Please review the errors above${NC}"
fi

echo -e "${BLUE}================================================${NC}"

exit $TEST_EXIT_CODE
