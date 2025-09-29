#!/usr/bin/env python
"""
Athome Property Scraper 実行スクリプト
"""
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.athome_scraper_config import *
from src.selenium_scraper import SeleniumAthomeScraper
from src.database import PropertyDatabase


def setup_logging():
    """ロギングを設定"""
    log_dir = LOG_CONFIG['log_dir']
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # ログファイル名（日付付き）
    log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"
    
    # ロギング設定
    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG['log_level']),
        format=LOG_CONFIG['log_format'],
        datefmt=LOG_CONFIG['log_date_format'],
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 外部ライブラリのログレベルを調整
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def run_scraping():
    """スクレイピングを実行"""
    logger = setup_logging()
    logger.info("="*60)
    logger.info("Athome Property Scraper 起動")
    logger.info("="*60)
    
    try:
        # 設定を辞書化
        config = {
            'ATHOME_BASE_URL': ATHOME_BASE_URL,
            'ATHOME_SEARCH_URL': ATHOME_SEARCH_URL,
            'SCRAPING_CONFIG': SCRAPING_CONFIG,
            'DATABASE_CONFIG': DATABASE_CONFIG,
            'RANK_THRESHOLDS': RANK_THRESHOLDS,
            'RANKING_WEIGHTS': RANKING_WEIGHTS,
            'PRICE_CRITERIA': PRICE_CRITERIA,
            'PREMIUM_AREAS': PREMIUM_AREAS,
            'STATION_DISTANCE_CRITERIA': STATION_DISTANCE_CRITERIA,
            'AREA_CRITERIA': AREA_CRITERIA,
            'INVESTMENT_CRITERIA': INVESTMENT_CRITERIA,
        }
        
        # Seleniumスクレイパーを実行
        scraper = SeleniumAthomeScraper(config)
        stats = scraper.scrape_all()
        
        # 結果サマリーを表示
        logger.info("\n" + "="*60)
        logger.info("実行結果サマリー")
        logger.info("="*60)
        logger.info(f"総処理件数: {stats['total_properties']}件")
        logger.info(f"新規物件: {stats['new_properties']}件")
        logger.info(f"更新物件: {stats['updated_properties']}件")
        logger.info(f"エラー: {stats['errors']}件")
        
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            logger.info(f"実行時間: {duration:.1f}秒")
        
        # 高ランク物件を表示
        db = PropertyDatabase(DATABASE_CONFIG['db_path'])
        high_rank_properties = db.get_active_properties(['S', 'A'])
        
        if high_rank_properties:
            logger.info("\n" + "="*60)
            logger.info("🏆 高ランク物件（S/A級）")
            logger.info("="*60)
            
            for prop in high_rank_properties[:5]:  # 上位5件
                logger.info(
                    f"{prop['ranking_grade']}級 ({prop['ranking_score']:.1f}点) - "
                    f"{prop['title']} - {prop['price']} - {prop['address']}"
                )
        
        # CSVエクスポート
        if OUTPUT_CONFIG.get('export_formats') and 'csv' in OUTPUT_CONFIG['export_formats']:
            export_dir = OUTPUT_CONFIG.get('export_dir', BASE_DIR / 'exports')
            export_dir.mkdir(parents=True, exist_ok=True)
            
            csv_file = export_dir / f"properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            db.export_to_csv(csv_file, rank_filter=['S', 'A', 'B'])
            logger.info(f"\nCSVファイルを出力しました: {csv_file}")
        
        logger.info("\n" + "="*60)
        logger.info("スクレイピング正常終了")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


def show_status():
    """現在のステータスを表示"""
    logger = setup_logging()
    
    try:
        db = PropertyDatabase(DATABASE_CONFIG['db_path'])
        stats = db.get_statistics()
        
        print("\n" + "="*60)
        print("📊 Athome Property Scraper ステータス")
        print("="*60)
        
        # 総物件数
        print(f"アクティブ物件数: {stats.get('total_active_properties', 0)}件")
        
        # ランク別
        if stats.get('properties_by_rank'):
            print("\n【ランク別物件数】")
            for rank in ['S', 'A', 'B', 'C', 'D']:
                count = stats['properties_by_rank'].get(rank, 0)
                bar = '█' * (count // 2) if count > 0 else ''
                print(f"  {rank}級: {count:3d}件 {bar}")
        
        # 最終実行
        if stats.get('last_scraping'):
            print(f"\n【最終スクレイピング】")
            print(f"  実行時刻: {stats['last_scraping']['time']}")
            print(f"  新規物件: {stats['last_scraping']['new_properties']}件")
            print(f"  総件数: {stats['last_scraping']['total_properties']}件")
        
        # 高ランク物件
        if stats.get('high_rank_properties'):
            print("\n【高ランク物件 TOP5】")
            for i, prop in enumerate(stats['high_rank_properties'][:5], 1):
                print(f"  {i}. {prop['ranking_grade']}級 ({prop['ranking_score']:.1f}点)")
                print(f"     {prop['title'][:30]}...")
                print(f"     {prop['price']} - {prop['address'][:20]}")
                print()
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"ステータス表示エラー: {e}")
        sys.exit(1)


def show_help():
    """ヘルプを表示"""
    print("""
Athome Property Scraper - 大分市売土地情報自動収集システム

使用方法:
    python run_scraper.py [コマンド]

コマンド:
    run      - スクレイピングを実行（デフォルト）
    status   - 現在のステータスを表示
    help     - このヘルプを表示

例:
    python run_scraper.py            # スクレイピング実行
    python run_scraper.py status     # ステータス確認
    python run_scraper.py help       # ヘルプ表示

設定ファイル:
    config/athome_scraper_config.py で各種設定を変更できます
    
ログファイル:
    logs/scraper_YYYYMMDD.log に実行ログが保存されます
    """)


def main():
    """メイン処理"""
    # コマンドライン引数を処理
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            show_status()
        elif command == 'help' or command == '-h' or command == '--help':
            show_help()
        elif command == 'run':
            run_scraping()
        else:
            print(f"不明なコマンド: {command}")
            print("使用方法: python run_scraper.py [run|status|help]")
            sys.exit(1)
    else:
        # デフォルトはスクレイピング実行
        run_scraping()


if __name__ == "__main__":
    main()