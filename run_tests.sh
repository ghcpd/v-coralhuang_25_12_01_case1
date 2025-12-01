#!/usr/bin/env bash
set -e
echo "Running test suite (bash)..."
python --version
PYTHON_OK=$(python - <<'PY'
import sys
print(1 if sys.version_info >= (3,8) else 0)
PY
)
if [ $PYTHON_OK -eq 0 ]; then
  echo "Python 3.8+ is required"; exit 1
fi
if [ ! -d .venv ]; then
  python -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest --maxfail=1 --disable-warnings -q
