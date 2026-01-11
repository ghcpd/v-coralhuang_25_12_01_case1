#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON_BIN:-python3}

echo "[+] Checking Python version..."
VERSION=$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
MAJOR=$(echo "$VERSION" | cut -d. -f1)
MINOR=$(echo "$VERSION" | cut -d. -f2)
if (( MAJOR < 3 || (MAJOR == 3 && MINOR < 8) )); then
  echo "Python 3.8+ required. Found $VERSION" >&2
  exit 1
fi

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_PATH="$PROJECT_ROOT/.venv"

if [[ ! -d "$VENV_PATH" ]]; then
  echo "[+] Creating virtual environment at $VENV_PATH"
  $PYTHON_BIN -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

echo "[+] Installing dependencies"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"
pip install -r "$PROJECT_ROOT/requirements-dev.txt"

echo "[+] Running pytest with coverage"
pytest --cov=dashboard_improved --cov=data_service_improved --cov-report=term-missing
