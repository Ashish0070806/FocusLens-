@echo off
title FocusLens - Live Webcam Telemetry
cd /d "%~dp0"
python3.13 webcam_telemetry.py %*
if %ERRORLEVEL% NEQ 0 (
    pause
)
