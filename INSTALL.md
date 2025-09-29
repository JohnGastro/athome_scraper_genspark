# インストールガイド

## 📋 必要な環境

- **OS**: Windows 10/11、macOS、Linux
- **Python**: 3.8以上（[python.org](https://www.python.org/)からダウンロード）
- **メモリ**: 1GB以上
- **ディスク空き容量**: 200MB以上
- **インターネット接続**: 必須

## 🚀 クイックインストール（推奨）

### Windows の場合

```powershell
# 1. PowerShellを管理者権限で開く

# 2. プロジェクトフォルダに移動
cd C:\path\to\athome_scraper

# 3. 仮想環境を作成
python -m venv venv

# 4. 仮想環境をアクティベート
.\venv\Scripts\Activate

# 5. 依存関係をインストール
pip install -r requirements.txt

# 6. テスト実行
python tests\test_demo.py
```

### macOS/Linux の場合

```bash
# 1. ターミナルを開く

# 2. プロジェクトフォルダに移動
cd ~/athome_scraper

# 3. セットアップスクリプトを実行
chmod +x scripts/setup.sh
./scripts/setup.sh

# 4. 仮想環境をアクティベート
source venv/bin/activate

# 5. テスト実行
python tests/test_demo.py
```

## 📝 手動インストール

### 1. Pythonの確認

```bash
python --version
# または
python3 --version
```

Python 3.8以上が必要です。インストールされていない場合は[python.org](https://www.python.org/)からダウンロードしてください。

### 2. プロジェクトのセットアップ

```bash
# プロジェクトディレクトリに移動
cd athome_scraper

# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements.txt
```

### 3. 必要なディレクトリの作成

```bash
mkdir -p data logs exports tests
```

### 4. 動作確認

```bash
# デモスクリプトを実行
python tests/test_demo.py

# ヘルプを表示
python scripts/run_scraper.py help
```

## ⚙️ 設定

### 基本設定の確認

`config/athome_scraper_config.py`を編集して設定を調整：

```python
# スクレイピング間隔（秒）
SCRAPING_CONFIG = {
    "request_delay": 2,  # サーバーに負荷をかけないよう調整
    "max_pages": 10,     # 取得ページ数の上限
}
```

### URLの設定

大分市以外の地域を対象にする場合は、`ATHOME_SEARCH_URL`を変更：

```python
# 例：福岡市の場合
ATHOME_SEARCH_URL = "https://www.athome.co.jp/tochi/chuko/fukuoka/fukuoka-city/list/"
```

## 🏃 実行方法

### 基本的な使い方

```bash
# 仮想環境をアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# スクレイピングを実行
python scripts/run_scraper.py

# ステータスを確認
python scripts/run_scraper.py status

# ヘルプを表示
python scripts/run_scraper.py help
```

### 定期実行の設定

#### Linux/macOS (crontab)

```bash
# crontabを編集
crontab -e

# 以下を追加（パスは環境に合わせて変更）
0 9,12,15,17 * * * cd /home/user/athome_scraper && source venv/bin/activate && python scripts/run_scraper.py >> logs/cron.log 2>&1
```

#### Windows (タスクスケジューラ)

1. タスクスケジューラを開く
2. 「基本タスクの作成」を選択
3. 名前：「Athome Property Scraper」
4. トリガー：毎日
5. 操作：プログラムの開始
   - プログラム：`C:\path\to\athome_scraper\venv\Scripts\python.exe`
   - 引数：`scripts/run_scraper.py`
   - 開始：`C:\path\to\athome_scraper`

## 🔧 トラブルシューティング

### よくある問題

#### 1. Pythonが見つからない

```bash
# Pythonのパスを確認
which python3  # macOS/Linux
where python   # Windows
```

#### 2. pip install でエラー

```bash
# pipをアップグレード
python -m pip install --upgrade pip

# 個別にインストール
pip install requests
pip install beautifulsoup4
pip install lxml
pip install pandas
```

#### 3. Permission denied エラー

```bash
# macOS/Linux: 実行権限を付与
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

#### 4. モジュールが見つからない

```bash
# 仮想環境が有効か確認
which python  # venv内のpythonが表示されるはず

# 再インストール
pip install -r requirements.txt
```

## 📚 追加リソース

- [Python公式ドキュメント](https://docs.python.org/ja/)
- [BeautifulSoup4ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests ドキュメント](https://requests-docs-ja.readthedocs.io/)

## 🆘 サポート

問題が解決しない場合は、以下の情報を含めてお問い合わせください：

- OS名とバージョン
- Pythonのバージョン（`python --version`の出力）
- エラーメッセージの全文
- `logs/`フォルダ内の最新ログファイル

---

**最終更新**: 2024年  
**バージョン**: 1.0.0