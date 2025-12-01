# PowerShell test runner
$ErrorActionPreference = 'Stop'

# check python version
$py = python -V
if ($LASTEXITCODE -ne 0) { Write-Error 'Python not found'; exit 1 }

# Create venv if not exists
if (!(Test-Path -Path .venv)) {
  python -m venv .venv
}
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pytest -q --maxfail=1 --disable-warnings
exit $LASTEXITCODE
