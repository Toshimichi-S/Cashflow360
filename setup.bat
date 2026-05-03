@echo off
chcp 65001 > nul
echo ========================================
echo  キャッシュフロー管理アプリ セットアップ
echo ========================================
echo.

REM Pythonチェック
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonが見つかりません。
    echo https://www.python.org/downloads/ からPython 3.11以上をインストールしてください。
    echo インストール時に「Add Python to PATH」にチェックを入れてください。
    pause
    exit /b 1
)

echo [OK] Pythonが見つかりました
python --version

echo.
echo 必要なライブラリをインストールしています...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [エラー] インストールに失敗しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo  セットアップ完了！
echo  run.bat をダブルクリックしてアプリを起動してください。
echo ========================================
pause
