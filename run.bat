@echo off
cd /d %~dp0
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] App failed to start. Run setup.bat first.
    pause
)
