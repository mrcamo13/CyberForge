@echo off
cd /d "%~dp0"
python play.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python returned exit code %ERRORLEVEL%
    pause
)
