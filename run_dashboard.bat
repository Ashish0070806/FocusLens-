@echo off
title FocusLens - Web Dashboard Server
cd /d "%~dp0"
python3.13 serve_dashboard.py %*
if %ERRORLEVEL% NEQ 0 (
    pause
)
