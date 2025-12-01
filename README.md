# Improved Sales Dashboard

This workspace shows an improved interactive sales dashboard with AJAX updates, multi-dimension filters, and caching.

Run locally:

PowerShell (recommended Python 3.8-3.11):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/dashboard_improved.py
```

Bash (recommended Python 3.8-3.11):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/dashboard_improved.py
```

Open http://localhost:5000/improved

Run tests:
```bash
./run_tests.sh
```
or
```powershell
.\run_tests.ps1
```

Notes:
- The test runner installs `pandas` which requires prebuilt wheels on Windows. For a smooth test run on Windows, use Python 3.8–3.11 (3.14 may require building pandas from source and Visual Studio build tools.)
- If you cannot switch Python versions, you can also run tests in a Linux container or a virtual environment with a supported Python version.
