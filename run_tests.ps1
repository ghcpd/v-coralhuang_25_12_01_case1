#!/usr/bin/env pwsh
# PowerShell test runner script for Windows
# One-command test setup, execution, and reporting

param(
    [switch]$Coverage,
    [switch]$Verbose,
    [string]$TestPath = "tests",
    [string]$Marker = ""
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  Sales Dashboard - Test Runner (PowerShell)" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "🔍 Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✓ Found: $pythonVersion" -ForegroundColor Green
    
    # Extract version number
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Host "   ✗ Error: Python 3.8+ required, found $major.$minor" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "   ✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Virtual environment setup
$venvPath = ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "📦 Virtual environment exists" -ForegroundColor Yellow
} else {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
}

Write-Host ""

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "   ✗ Activation script not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install/upgrade pip
Write-Host "📥 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Pip upgraded" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Warning: Pip upgrade failed (continuing...)" -ForegroundColor Yellow
}

Write-Host ""

# Install requirements
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow

# Install main requirements
if (Test-Path "requirements.txt") {
    Write-Host "   Installing main requirements..." -ForegroundColor Cyan
    python -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ✗ Failed to install main requirements" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ⚠ Warning: requirements.txt not found" -ForegroundColor Yellow
}

# Install dev requirements
if (Test-Path "requirements-dev.txt") {
    Write-Host "   Installing dev requirements..." -ForegroundColor Cyan
    python -m pip install -r requirements-dev.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ✗ Failed to install dev requirements" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ⚠ Warning: requirements-dev.txt not found" -ForegroundColor Yellow
}

Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Build pytest command
Write-Host "🧪 Running tests..." -ForegroundColor Yellow
Write-Host ""

$pytestArgs = @($TestPath)

if ($Verbose) {
    $pytestArgs += "-vv"
} else {
    $pytestArgs += "-v"
}

if ($Coverage) {
    $pytestArgs += "--cov=src"
    $pytestArgs += "--cov-report=term-missing"
    $pytestArgs += "--cov-report=html"
    $pytestArgs += "--cov-report=xml"
}

if ($Marker) {
    $pytestArgs += "-m"
    $pytestArgs += $Marker
}

# Run pytest
python -m pytest @pytestArgs

$testExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan

if ($testExitCode -eq 0) {
    Write-Host "  ✓ ALL TESTS PASSED" -ForegroundColor Green
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 59) -ForegroundColor Cyan
    Write-Host ""
    
    if ($Coverage) {
        Write-Host "📊 Coverage report generated:" -ForegroundColor Cyan
        Write-Host "   • Terminal: See above" -ForegroundColor White
        Write-Host "   • HTML: htmlcov/index.html" -ForegroundColor White
        Write-Host "   • XML: coverage.xml" -ForegroundColor White
        Write-Host ""
        
        # Open coverage report if available
        $htmlReport = "htmlcov\index.html"
        if (Test-Path $htmlReport) {
            $openReport = Read-Host "Open HTML coverage report? (y/N)"
            if ($openReport -eq "y" -or $openReport -eq "Y") {
                Start-Process $htmlReport
            }
        }
    }
    
    exit 0
} else {
    Write-Host "  ✗ TESTS FAILED" -ForegroundColor Red
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 59) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 Tips:" -ForegroundColor Yellow
    Write-Host "   • Run with -Verbose for detailed output" -ForegroundColor White
    Write-Host "   • Use -Marker to run specific test categories" -ForegroundColor White
    Write-Host "   • Check test output above for failure details" -ForegroundColor White
    Write-Host ""
    exit 1
}
