$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or not available on PATH. Install Python 3.10+ and try again."
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Bypassing script policy for this session..."
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing project dependencies..."
python -m pip install -r config\requirements.txt

Write-Host "Environment is ready."
Write-Host "To activate it later, run: .\.venv\Scripts\Activate.ps1"
