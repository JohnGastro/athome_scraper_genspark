"""
物件ランク付けアルゴリズム
価格、立地、面積、投資価値の4軸で総合評価
"""
import re
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PropertyRanker:
    """物件ランク付けクラス"""
    
    def __init__(self, config: Dict):
        """
        ランク付けエンジンを初期化
        
        Args:
            config: 設定辞書
        """
        self.rank_thresholds = config.get('RANK_THRESHOLDS', {
            "S": 90, "A": 80, "B": 70, "C": 60, "D": 0
        })
        self.weights = config.get('RANKING_WEIGHTS', {
            "price": 0.30,
            "location": 0.30,
            "area": 0.20,
            "investment": 0.20
        })
        self.price_criteria = config.get('PRICE_CRITERIA', {
            "excellent": 10, "very_good": 15, "good": 20, "fair": 25, "poor": 30
        })
        self.premium_areas = config.get('PREMIUM_AREAS', [])
        self.station_criteria = config.get('STATION_DISTANCE_CRITERIA', {
            "excellent": 5, "very_good": 10, "good": 15, "fair": 20, "poor": 30
        })
        self.area_criteria = config.get('AREA_CRITERIA', {
            "excellent": 100, "very_good": 70, "good": 50, "fair": 30, "poor": 20
        })
        self.investment_criteria = config.get('INVESTMENT_CRITERIA', {})
    
    def calculate_rank(self, property_data: Dict) -> Dict:
        """
        物件のランクを計算
        
        Args:
            property_data: 物件データ
        
        Returns:
            ランク情報を含む辞書
        """
        # 各評価項目のスコアを計算
        price_score = self._evaluate_price(property_data)
        location_score = self._evaluate_location(property_data)
        area_score = self._evaluate_area(property_data)
        investment_score = self._evaluate_investment(property_data)
        
        # 重み付き総合スコアを計算
        total_score = (
            price_score * self.weights['price'] +
            location_score * self.weights['location'] +
            area_score * self.weights['area'] +
            investment_score * self.weights['investment']
        )
        
        # ランクを判定
        rank_grade = self._determine_grade(total_score)
        
        result = {
            'ranking_score': round(total_score, 2),
            'ranking_grade': rank_grade,
            'price_evaluation': round(price_score, 2),
            'location_evaluation': round(location_score, 2),
            'area_evaluation': round(area_score, 2),
            'investment_evaluation': round(investment_score, 2)
        }
        
        logger.debug(f"ランク計算完了: {property_data.get('property_id')} - {rank_grade}級 ({total_score:.1f}点)")
        
        return result
    
    def _evaluate_price(self, property_data: Dict) -> float:
        """
        価格評価（坪単価ベース）
        
        Args:
            property_data: 物件データ
        
        Returns:
            価格スコア（0-100）
        """
        try:
            price_numeric = property_data.get('price_numeric', 0)
            land_area_tsubo = property_data.get('land_area_tsubo', 0)
            
            if price_numeric <= 0 or land_area_tsubo <= 0:
                return 50.0  # データ不足の場合は中間値
            
            # 坪単価を計算（万円）
            price_per_tsubo = price_numeric / land_area_tsubo
            
            # スコアを計算
            if price_per_tsubo <= self.price_criteria['excellent']:
                score = 100
            elif price_per_tsubo <= self.price_criteria['very_good']:
                score = 80
            elif price_per_tsubo <= self.price_criteria['good']:
                score = 60
            elif price_per_tsubo <= self.price_criteria['fair']:
                score = 40
            elif price_per_tsubo <= self.price_criteria['poor']:
                score = 20
            else:
                score = 10
            
            logger.debug(f"価格評価: 坪単価{price_per_tsubo:.1f}万円 → {score}点")
            return float(score)
            
        except Exception as e:
            logger.warning(f"価格評価でエラー: {e}")
            return 50.0
    
    def _evaluate_location(self, property_data: Dict) -> float:
        """
        立地評価（エリアと駅距離）
        
        Args:
            property_data: 物件データ
        
        Returns:
            立地スコア（0-100）
        """
        try:
            address = property_data.get('address', '')
            walk_minutes = property_data.get('walk_minutes', None)
            
            # エリア評価（50%）
            area_score = 50  # デフォルト
            for premium_area in self.premium_areas:
                if premium_area in address:
                    area_score = 100
                    logger.debug(f"プレミアムエリア: {premium_area}")
                    break
            
            # 駅距離評価（50%）
            if walk_minutes is not None:
                if walk_minutes <= self.station_criteria['excellent']:
                    station_score = 100
                elif walk_minutes <= self.station_criteria['very_good']:
                    station_score = 80
                elif walk_minutes <= self.station_criteria['good']:
                    station_score = 60
                elif walk_minutes <= self.station_criteria['fair']:
                    station_score = 40
                elif walk_minutes <= self.station_criteria['poor']:
                    station_score = 20
                else:
                    station_score = 10
            else:
                station_score = 30  # 駅情報なしの場合
            
            # 総合立地スコア
            total_location_score = (area_score * 0.5 + station_score * 0.5)
            
            logger.debug(f"立地評価: エリア{area_score}点, 駅距離{station_score}点 → {total_location_score}点")
            return float(total_location_score)
            
        except Exception as e:
            logger.warning(f"立地評価でエラー: {e}")
            return 50.0
    
    def _evaluate_area(self, property_data: Dict) -> float:
        """
        面積評価
        
        Args:
            property_data: 物件データ
        
        Returns:
            面積スコア（0-100）
        """
        try:
            land_area_tsubo = property_data.get('land_area_tsubo', 0)
            
            if land_area_tsubo <= 0:
                return 30.0  # データなしの場合
            
            # スコアを計算
            if land_area_tsubo >= self.area_criteria['excellent']:
                score = 100
            elif land_area_tsubo >= self.area_criteria['very_good']:
                score = 80
            elif land_area_tsubo >= self.area_criteria['good']:
                score = 60
            elif land_area_tsubo >= self.area_criteria['fair']:
                score = 40
            elif land_area_tsubo >= self.area_criteria['poor']:
                score = 20
            else:
                score = 10
            
            logger.debug(f"面積評価: {land_area_tsubo:.1f}坪 → {score}点")
            return float(score)
            
        except Exception as e:
            logger.warning(f"面積評価でエラー: {e}")
            return 30.0
    
    def _evaluate_investment(self, property_data: Dict) -> float:
        """
        投資価値評価（建ぺい率、容積率、用途地域など）
        
        Args:
            property_data: 物件データ
        
        Returns:
            投資価値スコア（0-100）
        """
        try:
            building_coverage = property_data.get('building_coverage', 0)
            floor_area_ratio = property_data.get('floor_area_ratio', 0)
            usage_area = property_data.get('usage_area', '')
            
            scores = []
            
            # 建ぺい率評価
            if building_coverage > 0:
                coverage_score = 50  # デフォルト
                for threshold, score in sorted(self.investment_criteria.get('建ぺい率', {}).items(), reverse=True):
                    if building_coverage >= threshold:
                        coverage_score = score
                        break
                scores.append(coverage_score)
                logger.debug(f"建ぺい率{building_coverage}% → {coverage_score}点")
            
            # 容積率評価
            if floor_area_ratio > 0:
                ratio_score = 50  # デフォルト
                for threshold, score in sorted(self.investment_criteria.get('容積率', {}).items(), reverse=True):
                    if floor_area_ratio >= threshold:
                        ratio_score = score
                        break
                scores.append(ratio_score)
                logger.debug(f"容積率{floor_area_ratio}% → {ratio_score}点")
            
            # 用途地域評価
            usage_score = 50  # デフォルト
            if '商業' in usage_area:
                usage_score = 90
            elif '近隣商業' in usage_area:
                usage_score = 80
            elif '準工業' in usage_area:
                usage_score = 70
            elif '第一種住居' in usage_area or '第二種住居' in usage_area:
                usage_score = 60
            elif '第一種低層' in usage_area or '第二種低層' in usage_area:
                usage_score = 40
            
            scores.append(usage_score)
            logger.debug(f"用途地域: {usage_area} → {usage_score}点")
            
            # 平均スコアを返す
            if scores:
                avg_score = sum(scores) / len(scores)
                return float(avg_score)
            else:
                return 50.0  # データなしの場合
                
        except Exception as e:
            logger.warning(f"投資価値評価でエラー: {e}")
            return 50.0
    
    def _determine_grade(self, total_score: float) -> str:
        """
        総合スコアからランクを判定
        
        Args:
            total_score: 総合スコア
        
        Returns:
            ランク（S, A, B, C, D）
        """
        for grade in ['S', 'A', 'B', 'C']:
            if total_score >= self.rank_thresholds[grade]:
                return grade
        return 'D'
    
    def parse_numeric_value(self, text: str, pattern: str = r'[\d,]+') -> Optional[float]:
        """
        テキストから数値を抽出
        
        Args:
            text: 対象テキスト
            pattern: 抽出パターン
        
        Returns:
            抽出した数値
        """
        if not text:
            return None
        
        try:
            match = re.search(pattern, text.replace(',', ''))
            if match:
                return float(match.group())
        except:
            pass
        
        return None