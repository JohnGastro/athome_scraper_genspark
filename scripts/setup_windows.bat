@echo off
REM Windows用セットアップバッチファイル

echo ========================================
echo Athome Property Scraper セットアップ
echo ========================================

REM スクリプトのディレクトリに移動
cd /d "%~dp0\.."

REM Python3の確認
echo 1. Python環境の確認...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません
    echo Python 3.8以上をインストールしてください
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo.

REM 仮想環境の作成
echo 2. 仮想環境の作成...
if exist "venv" (
    echo 既存の仮想環境が見つかりました
    set /p RECREATE="再作成しますか？ (y/N): "
    if /i "%RECREATE%"=="y" (
        rmdir /s /q venv
        python -m venv venv
        echo 仮想環境を再作成しました
    ) else (
        echo 既存の仮想環境を使用します
    )
) else (
    python -m venv venv
    echo 仮想環境を作成しました
)

REM 仮想環境をアクティベート
echo.
echo 3. 仮想環境をアクティベート...
call venv\Scripts\activate

REM pipのアップグレード
echo.
echo 4. pipをアップグレード...
python -m pip install --upgrade pip

REM 依存関係のインストール
echo.
echo 5. 依存関係をインストール...
pip install -r requirements.txt

REM ディレクトリの作成
echo.
echo 6. 必要なディレクトリを作成...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "tests" mkdir tests

REM テスト実行
echo.
echo 7. インストールの確認...
python tests\test_demo.py

echo.
echo ========================================
echo セットアップが完了しました！
echo ========================================
echo.
echo 使用方法:
echo   1. スクレイピングを実行:
echo      scripts\run_scraper_windows.bat
echo.
echo   2. ステータスを確認:
echo      scripts\run_scraper_windows.bat status
echo.
echo   3. ヘルプを表示:
echo      scripts\run_scraper_windows.bat help
echo.
echo   4. デモを実行:
echo      scripts\run_scraper_windows.bat demo
echo.

pause