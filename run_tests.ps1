# Enhanced Sales Dashboard - Test Runner (Windows PowerShell)
# Automatically checks environment, creates venv, installs dependencies, and runs tests

param(
    [switch]$Force = $false,
    [switch]$NoVenv = $false
)

# Enable error handling
$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Blue
    Write-Host $Text -ForegroundColor Blue
    Write-Host "================================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

Write-Header "Enhanced Sales Dashboard - Test Runner"

# Check Python version
Write-Warning "Checking Python version..."
try {
    $PythonVersion = & python --version 2>&1
    Write-Success "Python found: $PythonVersion"
}
catch {
    Write-Error "Python is not installed or not in PATH"
    Write-Error "Please install Python 3.8 or later from https://www.python.org"
    exit 1
}

# Parse version
if ($PythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
    $Major = [int]$Matches[1]
    $Minor = [int]$Matches[2]
    
    if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 8)) {
        Write-Error "Python 3.8 or later is required (found $Major.$Minor)"
        exit 1
    }
}

# Get script directory
$ProjectDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ProjectDir "venv"

Write-Host ""
Write-Host "Project directory: $ProjectDir" -ForegroundColor Blue

# Create/activate virtual environment
if (-not $NoVenv) {
    if (-not (Test-Path $VenvDir)) {
        Write-Warning "Creating virtual environment..."
        & python -m venv $VenvDir
        Write-Success "Virtual environment created"
    }
    
    Write-Warning "Activating virtual environment..."
    $ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    
    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-Success "Virtual environment activated"
    }
    else {
        Write-Error "Failed to find activation script at $ActivateScript"
        exit 1
    }
}

# Upgrade pip
Write-Warning "Upgrading pip..."
& python -m pip install --upgrade pip --quiet
Write-Success "pip upgraded"

# Install dependencies
Write-Warning "Installing main dependencies..."
$ReqFile = Join-Path $ProjectDir "requirements.txt"
if (Test-Path $ReqFile) {
    & pip install -r $ReqFile --quiet
    Write-Success "Main dependencies installed"
}

Write-Warning "Installing development dependencies..."
$DevReqFile = Join-Path $ProjectDir "requirements-dev.txt"
if (Test-Path $DevReqFile) {
    & pip install -r $DevReqFile --quiet
    Write-Success "Development dependencies installed"
}

# Run tests
Write-Header "Running Tests"

Push-Location $ProjectDir

try {
    & python -m pytest tests/ -v --tb=short
    $TestExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

# Display results summary
Write-Header "Test Results Summary"

$HtmlCoverageReport = Join-Path $ProjectDir "htmlcov\index.html"
if (Test-Path $HtmlCoverageReport) {
    Write-Success "Coverage report generated: htmlcov/index.html"
}

if ($TestExitCode -eq 0) {
    Write-Success "All tests passed!"
    Write-Success "Project is ready for use"
}
else {
    Write-Error "Some tests failed"
    Write-Error "Please review the errors above"
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue

exit $TestExitCode
