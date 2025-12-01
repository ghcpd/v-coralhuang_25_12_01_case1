#!/usr/bin/env bash
set -e
python -V
if [ ! -d .venv ]; then
  python -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q --maxfail=1 --disable-warnings
exit $?
