@echo off
title FocusLens - Telemetry Simulation Engine
cd /d "%~dp0"
python3.13 simulate_telemetry.py %*
if %ERRORLEVEL% NEQ 0 (
    pause
)
