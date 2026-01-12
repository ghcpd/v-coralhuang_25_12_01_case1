#!/bin/bash
# Bash test runner script for Linux/Mac
# One-command test setup, execution, and reporting

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default options
COVERAGE=false
VERBOSE=false
TEST_PATH="tests"
MARKER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --marker)
            MARKER="$2"
            shift 2
            ;;
        --path)
            TEST_PATH="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --coverage     Run tests with coverage report"
            echo "  --verbose      Verbose output"
            echo "  --marker NAME  Run tests with specific marker"
            echo "  --path PATH    Test path (default: tests)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Sales Dashboard - Test Runner (Bash)${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}🔍 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}   ✗ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}   ✓ Found: Python $PYTHON_VERSION${NC}"

# Check if Python version is 3.8+
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || [ "$MAJOR" -eq 3 -a "$MINOR" -lt 8 ]; then
    echo -e "${RED}   ✗ Error: Python 3.8+ required, found $MAJOR.$MINOR${NC}"
    exit 1
fi

echo ""

# Virtual environment setup
VENV_PATH=".venv"
ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"

if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}📦 Virtual environment exists${NC}"
else
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    echo -e "${GREEN}   ✓ Virtual environment created${NC}"
fi

echo ""

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
if [ -f "$ACTIVATE_SCRIPT" ]; then
    source "$ACTIVATE_SCRIPT"
    echo -e "${GREEN}   ✓ Virtual environment activated${NC}"
else
    echo -e "${RED}   ✗ Activation script not found${NC}"
    exit 1
fi

echo ""

# Install/upgrade pip
echo -e "${YELLOW}📥 Upgrading pip...${NC}"
python -m pip install --upgrade pip --quiet || {
    echo -e "${YELLOW}   ⚠ Warning: Pip upgrade failed (continuing...)${NC}"
}
echo -e "${GREEN}   ✓ Pip upgraded${NC}"

echo ""

# Install requirements
echo -e "${YELLOW}📥 Installing dependencies...${NC}"

# Install main requirements
if [ -f "requirements.txt" ]; then
    echo -e "${CYAN}   Installing main requirements...${NC}"
    python -m pip install -r requirements.txt --quiet || {
        echo -e "${RED}   ✗ Failed to install main requirements${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}   ⚠ Warning: requirements.txt not found${NC}"
fi

# Install dev requirements
if [ -f "requirements-dev.txt" ]; then
    echo -e "${CYAN}   Installing dev requirements...${NC}"
    python -m pip install -r requirements-dev.txt --quiet || {
        echo -e "${RED}   ✗ Failed to install dev requirements${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}   ⚠ Warning: requirements-dev.txt not found${NC}"
fi

echo -e "${GREEN}   ✓ Dependencies installed${NC}"
echo ""

# Build pytest command
echo -e "${YELLOW}🧪 Running tests...${NC}"
echo ""

PYTEST_ARGS=("$TEST_PATH")

if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS+=("-vv")
else
    PYTEST_ARGS+=("-v")
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS+=("--cov=src")
    PYTEST_ARGS+=("--cov-report=term-missing")
    PYTEST_ARGS+=("--cov-report=html")
    PYTEST_ARGS+=("--cov-report=xml")
fi

if [ -n "$MARKER" ]; then
    PYTEST_ARGS+=("-m" "$MARKER")
fi

# Run pytest
set +e  # Don't exit on pytest failure
python -m pytest "${PYTEST_ARGS[@]}"
TEST_EXIT_CODE=$?
set -e

echo ""
echo -e "${CYAN}============================================================${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}  ✓ ALL TESTS PASSED${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    
    if [ "$COVERAGE" = true ]; then
        echo -e "${CYAN}📊 Coverage report generated:${NC}"
        echo -e "   • Terminal: See above"
        echo -e "   • HTML: htmlcov/index.html"
        echo -e "   • XML: coverage.xml"
        echo ""
        
        # Try to open coverage report
        HTML_REPORT="htmlcov/index.html"
        if [ -f "$HTML_REPORT" ]; then
            if command -v xdg-open &> /dev/null; then
                read -p "Open HTML coverage report? (y/N) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    xdg-open "$HTML_REPORT" 2>/dev/null || open "$HTML_REPORT" 2>/dev/null || true
                fi
            fi
        fi
    fi
    
    exit 0
else
    echo -e "${RED}  ✗ TESTS FAILED${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo -e "   • Run with --verbose for detailed output"
    echo -e "   • Use --marker to run specific test categories"
    echo -e "   • Check test output above for failure details"
    echo ""
    exit 1
fi
