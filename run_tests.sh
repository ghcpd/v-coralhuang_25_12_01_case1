#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python3}
${PYTHON} -c 'import sys; v=sys.version_info; sys.exit(0 if (v.major==3 and v.minor>=8 and v.minor<12) or (v.major>3 and v.major<12) else 2)'
echo "Using ${PYTHON} (>=3.8)"
${PYTHON} -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest --maxfail=1 --disable-warnings -q
