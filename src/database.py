"""
データベース管理モジュール
SQLiteを使用した物件情報の永続化
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PropertyDatabase:
    """物件データベース管理クラス"""
    
    def __init__(self, db_path: str):
        """
        データベースを初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """データベースとテーブルを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 物件情報テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price TEXT,
                    price_numeric INTEGER,
                    address TEXT,
                    land_area TEXT,
                    land_area_tsubo REAL,
                    land_area_m2 REAL,
                    nearest_station TEXT,
                    walk_time TEXT,
                    walk_minutes INTEGER,
                    building_coverage REAL,
                    floor_area_ratio REAL,
                    land_rights TEXT,
                    city_planning TEXT,
                    usage_area TEXT,
                    contact_info TEXT,
                    features TEXT,
                    description TEXT,
                    image_urls TEXT,
                    ranking_score REAL,
                    ranking_grade TEXT,
                    price_evaluation REAL,
                    location_evaluation REAL,
                    area_evaluation REAL,
                    investment_evaluation REAL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    raw_data TEXT
                )
            """)
            
            # スクレイピングログテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_properties INTEGER DEFAULT 0,
                    new_properties INTEGER DEFAULT 0,
                    updated_properties INTEGER DEFAULT 0,
                    deactivated_properties INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    status TEXT,
                    message TEXT,
                    duration_seconds REAL
                )
            """)
            
            # プロパティ変更履歴テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS property_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id TEXT NOT NULL,
                    change_type TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties(property_id)
                )
            """)
            
            # インデックスの作成
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_property_id ON properties(property_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ranking_grade ON properties(ranking_grade)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON properties(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_at ON properties(scraped_at)")
            
            conn.commit()
            logger.info(f"データベースを初期化しました: {self.db_path}")
    
    def upsert_property(self, property_data: Dict) -> Tuple[bool, str]:
        """
        物件情報を挿入または更新
        
        Args:
            property_data: 物件データの辞書
        
        Returns:
            (is_new, property_id): 新規物件かどうかとプロパティID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            property_id = property_data.get('property_id')
            
            # 既存データの確認
            cursor.execute("SELECT * FROM properties WHERE property_id = ?", (property_id,))
            existing = cursor.fetchone()
            
            # JSON形式のデータを文字列に変換
            if 'image_urls' in property_data and isinstance(property_data['image_urls'], list):
                property_data['image_urls'] = json.dumps(property_data['image_urls'])
            
            if 'raw_data' in property_data and isinstance(property_data['raw_data'], dict):
                property_data['raw_data'] = json.dumps(property_data['raw_data'])
            
            if existing:
                # 更新
                update_fields = []
                update_values = []
                
                for key, value in property_data.items():
                    if key != 'property_id':
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                update_values.append(datetime.now())
                update_values.append(property_id)
                
                query = f"""
                    UPDATE properties 
                    SET {', '.join(update_fields)}, updated_at = ?
                    WHERE property_id = ?
                """
                
                cursor.execute(query, update_values)
                logger.debug(f"物件を更新しました: {property_id}")
                return False, property_id
            else:
                # 新規挿入
                columns = list(property_data.keys())
                placeholders = ['?' for _ in columns]
                values = list(property_data.values())
                
                query = f"""
                    INSERT INTO properties ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cursor.execute(query, values)
                logger.info(f"新規物件を追加しました: {property_id}")
                return True, property_id
    
    def get_property(self, property_id: str) -> Optional[Dict]:
        """
        物件情報を取得
        
        Args:
            property_id: 物件ID
        
        Returns:
            物件情報の辞書
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM properties WHERE property_id = ?", (property_id,))
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                # JSON文字列をパース
                if data.get('image_urls'):
                    try:
                        data['image_urls'] = json.loads(data['image_urls'])
                    except:
                        pass
                if data.get('raw_data'):
                    try:
                        data['raw_data'] = json.loads(data['raw_data'])
                    except:
                        pass
                return data
            return None
    
    def get_active_properties(self, rank_filter: Optional[List[str]] = None) -> List[Dict]:
        """
        アクティブな物件を取得
        
        Args:
            rank_filter: ランクでフィルタリング（例: ['S', 'A']）
        
        Returns:
            物件情報のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM properties WHERE is_active = 1"
            params = []
            
            if rank_filter:
                placeholders = ','.join(['?' for _ in rank_filter])
                query += f" AND ranking_grade IN ({placeholders})"
                params.extend(rank_filter)
            
            query += " ORDER BY ranking_score DESC, scraped_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            properties = []
            for row in rows:
                data = dict(row)
                # JSON文字列をパース
                if data.get('image_urls'):
                    try:
                        data['image_urls'] = json.loads(data['image_urls'])
                    except:
                        pass
                if data.get('raw_data'):
                    try:
                        data['raw_data'] = json.loads(data['raw_data'])
                    except:
                        pass
                properties.append(data)
            
            return properties
    
    def deactivate_old_properties(self, active_property_ids: List[str]):
        """
        リストにない物件を非アクティブ化
        
        Args:
            active_property_ids: アクティブな物件IDのリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if active_property_ids:
                placeholders = ','.join(['?' for _ in active_property_ids])
                query = f"""
                    UPDATE properties 
                    SET is_active = 0, updated_at = ?
                    WHERE property_id NOT IN ({placeholders}) AND is_active = 1
                """
                params = [datetime.now()] + active_property_ids
            else:
                query = "UPDATE properties SET is_active = 0, updated_at = ? WHERE is_active = 1"
                params = [datetime.now()]
            
            cursor.execute(query, params)
            deactivated = cursor.rowcount
            
            if deactivated > 0:
                logger.info(f"{deactivated}件の物件を非アクティブ化しました")
            
            return deactivated
    
    def log_scraping(self, log_data: Dict):
        """
        スクレイピング実行ログを記録
        
        Args:
            log_data: ログデータの辞書
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            columns = list(log_data.keys())
            placeholders = ['?' for _ in columns]
            values = list(log_data.values())
            
            query = f"""
                INSERT INTO scraping_logs ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            cursor.execute(query, values)
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 総物件数
            cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
            stats['total_active_properties'] = cursor.fetchone()[0]
            
            # ランク別件数
            cursor.execute("""
                SELECT ranking_grade, COUNT(*) as count 
                FROM properties 
                WHERE is_active = 1 
                GROUP BY ranking_grade
            """)
            stats['properties_by_rank'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 最終スクレイピング時刻
            cursor.execute("""
                SELECT execution_time, new_properties, total_properties 
                FROM scraping_logs 
                ORDER BY execution_time DESC 
                LIMIT 1
            """)
            last_scraping = cursor.fetchone()
            if last_scraping:
                stats['last_scraping'] = {
                    'time': last_scraping[0],
                    'new_properties': last_scraping[1],
                    'total_properties': last_scraping[2]
                }
            
            # 高ランク物件（S,A）
            cursor.execute("""
                SELECT property_id, title, price, address, ranking_grade, ranking_score 
                FROM properties 
                WHERE is_active = 1 AND ranking_grade IN ('S', 'A')
                ORDER BY ranking_score DESC 
                LIMIT 10
            """)
            stats['high_rank_properties'] = [
                {
                    'property_id': row[0],
                    'title': row[1],
                    'price': row[2],
                    'address': row[3],
                    'ranking_grade': row[4],
                    'ranking_score': row[5]
                }
                for row in cursor.fetchall()
            ]
            
            return stats
    
    def export_to_csv(self, output_path: str, rank_filter: Optional[List[str]] = None):
        """
        CSVファイルにエクスポート
        
        Args:
            output_path: 出力ファイルパス
            rank_filter: ランクフィルター
        """
        import csv
        
        properties = self.get_active_properties(rank_filter)
        
        if not properties:
            logger.warning("エクスポートする物件がありません")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV用のフィールドを準備
        fieldnames = [
            'property_id', 'title', 'price', 'address', 'land_area', 'land_area_tsubo',
            'nearest_station', 'walk_time', 'ranking_grade', 'ranking_score',
            'price_evaluation', 'location_evaluation', 'area_evaluation', 'investment_evaluation',
            'url', 'scraped_at'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(properties)
        
        logger.info(f"CSVファイルを出力しました: {output_path} ({len(properties)}件)")