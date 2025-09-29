#!/bin/bash

echo "========================================"
echo "Athome Property Scraper セットアップ"
echo "========================================"

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Python3の確認
echo "1. Python環境の確認..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3がインストールされていません"
    echo "Pythonをインストールしてください: https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )(.+)')
echo "✅ Python $PYTHON_VERSION が見つかりました"

# 仮想環境の作成
echo ""
echo "2. 仮想環境の作成..."
if [ -d "venv" ]; then
    echo "既存の仮想環境が見つかりました"
    read -p "再作成しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo "✅ 仮想環境を再作成しました"
    else
        echo "既存の仮想環境を使用します"
    fi
else
    python3 -m venv venv
    echo "✅ 仮想環境を作成しました"
fi

# 仮想環境をアクティベート
echo ""
echo "3. 仮想環境をアクティベート..."
source venv/bin/activate

# pipのアップグレード
echo ""
echo "4. pipをアップグレード..."
pip install --upgrade pip

# 依存関係のインストール
echo ""
echo "5. 依存関係をインストール..."
pip install -r requirements.txt

# ディレクトリの作成
echo ""
echo "6. 必要なディレクトリを作成..."
mkdir -p data logs exports tests

# 設定ファイルの確認
echo ""
echo "7. 設定ファイルの確認..."
if [ -f "config/athome_scraper_config.py" ]; then
    echo "✅ 設定ファイルが見つかりました"
else
    echo "❌ 設定ファイルが見つかりません"
    exit 1
fi

# テスト実行
echo ""
echo "8. インストールの確認..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.database import PropertyDatabase
    from src.ranking import PropertyRanker
    from src.athome_scraper import AthomeScraper
    print('✅ すべてのモジュールが正常にインポートできました')
except ImportError as e:
    print(f'❌ モジュールのインポートに失敗しました: {e}')
    sys.exit(1)
"

# 実行権限の付与
echo ""
echo "9. スクリプトに実行権限を付与..."
chmod +x scripts/*.sh
chmod +x scripts/*.py

echo ""
echo "========================================"
echo "✅ セットアップが完了しました！"
echo "========================================"
echo ""
echo "使用方法:"
echo "  1. 仮想環境をアクティベート:"
echo "     source venv/bin/activate"
echo ""
echo "  2. スクレイピングを実行:"
echo "     python scripts/run_scraper.py"
echo ""
echo "  3. ステータスを確認:"
echo "     python scripts/run_scraper.py status"
echo ""
echo "  4. ヘルプを表示:"
echo "     python scripts/run_scraper.py help"
echo ""
echo "設定ファイル:"
echo "  config/athome_scraper_config.py"
echo ""
echo "ログファイル:"
echo "  logs/scraper_YYYYMMDD.log"
echo ""