Param()
Write-Host "Starting tests (PowerShell)"
$python = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $python) { Write-Error "python not found. Please install Python 3.8+"; exit 1 }
Try {
	$pyver = (& $python.Path -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
} Catch {
	$pyver = '0.0'
}
if (-not ($pyver -match '^(3)\.([8-9]|1[0-1])$')) { Write-Error "Python 3.8 - 3.11 required for test runner (pandas prebuilt wheels)"; exit 2 }
echo "Using $($python.Path)"
& $python.Path -m venv .venv
if (Test-Path .venv/Scripts/Activate.ps1) {
	. ./.venv/Scripts/Activate.ps1
} else {
	Write-Host "Activating virtualenv failed; is PowerShell script execution policy preventing activation?";
}
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest --maxfail=1 --disable-warnings -q
