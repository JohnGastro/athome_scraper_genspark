@echo off
REM Windows用実行バッチファイル

echo ========================================
echo Athome Property Scraper - Windows版
echo ========================================

REM スクリプトのディレクトリに移動
cd /d "%~dp0\.."

REM 仮想環境が存在するか確認
if not exist "venv\Scripts\activate.bat" (
    echo エラー: 仮想環境が見つかりません
    echo まず以下を実行してください:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM 仮想環境をアクティベート
call venv\Scripts\activate

REM コマンドライン引数をチェック
if "%1"=="" (
    REM 引数なしの場合は実行
    python scripts\run_scraper.py
) else if "%1"=="status" (
    python scripts\run_scraper.py status
) else if "%1"=="help" (
    python scripts\run_scraper.py help
) else if "%1"=="demo" (
    python tests\test_demo.py
) else (
    echo 不明なコマンド: %1
    echo 使用方法: run_scraper_windows.bat [status^|help^|demo]
)

pause