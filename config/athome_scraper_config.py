"""
Athome Property Scraper 設定ファイル
大分市売土地情報収集システムの設定
"""
import os
from pathlib import Path

# プロジェクトのベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================
# スクレイピング設定
# ===========================================

# Athome 大分市売土地のURL（条件指定可能）
ATHOME_BASE_URL = "https://www.athome.co.jp"
ATHOME_SEARCH_URL = "https://www.athome.co.jp/tochi/chuko/oita/oita-city/list/"

# スクレイピング設定
SCRAPING_CONFIG = {
    "request_delay": 2,  # リクエスト間隔（秒）
    "timeout": 30,  # タイムアウト（秒）
    "max_retries": 3,  # 最大リトライ回数
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "max_pages": 10,  # 最大取得ページ数（None = 全ページ）
}

# ===========================================
# データベース設定
# ===========================================

DATABASE_CONFIG = {
    "db_path": BASE_DIR / "data" / "properties.db",
    "backup_dir": BASE_DIR / "data" / "backups",
}

# ===========================================
# ランク付け設定
# ===========================================

# ランク閾値（総合スコア）
RANK_THRESHOLDS = {
    "S": 90,  # 90点以上
    "A": 80,  # 80-89点
    "B": 70,  # 70-79点
    "C": 60,  # 60-69点
    "D": 0,   # 60点未満
}

# 評価項目の重み付け（合計100%）
RANKING_WEIGHTS = {
    "price": 0.30,      # 価格評価（30%）
    "location": 0.30,   # 立地評価（30%）
    "area": 0.20,       # 面積評価（20%）
    "investment": 0.20, # 投資価値評価（20%）
}

# 価格評価基準（坪単価：万円）
PRICE_CRITERIA = {
    "excellent": 10,  # 10万円/坪以下 → 100点
    "very_good": 15,  # 15万円/坪以下 → 80点
    "good": 20,       # 20万円/坪以下 → 60点
    "fair": 25,       # 25万円/坪以下 → 40点
    "poor": 30,       # 30万円/坪以下 → 20点
}

# 立地評価（優良エリア）
PREMIUM_AREAS = [
    "中央町", "府内町", "都町", "金池町", "末広町",
    "千代町", "大手町", "荷揚町", "長浜町", "錦町",
    "城崎町", "東大道", "西大道", "大道町", "萩原"
]

# 駅距離評価基準（徒歩分）
STATION_DISTANCE_CRITERIA = {
    "excellent": 5,   # 5分以内 → 100点
    "very_good": 10,  # 10分以内 → 80点
    "good": 15,       # 15分以内 → 60点
    "fair": 20,       # 20分以内 → 40点
    "poor": 30,       # 30分以内 → 20点
}

# 面積評価基準（坪）
AREA_CRITERIA = {
    "excellent": 100,  # 100坪以上 → 100点
    "very_good": 70,   # 70坪以上 → 80点
    "good": 50,        # 50坪以上 → 60点
    "fair": 30,        # 30坪以上 → 40点
    "poor": 20,        # 20坪以上 → 20点
}

# 投資価値評価基準
INVESTMENT_CRITERIA = {
    "建ぺい率": {
        80: 100,  # 80%以上 → 100点
        70: 80,   # 70%以上 → 80点
        60: 60,   # 60%以上 → 60点
        50: 40,   # 50%以上 → 40点
    },
    "容積率": {
        400: 100,  # 400%以上 → 100点
        300: 80,   # 300%以上 → 80点
        200: 60,   # 200%以上 → 60点
        150: 40,   # 150%以上 → 40点
    }
}

# ===========================================
# 通知設定
# ===========================================

NOTIFICATION_CONFIG = {
    "enable_notification": True,  # 通知を有効化
    "notify_rank": ["S", "A"],   # 通知対象ランク
    "notify_new_only": True,      # 新規物件のみ通知
}

# LINE通知設定（オプション）
LINE_NOTIFY_CONFIG = {
    "enabled": False,  # LINE通知を使用する場合はTrueに設定
    "access_token": "",  # LINE Notify のアクセストークン
}

# ===========================================
# ログ設定
# ===========================================

LOG_CONFIG = {
    "log_dir": BASE_DIR / "logs",
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_date_format": "%Y-%m-%d %H:%M:%S",
    "log_rotation": {
        "when": "midnight",  # 日次ローテーション
        "interval": 1,
        "backup_count": 30,  # 30日分保持
    }
}

# ===========================================
# 出力設定
# ===========================================

OUTPUT_CONFIG = {
    "export_dir": BASE_DIR / "exports",
    "export_formats": ["csv", "excel", "json"],  # エクスポート形式
    "include_inactive": False,  # 非アクティブ物件を含むか
}

# ===========================================
# 開発・デバッグ設定
# ===========================================

DEBUG_MODE = False  # デバッグモード
TEST_MODE = False   # テストモード（実際のスクレイピングを行わない）
SAMPLE_DATA_FILE = BASE_DIR / "tests" / "sample_data.json"  # テスト用サンプルデータ

# ===========================================
# スケジュール設定（参考用）
# ===========================================

SCHEDULE_CONFIG = {
    "cron_expression": "0 9,12,15,17 * * *",  # 毎日9時、12時、15時、17時に実行
    "timezone": "Asia/Tokyo",
}