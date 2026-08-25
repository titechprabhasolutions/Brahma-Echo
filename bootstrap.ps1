param(
    [switch]$IsElevated = $false
)

# 1. Self-Elevate to Admin (Required for silent global installs)
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Elevating privileges for installation..."
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command $arguments"
    exit
}

$ErrorActionPreference = "Stop"
$WorkingDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -Path $WorkingDir

Write-Host "==========================================================================" -ForegroundColor Yellow
Write-Host "  ____  ____      _    _   _ __  __    _      _    ___ " -ForegroundColor Yellow
Write-Host " | __ )|  _ \    / \  | | | |  \/  |  / \    / \  |_ _|" -ForegroundColor Yellow
Write-Host " |  _ \| |_) |  / _ \ | |_| | |\/| | / _ \  / _ \  | | " -ForegroundColor Yellow
Write-Host " | |_) |  _ <  / ___ \|  _  | |  | |/ ___ \/ ___ \ | | " -ForegroundColor Yellow
Write-Host " |____/|_| \_\/_/   \_\_| |_|_|  |_/_/   \_\_/   \_\___|" -ForegroundColor Yellow
Write-Host ""
Write-Host "                      PREMIUM LOADER" -ForegroundColor Green
Write-Host "==========================================================================" -ForegroundColor Yellow
Write-Host ""

# 2. Helper to refresh environment variables
function Update-Environment {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 3. Check for Python
$PythonExe = $null
if (Get-Command "py" -ErrorAction SilentlyContinue) { $PythonExe = "py" }
elseif (Get-Command "python" -ErrorAction SilentlyContinue) { $PythonExe = "python" }

if (-not $PythonExe) {
    Write-Host "Python not found. Downloading Python 3.11.8..." -ForegroundColor Yellow
    $PythonUrl = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe"
    $PythonInstaller = "$env:TEMP\python_installer.exe"
    Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonInstaller
    
    Write-Host "Installing Python (Silent Mode)..." -ForegroundColor Yellow
    Start-Process -FilePath $PythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
    
    Write-Host "Python installed successfully." -ForegroundColor Green
    Update-Environment
    $PythonExe = "python"
} else {
    Write-Host "Python is already installed: $(Get-Command $PythonExe | Select-Object -ExpandProperty Source)" -ForegroundColor Green
}

# 4. Check for Node.js
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found. Downloading Node v20 LTS..." -ForegroundColor Yellow
    $NodeUrl = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    $NodeInstaller = "$env:TEMP\node_installer.msi"
    Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeInstaller
    
    Write-Host "Installing Node.js (Silent Mode)..." -ForegroundColor Yellow
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$NodeInstaller`" /qn" -Wait
    
    Write-Host "Node.js installed successfully." -ForegroundColor Green
    Update-Environment
} else {
    Write-Host "Node.js is already installed: $(Get-Command node | Select-Object -ExpandProperty Source)" -ForegroundColor Green
}

# 5. Virtual Environment Setup
$VenvDir = Join-Path -Path $WorkingDir -ChildPath ".venv"
$VenvPython = Join-Path -Path $VenvDir -ChildPath "Scripts\python.exe"
$VenvPythonW = Join-Path -Path $VenvDir -ChildPath "Scripts\pythonw.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Virtual Environment in .venv..." -ForegroundColor Cyan
    if (Test-Path $VenvDir) { Remove-Item -Recurse -Force $VenvDir }
    Start-Process -FilePath $PythonExe -ArgumentList "-m venv .venv" -Wait -NoNewWindow
    Write-Host "Virtual Environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual Environment already exists." -ForegroundColor Green
}

# 6. Install Dependencies
Write-Host "Updating pip and installing dependencies..." -ForegroundColor Cyan
Start-Process -FilePath $VenvPython -ArgumentList "-m pip install --upgrade pip setuptools wheel" -Wait -NoNewWindow
Start-Process -FilePath $VenvPython -ArgumentList "-m pip install -r requirements.txt" -Wait -NoNewWindow

Write-Host "Installing Playwright browsers..." -ForegroundColor Cyan
Start-Process -FilePath $VenvPython -ArgumentList "-m playwright install" -Wait -NoNewWindow

# 7. Launch App
Write-Host "Starting Brahma AI..." -ForegroundColor Green
if (Test-Path $VenvPythonW) {
    Start-Process -FilePath $VenvPythonW -ArgumentList "main.py --startup" -WorkingDirectory $WorkingDir
} else {
    Start-Process -FilePath $VenvPython -ArgumentList "main.py --startup" -WorkingDirectory $WorkingDir -WindowStyle Hidden
}

Write-Host "Bootstrap complete. You can close this window."
Start-Sleep -Seconds 3
