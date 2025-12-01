param()
Write-Host "Running test suite (PowerShell)..."
python -V
if ($LASTEXITCODE -ne 0) { Write-Host "Python not found."; exit 1 }
py -3 - <<'PY'
import sys
if sys.version_info < (3,8):
    print('Python 3.8+ is required')
    sys.exit(1)
print('Python version OK')
PY

if (-Not (Test-Path .venv)) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1; pip install --upgrade pip; pip install -r requirements.txt; pip install -r requirements-dev.txt; pytest --maxfail=1 --disable-warnings -q; exit $LASTEXITCODE
