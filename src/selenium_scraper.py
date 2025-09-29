"""
Selenium版 Athome Property Scraper
ブラウザ自動化でCAPTCHA回避
"""
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from .database import PropertyDatabase
from .ranking import PropertyRanker

logger = logging.getLogger(__name__)


class SeleniumAthomeScraper:
    """Selenium版Athome物件スクレイパークラス"""
    
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
        
        # Chrome オプション設定（ボット検出を回避）
        self.chrome_options = Options()
        
        # 自動化検出を回避する設定
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # プロファイル設定（実際のユーザーのように見せる）
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--start-maximized")
        
        # 言語設定
        self.chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'ja,en-US;q=0.9,en;q=0.8'
        })
        
        # User-Agent設定（最新のChromeバージョン）
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        self.chrome_options.add_argument(f'user-agent={user_agent}')
        
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
        
        self.driver = None
    
    def _init_driver(self):
        """WebDriverを初期化"""
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.implicitly_wait(10)
            
            # JavaScriptでボット検出を回避
            stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ja', 'en-US', 'en']
                });
                
                window.navigator.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                });
            """
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            
            logger.info("WebDriverを初期化しました（ステルスモード）")
        except Exception as e:
            logger.error(f"WebDriver初期化エラー: {e}")
            raise
    
    def _close_driver(self):
        """WebDriverを閉じる"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("WebDriverを終了しました")
    
    def scrape_all(self) -> Dict:
        """
        全物件をスクレイピング
        
        Returns:
            スクレイピング結果の統計
        """
        logger.info("Seleniumスクレイピングを開始します")
        self.stats['start_time'] = datetime.now()
        
        try:
            # WebDriver初期化
            self._init_driver()
            
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
        finally:
            self._close_driver()
    
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
                
                # ページを取得（ゆっくりとアクセス）
                if page == 1:
                    # 最初はホームページにアクセスしてクッキーを取得
                    self.driver.get(self.base_url)
                    time.sleep(3)  # 人間らしい待機時間
                
                self.driver.get(url)
                time.sleep(2)  # ページ読み込み待機
                
                # スクロールして人間らしい動作をシミュレート
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
                time.sleep(1)
                
                # CAPTCHAチェック
                page_source = self.driver.page_source
                if "認証にご協力ください" in page_source or "captcha" in page_source.lower():
                    logger.warning("CAPTCHA検出。手動で解決してください...")
                    logger.info("パズル認証を完了させてから、Enterキーを押してください")
                    input("解決したらEnter: ")
                    # 解決後、ページを再読み込み
                    self.driver.refresh()
                    time.sleep(3)
                
                # ページが完全に読み込まれるまで待機
                wait = WebDriverWait(self.driver, 30)
                
                # 物件リンクを取得
                property_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    'a[href*="/kodate/"], a[href*="/tochi/"], .property-item a, .item-title a')
                
                if not property_elements:
                    logger.warning(f"ページ{page}で物件が見つかりません")
                    # ページソースを確認
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    # より広範なセレクタで再検索
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if any(keyword in href for keyword in ['/kodate/', '/tochi/', '/bukken/', '/detail/']):
                            full_url = urljoin(self.base_url, href)
                            property_urls.append(full_url)
                            logger.info(f"物件URL発見: {full_url}")
                    
                    if not property_urls:
                        break
                else:
                    # URLを収集
                    for element in property_elements:
                        href = element.get_attribute('href')
                        if href:
                            property_urls.append(href)
                            logger.info(f"物件URL取得: {href}")
                
                logger.info(f"ページ{page}から{len(property_elements)}件の物件を取得")
                
                # 次のページボタンを探す
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 
                        'a.next-page, .pagination .next a, a[rel="next"]')
                    if not next_button.is_enabled() or (max_pages and page >= max_pages):
                        break
                except:
                    logger.info("次のページが見つかりません")
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
            self.driver.get(url)
            
            # ページが完全に読み込まれるまで待機
            wait = WebDriverWait(self.driver, 20)
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 物件IDを生成（URLから）
            property_id = self._extract_property_id(url)
            
            # 基本情報を抽出
            data = {
                'property_id': property_id,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # タイトル
            title_elem = soup.select_one('h1, .property-title, .bukken-title, .item-title')
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
            address_elem = soup.select_one('.address, .jusho, [class*="address"], .item-address')
            data['address'] = address_elem.get_text(strip=True) if address_elem else ''
            
            # 土地面積
            area_elem = soup.select_one('[class*="area"], [class*="menseki"], .land-area')
            if area_elem:
                area_text = area_elem.get_text(strip=True)
                data['land_area'] = area_text
                
                # 平米を抽出
                m2_match = re.search(r'([\d,]+\.?\d*)\s*(?:m2|㎡)', area_text)
                if m2_match:
                    land_area_m2 = float(m2_match.group(1).replace(',', ''))
                    data['land_area_m2'] = land_area_m2
                    data['land_area_tsubo'] = land_area_m2 / 3.305785  # 坪に変換
                
                # 坪を直接抽出
                tsubo_match = re.search(r'([\d,]+\.?\d*)\s*坪', area_text)
                if tsubo_match:
                    data['land_area_tsubo'] = float(tsubo_match.group(1).replace(',', ''))
            
            # 最寄駅
            station_elem = soup.select_one('[class*="station"], [class*="eki"], .access')
            if station_elem:
                station_text = station_elem.get_text(strip=True)
                data['nearest_station'] = station_text
                
                # 徒歩時間を抽出
                walk_match = re.search(r'徒歩\s*(\d+)\s*分', station_text)
                if walk_match:
                    data['walk_time'] = f"徒歩{walk_match.group(1)}分"
                    data['walk_minutes'] = int(walk_match.group(1))
            
            # 建ぺい率・容積率
            coverage_elem = soup.select_one('[class*="kenpei"], .building-coverage')
            if coverage_elem:
                coverage_text = coverage_elem.get_text(strip=True)
                coverage_match = re.search(r'(\d+)\s*[%％]', coverage_text)
                if coverage_match:
                    data['building_coverage'] = float(coverage_match.group(1))
            
            ratio_elem = soup.select_one('[class*="yoseki"], .floor-area-ratio')
            if ratio_elem:
                ratio_text = ratio_elem.get_text(strip=True)
                ratio_match = re.search(r'(\d+)\s*[%％]', ratio_text)
                if ratio_match:
                    data['floor_area_ratio'] = float(ratio_match.group(1))
            
            # 用途地域
            usage_elem = soup.select_one('[class*="youto"], [class*="chiiki"], .usage-area')
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
        id_match = re.search(r'/(\d+)(?:/|$|\?)', url)
        if id_match:
            return f"athome_{id_match.group(1)}"
        
        # フォールバック：URLのハッシュ値
        import hashlib
        return f"athome_{hashlib.md5(url.encode()).hexdigest()[:10]}"