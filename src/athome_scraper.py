"""
Athome Property Scraper メインモジュール
大分市の売土地情報を自動収集
"""
import re
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .database import PropertyDatabase
from .ranking import PropertyRanker

logger = logging.getLogger(__name__)


class AthomeScraper:
    """Athome物件スクレイパークラス"""
    
    def __init__(self, config: Dict):
        """
        スクレイパーを初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.base_url = config.get('ATHOME_BASE_URL', 'https://www.athome.co.jp')
        self.search_url = config.get('ATHOME_SEARCH_URL')
        self.scraping_config = config.get('SCRAPING_CONFIG', {})
        
        # セッション設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.scraping_config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        })
        
        # データベースとランカーの初期化
        db_path = config.get('DATABASE_CONFIG', {}).get('db_path', 'data/properties.db')
        self.db = PropertyDatabase(db_path)
        self.ranker = PropertyRanker(config)
        
        # スクレイピング統計
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_properties': 0,
            'new_properties': 0,
            'updated_properties': 0,
            'errors': 0
        }
    
    def scrape_all(self) -> Dict:
        """
        全物件をスクレイピング
        
        Returns:
            スクレイピング結果の統計
        """
        logger.info("スクレイピングを開始します")
        self.stats['start_time'] = datetime.now()
        
        try:
            # ページリストを取得
            property_urls = self._get_property_urls()
            logger.info(f"{len(property_urls)}件の物件URLを取得しました")
            
            # 各物件の詳細を取得
            active_property_ids = []
            for i, url in enumerate(property_urls, 1):
                try:
                    logger.info(f"処理中: {i}/{len(property_urls)} - {url}")
                    property_data = self._scrape_property_detail(url)
                    
                    if property_data:
                        # ランク付け
                        rank_info = self.ranker.calculate_rank(property_data)
                        property_data.update(rank_info)
                        
                        # データベースに保存
                        is_new, property_id = self.db.upsert_property(property_data)
                        active_property_ids.append(property_id)
                        
                        if is_new:
                            self.stats['new_properties'] += 1
                            logger.info(f"新規物件: {property_data.get('title')} - {rank_info['ranking_grade']}級")
                        else:
                            self.stats['updated_properties'] += 1
                        
                        self.stats['total_properties'] += 1
                    
                    # リクエスト間隔
                    time.sleep(self.scraping_config.get('request_delay', 2))
                    
                except Exception as e:
                    logger.error(f"物件処理エラー: {url} - {e}")
                    self.stats['errors'] += 1
                    continue
            
            # 古い物件を非アクティブ化
            deactivated = self.db.deactivate_old_properties(active_property_ids)
            
            # 統計を更新
            self.stats['end_time'] = datetime.now()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            # ログを記録
            self.db.log_scraping({
                'total_properties': self.stats['total_properties'],
                'new_properties': self.stats['new_properties'],
                'updated_properties': self.stats['updated_properties'],
                'deactivated_properties': deactivated,
                'errors': self.stats['errors'],
                'status': 'completed',
                'message': f"正常終了: {self.stats['total_properties']}件処理",
                'duration_seconds': duration
            })
            
            logger.info(f"スクレイピング完了: {self.stats}")
            return self.stats
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            self.stats['end_time'] = datetime.now()
            
            # エラーログを記録
            self.db.log_scraping({
                'total_properties': self.stats['total_properties'],
                'new_properties': self.stats['new_properties'],
                'updated_properties': self.stats['updated_properties'],
                'errors': self.stats['errors'] + 1,
                'status': 'error',
                'message': str(e),
                'duration_seconds': (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            })
            
            raise
    
    def _get_property_urls(self) -> List[str]:
        """
        物件URLのリストを取得
        
        Returns:
            物件URLのリスト
        """
        property_urls = []
        page = 1
        max_pages = self.scraping_config.get('max_pages', 10)
        
        while True:
            try:
                # ページURLを構築
                if page == 1:
                    url = self.search_url
                else:
                    url = f"{self.search_url}?page={page}"
                
                logger.info(f"ページ{page}を取得中: {url}")
                
                # ページを取得
                response = self.session.get(
                    url,
                    timeout=self.scraping_config.get('timeout', 30)
                )
                response.raise_for_status()
                
                # HTMLをパース
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 物件リンクを抽出（サイト構造に応じて調整必要）
                property_links = soup.select('a.property-link, .bukken-link a, .item-link')
                
                if not property_links:
                    # 別のセレクタを試す
                    property_links = soup.select('[class*="property"] a[href*="/detail/"], [class*="bukken"] a[href*="/detail/"]')
                
                if not property_links:
                    logger.warning(f"ページ{page}で物件が見つかりません")
                    break
                
                # URLを収集
                for link in property_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if '/detail/' in full_url or '/bukken/' in full_url:
                            property_urls.append(full_url)
                
                logger.info(f"ページ{page}から{len(property_links)}件の物件を取得")
                
                # 次のページがあるかチェック
                next_button = soup.select_one('a.next-page, .pagination .next a, [class*="next"]')
                if not next_button or (max_pages and page >= max_pages):
                    break
                
                page += 1
                time.sleep(self.scraping_config.get('request_delay', 2))
                
            except Exception as e:
                logger.error(f"ページ取得エラー: ページ{page} - {e}")
                break
        
        # 重複を除去
        property_urls = list(set(property_urls))
        return property_urls
    
    def _scrape_property_detail(self, url: str) -> Optional[Dict]:
        """
        物件詳細をスクレイピング
        
        Args:
            url: 物件詳細URL
        
        Returns:
            物件データの辞書
        """
        try:
            response = self.session.get(
                url,
                timeout=self.scraping_config.get('timeout', 30)
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 物件IDを生成（URLから）
            property_id = self._extract_property_id(url)
            
            # 基本情報を抽出
            data = {
                'property_id': property_id,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # タイトル
            title_elem = soup.select_one('h1, .property-title, .bukken-title')
            data['title'] = title_elem.get_text(strip=True) if title_elem else 'タイトルなし'
            
            # 価格
            price_elem = soup.select_one('.price, .kakaku, [class*="price"]')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                data['price'] = price_text
                # 数値を抽出（万円）
                price_match = re.search(r'([\d,]+)\s*万円', price_text)
                if price_match:
                    data['price_numeric'] = int(price_match.group(1).replace(',', ''))
            
            # 住所
            address_elem = soup.select_one('.address, .jusho, [class*="address"]')
            data['address'] = address_elem.get_text(strip=True) if address_elem else ''
            
            # 土地面積
            area_elem = soup.select_one('[class*="area"], [class*="menseki"]')
            if area_elem:
                area_text = area_elem.get_text(strip=True)
                data['land_area'] = area_text
                
                # 平米を抽出
                m2_match = re.search(r'([\d,]+\.?\d*)\s*m2|㎡', area_text)
                if m2_match:
                    land_area_m2 = float(m2_match.group(1).replace(',', ''))
                    data['land_area_m2'] = land_area_m2
                    data['land_area_tsubo'] = land_area_m2 / 3.305785  # 坪に変換
                
                # 坪を直接抽出
                tsubo_match = re.search(r'([\d,]+\.?\d*)\s*坪', area_text)
                if tsubo_match:
                    data['land_area_tsubo'] = float(tsubo_match.group(1).replace(',', ''))
            
            # 最寄駅
            station_elem = soup.select_one('[class*="station"], [class*="eki"]')
            if station_elem:
                station_text = station_elem.get_text(strip=True)
                data['nearest_station'] = station_text
                
                # 徒歩時間を抽出
                walk_match = re.search(r'徒歩\s*(\d+)\s*分', station_text)
                if walk_match:
                    data['walk_time'] = f"徒歩{walk_match.group(1)}分"
                    data['walk_minutes'] = int(walk_match.group(1))
            
            # 建ぺい率・容積率
            coverage_elem = soup.select_one('[class*="kenpei"]')
            if coverage_elem:
                coverage_text = coverage_elem.get_text(strip=True)
                coverage_match = re.search(r'(\d+)\s*[%％]', coverage_text)
                if coverage_match:
                    data['building_coverage'] = float(coverage_match.group(1))
            
            ratio_elem = soup.select_one('[class*="yoseki"]')
            if ratio_elem:
                ratio_text = ratio_elem.get_text(strip=True)
                ratio_match = re.search(r'(\d+)\s*[%％]', ratio_text)
                if ratio_match:
                    data['floor_area_ratio'] = float(ratio_match.group(1))
            
            # 用途地域
            usage_elem = soup.select_one('[class*="youto"], [class*="chiiki"]')
            data['usage_area'] = usage_elem.get_text(strip=True) if usage_elem else ''
            
            # 画像URL
            image_urls = []
            for img in soup.select('.property-image img, .bukken-image img, [class*="photo"] img'):
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    image_urls.append(urljoin(self.base_url, img_url))
            data['image_urls'] = image_urls[:5]  # 最大5枚
            
            # 生データを保存（デバッグ用）
            data['raw_data'] = {
                'title': data.get('title'),
                'price': data.get('price'),
                'address': data.get('address')
            }
            
            return data
            
        except Exception as e:
            logger.error(f"物件詳細取得エラー: {url} - {e}")
            return None
    
    def _extract_property_id(self, url: str) -> str:
        """
        URLから物件IDを抽出
        
        Args:
            url: 物件URL
        
        Returns:
            物件ID
        """
        # URLパスから数値部分を抽出
        path = urlparse(url).path
        id_match = re.search(r'/(\d+)', path)
        if id_match:
            return f"athome_{id_match.group(1)}"
        
        # フォールバック：URLのハッシュ値
        import hashlib
        return f"athome_{hashlib.md5(url.encode()).hexdigest()[:10]}"