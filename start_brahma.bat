@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Brahma AI - Lite - Premium Launcher
cd /d "%~dp0"

color 0E

echo ==========================================================================
echo   ____  ____      _    _   _ __  __    _      _    ___ 
echo  ^| __ )^|  _ \    / \  ^| ^| ^| ^|  \/  ^|  / \    / \  ^|_ _^|
echo  ^|  _ \^| ^|_) ^|  / _ \ ^| ^|_^| ^| ^|\/^| ^| / _ \  / _ \  ^| ^| 
echo  ^| ^|_) ^|  _ ^<  / ___ \^|  _  ^| ^|  ^| ^|/ ___ \/ ___ \ ^| ^| 
echo  ^|____/^|_^| \_\/_/   \_\_^| ^|_^|_^|  ^|_/_/   \_\_/   \_\___^|
echo.
echo                       PREMIUM LOADER
echo ==========================================================================
echo.
echo Launching automated bootstrap sequence...

powershell.exe -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"

if %errorlevel% neq 0 (
  echo ERROR: Bootstrap failed.
  pause
  exit /b %errorlevel%
)
exit /b 0
