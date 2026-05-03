@echo off
chcp 65001 > nul
echo ========================================
echo  キャッシュフロー管理アプリ exe化
echo ========================================
echo.

REM PyInstallerをインストール
echo [1/3] PyInstallerをインストール中...
python -m pip install pyinstaller
if errorlevel 1 (
    echo [エラー] PyInstallerのインストールに失敗しました。
    pause
    exit /b 1
)

echo.
echo [2/3] exeをビルド中...
echo ※ このウィンドウに進捗が表示されます。完了まで数分かかります。
echo.
pyinstaller --onefile --noconsole --name "キャッシュフロー管理" --add-data "ui;ui" main.py

if errorlevel 1 (
    echo.
    echo [エラー] ビルドに失敗しました。
    pause
    exit /b 1
)

echo.
echo [3/3] 完了！
echo ========================================
echo  dist\キャッシュフロー管理.exe が作成されました。
echo  このファイルをダブルクリックで起動できます。
echo ========================================
echo.
echo ※ 初回起動時にWindowsセキュリティの警告が出ることがあります。
echo   「詳細情報」→「実行」をクリックしてください。
pause
