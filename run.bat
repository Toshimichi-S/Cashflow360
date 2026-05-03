@echo off
chcp 65001 > nul
cd /d %~dp0
python main.py
if errorlevel 1 (
    echo.
    echo アプリの起動に失敗しました。
    echo setup.bat を先に実行してください。
    pause
)
