#!/usr/bin/env python
"""
デモンストレーション用テストスクリプト
実際のスクレイピングを行わずにシステムの動作を確認
"""
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import PropertyDatabase
from src.ranking import PropertyRanker
from config.athome_scraper_config import *


def test_database():
    """データベース機能のテスト"""
    print("="*60)
    print("📊 データベース機能のテスト")
    print("="*60)
    
    # データベース初期化
    db = PropertyDatabase(DATABASE_CONFIG['db_path'])
    print("✅ データベースを初期化しました")
    
    # サンプル物件データ
    sample_properties = [
        {
            'property_id': 'test_001',
            'url': 'https://example.com/property/001',
            'title': '大分市中央町 売土地 100坪',
            'price': '1,000万円',
            'price_numeric': 1000,
            'address': '大分県大分市中央町1-2-3',
            'land_area': '330.58㎡（100坪）',
            'land_area_tsubo': 100,
            'land_area_m2': 330.58,
            'nearest_station': '大分駅 徒歩5分',
            'walk_minutes': 5,
            'building_coverage': 80,
            'floor_area_ratio': 400,
            'usage_area': '商業地域',
        },
        {
            'property_id': 'test_002',
            'url': 'https://example.com/property/002',
            'title': '大分市萩原 売土地 50坪',
            'price': '800万円',
            'price_numeric': 800,
            'address': '大分県大分市萩原4-5-6',
            'land_area': '165.29㎡（50坪）',
            'land_area_tsubo': 50,
            'land_area_m2': 165.29,
            'nearest_station': '大分駅 徒歩15分',
            'walk_minutes': 15,
            'building_coverage': 60,
            'floor_area_ratio': 200,
            'usage_area': '第一種住居地域',
        },
        {
            'property_id': 'test_003',
            'url': 'https://example.com/property/003',
            'title': '大分市明野北 売土地 30坪',
            'price': '600万円',
            'price_numeric': 600,
            'address': '大分県大分市明野北1-2-3',
            'land_area': '99.17㎡（30坪）',
            'land_area_tsubo': 30,
            'land_area_m2': 99.17,
            'nearest_station': '大分駅 バス20分',
            'walk_minutes': 30,
            'building_coverage': 50,
            'floor_area_ratio': 100,
            'usage_area': '第一種低層住居専用地域',
        }
    ]
    
    # 物件を追加
    for prop in sample_properties:
        is_new, prop_id = db.upsert_property(prop)
        status = "新規追加" if is_new else "更新"
        print(f"  {status}: {prop['title']}")
    
    print("\n✅ サンプル物件をデータベースに追加しました")
    return db, sample_properties


def test_ranking(db, sample_properties):
    """ランク付け機能のテスト"""
    print("\n" + "="*60)
    print("🏆 ランク付け機能のテスト")
    print("="*60)
    
    # ランカーを初期化
    config = {
        'RANK_THRESHOLDS': RANK_THRESHOLDS,
        'RANKING_WEIGHTS': RANKING_WEIGHTS,
        'PRICE_CRITERIA': PRICE_CRITERIA,
        'PREMIUM_AREAS': PREMIUM_AREAS,
        'STATION_DISTANCE_CRITERIA': STATION_DISTANCE_CRITERIA,
        'AREA_CRITERIA': AREA_CRITERIA,
        'INVESTMENT_CRITERIA': INVESTMENT_CRITERIA,
    }
    ranker = PropertyRanker(config)
    
    # 各物件をランク付け
    print("\n【ランク付け結果】")
    for prop in sample_properties:
        rank_info = ranker.calculate_rank(prop)
        prop.update(rank_info)
        
        # データベースを更新
        db.upsert_property(prop)
        
        # 結果を表示
        print(f"\n物件: {prop['title']}")
        print(f"  住所: {prop['address']}")
        print(f"  価格: {prop['price']} ({prop['price_numeric']/prop['land_area_tsubo']:.1f}万円/坪)")
        print(f"  面積: {prop['land_area']}")
        print(f"  評価スコア:")
        print(f"    - 価格評価: {rank_info['price_evaluation']:.1f}点")
        print(f"    - 立地評価: {rank_info['location_evaluation']:.1f}点")
        print(f"    - 面積評価: {rank_info['area_evaluation']:.1f}点")
        print(f"    - 投資価値: {rank_info['investment_evaluation']:.1f}点")
        print(f"  📊 総合スコア: {rank_info['ranking_score']:.1f}点")
        print(f"  🏅 ランク: {rank_info['ranking_grade']}級")


def test_statistics(db):
    """統計機能のテスト"""
    print("\n" + "="*60)
    print("📈 統計機能のテスト")
    print("="*60)
    
    stats = db.get_statistics()
    
    print(f"\nアクティブ物件数: {stats.get('total_active_properties', 0)}件")
    
    if stats.get('properties_by_rank'):
        print("\n【ランク別物件数】")
        for rank in ['S', 'A', 'B', 'C', 'D']:
            count = stats['properties_by_rank'].get(rank, 0)
            bar = '█' * (count * 5) if count > 0 else ''
            print(f"  {rank}級: {count}件 {bar}")
    
    if stats.get('high_rank_properties'):
        print("\n【高ランク物件】")
        for prop in stats['high_rank_properties']:
            print(f"  {prop['ranking_grade']}級 ({prop['ranking_score']:.1f}点) - {prop['title']}")
            print(f"    {prop['price']} - {prop['address']}")


def test_export(db):
    """エクスポート機能のテスト"""
    print("\n" + "="*60)
    print("💾 エクスポート機能のテスト")
    print("="*60)
    
    export_dir = OUTPUT_CONFIG.get('export_dir', BASE_DIR / 'exports')
    export_dir.mkdir(parents=True, exist_ok=True)
    
    csv_file = export_dir / f"test_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    db.export_to_csv(csv_file)
    
    if csv_file.exists():
        print(f"✅ CSVファイルを出力しました: {csv_file}")
        print(f"   ファイルサイズ: {csv_file.stat().st_size} bytes")
    else:
        print("❌ CSVファイルの出力に失敗しました")


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("🏠 Athome Property Scraper - デモンストレーション")
    print("="*70)
    print("\nこれはテスト用のデモです。実際のスクレイピングは行いません。")
    print("システムの主要機能を確認します。\n")
    
    try:
        # 各機能をテスト
        db, sample_properties = test_database()
        test_ranking(db, sample_properties)
        test_statistics(db)
        test_export(db)
        
        print("\n" + "="*70)
        print("✅ すべてのテストが正常に完了しました！")
        print("="*70)
        print("\n実際のスクレイピングを実行するには:")
        print("  python scripts/run_scraper.py")
        print("\n注意: 実際のスクレイピングを行う前に、必ず対象サイトの")
        print("      利用規約とrobots.txtを確認してください。")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()