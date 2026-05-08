@echo off
set PYTHONUTF8=1
title RIVER-F FLOW EDITION
cd /d "%~dp0"

echo ============================================
echo  RIVER-F FLOW EDITION (ANALYSIS ONLY)
echo ============================================
echo.
echo Starting Analysis System...
echo Browser will open automatically.
echo.

:: Start server and open browser
start /b python src/app.py
timeout /t 2 > nul
start http://localhost:5001

echo.
echo System is running on http://localhost:5001
echo To stop, close this window.
echo ============================================
pause