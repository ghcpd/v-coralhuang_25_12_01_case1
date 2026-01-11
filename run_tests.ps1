param(
    [string]$PythonPath = "python"
)

Write-Host "[+] Checking Python version..."
$version = & $PythonPath -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if (-not $version) { Write-Error "Python not found"; exit 1 }

$verParts = $version.Split('.') | ForEach-Object { [int]$_ }
if ($verParts[0] -lt 3 -or ($verParts[0] -eq 3 -and $verParts[1] -lt 8)) {
    Write-Error "Python 3.8+ required. Found $version"
    exit 1
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPath = Join-Path $projectRoot ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "[+] Creating virtual environment at $venvPath"
    & $PythonPath -m venv $venvPath
}

$activate = Join-Path $venvPath "Scripts\Activate.ps1"
. $activate

Write-Host "[+] Installing dependencies"
python -m pip install --upgrade pip
pip install -r "$projectRoot\requirements.txt"
pip install -r "$projectRoot\requirements-dev.txt"

Write-Host "[+] Running pytest with coverage"
pytest --cov=dashboard_improved --cov=data_service_improved --cov-report=term-missing

exit $LASTEXITCODE
