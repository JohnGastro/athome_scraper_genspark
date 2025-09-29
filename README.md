# Athome Property Scraper
大分市売土地情報自動収集・分析システム

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-green)
![License](https://img.shields.io/badge/license-Proprietary-red)

## 🎯 概要

このシステムは、athome.co.jpから大分市の売土地情報を自動収集し、AI分析によってランク付けを行い、高ランク物件を自動で通知・管理するPythonアプリケーションです。

### ✨ 主要機能

- **自動スクレイピング**: 大分市売土地情報の定期収集
- **AIランク付け**: 価格・立地・面積・投資価値による総合評価（S〜D級）
- **差分検出**: 新規物件・価格変更の自動検出
- **データベース管理**: SQLiteによる物件データの永続化
- **統計分析**: 物件統計とトレンド分析
- **CSVエクスポート**: ランク別物件リストの出力
- **ログ管理**: 詳細な実行履歴とエラー追跡

### 🎪 ビジネスモデル

**「不動産投資家が集まる不動産会社」**としてのブランディング戦略
- 高品質な物件情報の自動配信
- 投資家コミュニティの形成
- 紹介インセンティブ制度（成約時10万円）

## 🏗️ システム構成

```
athome_scraper/
├── README.md                    # このファイル
├── requirements.txt             # Python依存関係
├── .gitignore                   # Git除外設定
├── config/
│   └── athome_scraper_config.py # 設定ファイル
├── src/
│   ├── athome_scraper.py        # メインスクレイパー
│   ├── database.py              # データベース管理
│   └── ranking.py               # ランク付けアルゴリズム
├── scripts/
│   ├── setup.sh                 # セットアップスクリプト
│   ├── run_scraper.py           # 実行スクリプト
│   └── crontab_template         # cron設定テンプレート
├── data/
│   ├── .gitkeep
│   └── properties.db            # SQLiteデータベース（実行後作成）
├── logs/
│   ├── .gitkeep
│   └── scraper_YYYYMMDD.log    # 実行ログ（実行後作成）
├── exports/
│   └── properties_*.csv         # CSVエクスポート（実行後作成）
└── tests/
    └── test_*.py                # テストファイル
```

## 🚀 クイックスタート

### 前提条件

- Python 3.8以上
- pip（Pythonパッケージマネージャー）
- インターネット接続

### 1. セットアップ（初回のみ）

#### Windows の場合

```batch
# 1. プロジェクトをダウンロード・解凍
# 2. コマンドプロンプトまたはPowerShellを開く
# 3. プロジェクトフォルダに移動
cd athome_scraper

# 4. セットアップスクリプトを実行
scripts\setup_windows.bat

# または手動セットアップ
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### macOS/Linux の場合

```bash
# 1. プロジェクトをダウンロード・解凍
cd athome_scraper

# 2. セットアップスクリプトを実行
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. 仮想環境をアクティベート
source venv/bin/activate
```

### 2. 実行

#### Windows の場合

```batch
# スクレイピング実行
scripts\run_scraper_windows.bat

# ステータス確認
scripts\run_scraper_windows.bat status

# デモ実行
scripts\run_scraper_windows.bat demo

# または直接Pythonで実行
python scripts\run_scraper.py
```

#### macOS/Linux の場合

```bash
# スクレイピング実行
python scripts/run_scraper.py

# ステータス確認
python scripts/run_scraper.py status

# ヘルプ表示
python scripts/run_scraper.py help
```

### 3. 定期実行設定（オプション）

```bash
# crontabテンプレートを編集（PROJECT_DIRをフルパスに変更）
nano scripts/crontab_template

# crontabに登録
crontab scripts/crontab_template

# 設定確認
crontab -l
```

## ⚙️ 設定

### config/athome_scraper_config.py

主要な設定項目：

#### スクレイピング設定
```python
SCRAPING_CONFIG = {
    "request_delay": 2,      # リクエスト間隔（秒）
    "timeout": 30,           # タイムアウト（秒）
    "max_pages": 10,         # 最大取得ページ数
    "user_agent": "Mozilla/5.0..."  # ユーザーエージェント
}
```

#### ランク閾値
```python
RANK_THRESHOLDS = {
    "S": 90,  # S級：90点以上
    "A": 80,  # A級：80-89点
    "B": 70,  # B級：70-79点
    "C": 60,  # C級：60-69点
    "D": 0    # D級：60点未満
}
```

#### 評価基準
```python
# 価格評価（坪単価）
PRICE_CRITERIA = {
    "excellent": 10,  # 10万円/坪以下 → 100点
    "very_good": 15,  # 15万円/坪以下 → 80点
    # ...
}

# プレミアムエリア
PREMIUM_AREAS = [
    "中央町", "府内町", "都町", "金池町", "末広町",
    # ...
]
```

## 📊 ランク付けアルゴリズム

### 評価項目と配分

| 項目 | 配分 | 評価基準 |
|------|------|----------|
| **価格評価** | 30% | 坪単価による評価（10万円/坪以下で満点） |
| **立地評価** | 30% | エリア評価（50%）+ 駅距離評価（50%） |
| **面積評価** | 20% | 土地面積による評価（100坪以上で満点） |
| **投資価値** | 20% | 建ぺい率・容積率・用途地域による評価 |

### 総合ランク

| ランク | スコア | 説明 | アクション |
|--------|--------|------|------------|
| **S** | 90点以上 | 最優良物件 | 即時通知・最優先広告 |
| **A** | 80-89点 | 優良物件 | 優先通知・広告出稿 |
| **B** | 70-79点 | 良物件 | 通常配信 |
| **C** | 60-69点 | 標準物件 | 参考情報として保存 |
| **D** | 60点未満 | 要検討物件 | フィルタ対象 |

## 🗄️ データベース構造

### propertiesテーブル（主要カラム）

| カラム名 | 型 | 説明 |
|----------|-----|------|
| property_id | TEXT | 物件ID（ユニーク） |
| url | TEXT | 物件詳細URL |
| title | TEXT | 物件タイトル |
| price_numeric | INTEGER | 価格（数値、万円） |
| address | TEXT | 住所 |
| land_area_tsubo | REAL | 土地面積（坪） |
| ranking_score | REAL | 総合スコア（0-100） |
| ranking_grade | TEXT | ランク（S,A,B,C,D） |
| is_active | BOOLEAN | アクティブフラグ |

### scraping_logsテーブル

実行ログを記録し、統計情報を追跡します。

## 📈 出力ファイル

### CSVエクスポート
- **場所**: `exports/properties_YYYYMMDD_HHMMSS.csv`
- **内容**: ランク別物件リスト（S,A,B級のみ）
- **形式**: UTF-8 with BOM（Excel対応）

### ログファイル
- **実行ログ**: `logs/scraper_YYYYMMDD.log`
- **cron ログ**: `logs/cron.log`
- **ステータスレポート**: `logs/status_report.log`

## 🔧 カスタマイズ

### 1. 評価基準の調整
`config/athome_scraper_config.py`の各種基準値を変更

### 2. スクレイピング対象の変更
`ATHOME_SEARCH_URL`を変更してエリアや条件を調整

### 3. 通知機能の追加
`src/athome_scraper.py`に通知処理を追加（LINE、メール等）

### 4. エクスポート形式の追加
`OUTPUT_CONFIG['export_formats']`に形式を追加（json、excel等）

## 🚨 注意事項

### 法的・倫理的考慮
- **robots.txt**の遵守
- **利用規約**の確認と遵守
- **適切なリクエスト間隔**の維持（デフォルト2秒）
- **個人利用**の範囲内での使用

### 技術的制限
- JavaScriptレンダリングが必要な場合はSeleniumの追加が必要
- IPアドレス制限がある場合はプロキシの検討が必要
- サイト構造が変更された場合はセレクタの更新が必要

### パフォーマンス
- 大量のページを取得する場合は`max_pages`を調整
- データベースが大きくなった場合は定期的なクリーンアップを実施

## 🔮 今後の拡張予定

### Phase 1: 基本機能（✅ 完了）
- [x] スクレイピング基盤構築
- [x] ランク付けアルゴリズム実装
- [x] データベース管理機能
- [x] CSVエクスポート機能

### Phase 2: 通知・連携機能（開発中）
- [ ] LINE Bot API連携
- [ ] メール通知機能
- [ ] Slack通知機能
- [ ] 物件概要書の自動生成

### Phase 3: AI機能強化（計画中）
- [ ] 機械学習による価格予測
- [ ] 画像解析による物件評価
- [ ] 自然言語処理による詳細分析
- [ ] 市場トレンド分析

### Phase 4: Web UI開発（将来）
- [ ] 管理画面の開発
- [ ] APIサーバーの実装
- [ ] リアルタイムダッシュボード
- [ ] モバイルアプリ対応

## 🤝 トラブルシューティング

### よくある問題と解決方法

#### Q: スクレイピングが失敗する
**A:** 以下を確認してください：
- インターネット接続
- サイトの構造変更（セレクタの更新が必要）
- `logs/`フォルダの詳細なエラーログ

#### Q: ランク付けが適切でない
**A:** `config/athome_scraper_config.py`の評価基準を調整してください

#### Q: 定期実行が動作しない
**A:** crontabのパスとPython環境を確認してください

#### Q: データベースエラー
**A:** `data/properties.db`の権限を確認し、必要なら削除して再作成

## 📞 サポート

### 開発環境
- **Python**: 3.8以上推奨
- **OS**: Windows、macOS、Linux対応
- **必要メモリ**: 1GB以上
- **必要ディスク**: 100MB以上

### ログレベルの変更
`config/athome_scraper_config.py`の`LOG_CONFIG['log_level']`を変更：
- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 通常の実行情報（デフォルト）
- `WARNING`: 警告のみ
- `ERROR`: エラーのみ

## 📄 ライセンス

このソフトウェアは不動産投資コミュニティシステム専用です。
商用利用や再配布は禁止されています。

---

**作成者**: Real Estate Investment Community System  
**バージョン**: 1.0.0  
**最終更新**: 2024年  
**お問い合わせ**: [開発チームまで]

## 🎉 謝辞

このプロジェクトは以下のオープンソースライブラリを使用しています：
- BeautifulSoup4
- Requests
- Pandas
- その他requirements.txtに記載のライブラリ

皆様の素晴らしい成果に感謝いたします。