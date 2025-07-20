"""
Stock Screening Module for CycleMACD

Contains screening conditions and market index definitions.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from data_manager import get_japanese_stock_data


class HalfSignal:
    """半分シグナル - SMAクロス条件に基づくスクリーニング"""
    
    def __init__(self):
        self.name = "半分シグナル"
        self.description = "5日SMA > 20日SMA > 60日SMA、5日SMA上昇、ローソク足実体の半分以上が5日SMAを上抜け"
    
    def check_condition(self, symbol, period_days=100):
        """
        スクリーニング条件をチェック
        
        Args:
            symbol: チェック対象シンボル
            period_days: データ取得期間（日数）
        
        Returns:
            dict: {
                'symbol': シンボル,
                'passed': True/False,
                'details': 詳細情報,
                'error': エラーメッセージ（エラー時のみ）
            }
        """
        try:
            # データ取得
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            
            data = get_japanese_stock_data(symbol, start_date, end_date)
            
            if data is None or len(data) < 70:  # 最低70日分のデータが必要
                return {
                    'symbol': symbol,
                    'passed': False,
                    'error': f'データが不十分です (取得件数: {len(data) if data is not None else 0}件)'
                }
            
            # SMA計算
            data['SMA5'] = data['Close'].rolling(window=5).mean()
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['SMA60'] = data['Close'].rolling(window=60).mean()
            
            # 最新のデータ（最後の2日分）
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # 条件1: 5日SMA > 20日SMA > 60日SMA
            condition1 = (latest['SMA5'] > latest['SMA20'] > latest['SMA60'])
            
            # 条件2: 最新5日SMAが前日より上昇
            condition2 = (latest['SMA5'] > prev['SMA5'])
            
            # 条件3: ローソク足実体の半分以上が5日SMAを上抜け
            # 実体の上端（高い方の価格）
            body_top = max(latest['Open'], latest['Close'])
            # 実体の下端（低い方の価格）
            body_bottom = min(latest['Open'], latest['Close'])
            
            # 5日SMAより上にある実体部分の長さ
            if body_top > latest['SMA5']:
                cross_length = body_top - max(latest['SMA5'], body_bottom)
            else:
                cross_length = 0
            
            # 実体全体の長さ
            body_length = abs(latest['Close'] - latest['Open'])
            
            # 半分以上の条件
            condition3a = body_length > 0 and cross_length >= body_length / 2
            
            # 代替条件: 実体下部を前日終値に置き換えた場合
            alt_body_bottom = prev['Close']
            alt_body_length = abs(body_top - alt_body_bottom)
            
            if body_top > latest['SMA5']:
                alt_cross_length = body_top - max(latest['SMA5'], alt_body_bottom)
            else:
                alt_cross_length = 0
            
            condition3b = alt_body_length > 0 and alt_cross_length >= alt_body_length / 2
            
            condition3 = condition3a or condition3b
            
            # 全条件の結果
            passed = condition1 and condition2 and condition3
            
            details = {
                'latest_date': latest.name.strftime('%Y-%m-%d'),
                'close_price': float(latest['Close']),
                'sma5': float(latest['SMA5']),
                'sma20': float(latest['SMA20']),
                'sma60': float(latest['SMA60']),
                'condition1_sma_order': condition1,
                'condition2_sma5_rising': condition2,
                'condition3_half_cross': condition3,
                'body_length': float(body_length),
                'cross_length': float(cross_length),
                'cross_ratio': float(cross_length / body_length) if body_length > 0 else 0,
                'alternative_used': condition3b and not condition3a
            }
            
            return {
                'symbol': symbol,
                'passed': passed,
                'details': details
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'passed': False,
                'error': f'スクリーニングエラー: {str(e)}'
            }


class ScreeningEngine:
    """スクリーニング実行エンジン"""
    
    def __init__(self):
        self.conditions = {
            'halfsignal': HalfSignal()
        }
    
    def get_available_conditions(self):
        """利用可能なスクリーニング条件を取得"""
        return {
            name: condition.name 
            for name, condition in self.conditions.items()
        }
    
    def run_screening(self, condition_name, symbol_list, max_concurrent=5):
        """
        スクリーニングを実行
        
        Args:
            condition_name: スクリーニング条件名
            symbol_list: チェック対象シンボルリスト
            max_concurrent: 同時処理数
        
        Returns:
            dict: スクリーニング結果
        """
        if condition_name not in self.conditions:
            return {
                'error': f'スクリーニング条件 "{condition_name}" が見つかりません',
                'available_conditions': list(self.conditions.keys())
            }
        
        condition = self.conditions[condition_name]
        results = []
        passed_symbols = []
        failed_symbols = []
        error_symbols = []
        
        print(f"スクリーニング開始: {condition.name}")
        print(f"対象銘柄数: {len(symbol_list)}")
        
        for i, symbol in enumerate(symbol_list, 1):
            print(f"  {i}/{len(symbol_list)}: {symbol} をチェック中...")
            
            result = condition.check_condition(symbol)
            results.append(result)
            
            if 'error' in result:
                error_symbols.append(result)
            elif result['passed']:
                passed_symbols.append(result)
            else:
                failed_symbols.append(result)
        
        return {
            'condition_name': condition_name,
            'condition_description': condition.description,
            'total_checked': len(symbol_list),
            'passed_count': len(passed_symbols),
            'failed_count': len(failed_symbols),
            'error_count': len(error_symbols),
            'passed_symbols': passed_symbols,
            'failed_symbols': failed_symbols,
            'error_symbols': error_symbols,
            'all_results': results
        }


# 市場インデックス定義
MARKET_INDICES = {
    'nikkei225': {
        'name': '日経225',
        'description': '日経平均株価採用銘柄',
        'symbols': [
            # 主要な日経225銘柄（例）
            '1301.T', '1332.T', '1333.T', '1605.T', '1721.T', '1801.T', '1802.T', '1803.T', '1808.T', '1812.T',
            '1925.T', '1928.T', '1963.T', '2002.T', '2269.T', '2282.T', '2413.T', '2432.T', '2501.T', '2502.T',
            '2503.T', '2531.T', '2768.T', '2801.T', '2802.T', '2871.T', '2914.T', '3086.T', '3099.T', '3101.T',
            '3103.T', '3105.T', '3382.T', '3401.T', '3402.T', '3405.T', '3407.T', '3436.T', '3861.T', '3863.T',
            '4004.T', '4005.T', '4021.T', '4042.T', '4043.T', '4061.T', '4063.T', '4088.T', '4151.T', '4183.T',
            '4188.T', '4204.T', '4208.T', '4272.T', '4307.T', '4324.T', '4452.T', '4502.T', '4503.T', '4506.T',
            '4507.T', '4519.T', '4523.T', '4568.T', '4578.T', '4612.T', '4631.T', '4661.T', '4681.T', '4684.T',
            '4689.T', '4704.T', '4716.T', '4755.T', '4901.T', '4911.T', '4919.T', '4967.T', '4968.T', '5001.T',
            '5002.T', '5020.T', '5101.T', '5108.T', '5201.T', '5202.T', '5214.T', '5232.T', '5233.T', '5301.T',
            '5401.T', '5406.T', '5411.T', '5541.T', '5631.T', '5703.T', '5706.T', '5707.T', '5711.T', '5713.T',
            '5714.T', '5802.T', '5803.T', '5805.T', '5901.T', '5947.T', '5988.T', '6098.T', '6103.T', '6113.T',
            '6178.T', '6301.T', '6302.T', '6305.T', '6326.T', '6361.T', '6367.T', '6473.T', '6479.T', '6501.T',
            '6502.T', '6503.T', '6504.T', '6506.T', '6594.T', '6701.T', '6702.T', '6703.T', '6723.T', '6724.T',
            '6728.T', '6752.T', '6758.T', '6762.T', '6770.T', '6806.T', '6841.T', '6856.T', '6857.T', '6861.T',
            '6869.T', '6902.T', '6920.T', '6923.T', '6952.T', '6954.T', '6971.T', '6976.T', '6981.T', '7003.T',
            '7004.T', '7011.T', '7012.T', '7013.T', '7201.T', '7202.T', '7203.T', '7211.T', '7261.T', '7267.T',
            '7269.T', '7270.T', '7272.T', '7731.T', '7733.T', '7735.T', '7751.T', '7832.T', '7911.T', '7912.T',
            '7951.T', '7974.T', '8001.T', '8002.T', '8015.T', '8020.T', '8028.T', '8031.T', '8035.T', '8053.T',
            '8058.T', '8076.T', '8233.T', '8252.T', '8253.T', '8267.T', '8303.T', '8304.T', '8306.T', '8308.T',
            '8309.T', '8316.T', '8331.T', '8354.T', '8411.T', '8473.T', '8585.T', '8593.T', '8601.T', '8604.T',
            '8628.T', '8630.T', '8697.T', '8725.T', '8750.T', '8766.T', '8795.T', '8801.T', '8802.T', '8830.T',
            '9001.T', '9005.T', '9007.T', '9008.T', '9009.T', '9020.T', '9021.T', '9022.T', '9031.T', '9041.T',
            '9042.T', '9062.T', '9064.T', '9086.T', '9101.T', '9104.T', '9107.T', '9201.T', '9202.T', '9301.T',
            '9432.T', '9433.T', '9434.T', '9435.T', '9437.T', '9501.T', '9502.T', '9503.T', '9531.T', '9532.T',
            '9613.T', '9678.T', '9684.T', '9735.T', '9766.T', '9983.T', '9984.T'
        ]
    },
    'jpx400': {
        'name': 'JPX400',
        'description': 'JPX日経インデックス400採用銘柄',
        'symbols': [
            # JPX400の主要銘柄（日経225 + 追加銘柄の例）
            '1301.T', '1332.T', '1333.T', '1605.T', '1721.T', '1801.T', '1802.T', '1803.T', '1808.T', '1812.T',
            '1925.T', '1928.T', '1963.T', '2002.T', '2269.T', '2282.T', '2413.T', '2432.T', '2501.T', '2502.T',
            '2503.T', '2531.T', '2768.T', '2801.T', '2802.T', '2871.T', '2914.T', '3086.T', '3099.T', '3101.T',
            '3103.T', '3105.T', '3382.T', '3401.T', '3402.T', '3405.T', '3407.T', '3436.T', '3861.T', '3863.T',
            '4004.T', '4005.T', '4021.T', '4042.T', '4043.T', '4061.T', '4063.T', '4088.T', '4151.T', '4183.T',
            '4188.T', '4204.T', '4208.T', '4272.T', '4307.T', '4324.T', '4452.T', '4502.T', '4503.T', '4506.T',
            '4507.T', '4519.T', '4523.T', '4568.T', '4578.T', '4612.T', '4631.T', '4661.T', '4681.T', '4684.T',
            '4689.T', '4704.T', '4716.T', '4755.T', '4901.T', '4911.T', '4919.T', '4967.T', '4968.T', '5001.T',
            '5002.T', '5020.T', '5101.T', '5108.T', '5201.T', '5202.T', '5214.T', '5232.T', '5233.T', '5301.T',
            '5401.T', '5406.T', '5411.T', '5541.T', '5631.T', '5703.T', '5706.T', '5707.T', '5711.T', '5713.T',
            '5714.T', '5802.T', '5803.T', '5805.T', '5901.T', '5947.T', '5988.T', '6098.T', '6103.T', '6113.T',
            '6178.T', '6301.T', '6302.T', '6305.T', '6326.T', '6361.T', '6367.T', '6473.T', '6479.T', '6501.T',
            '6502.T', '6503.T', '6504.T', '6506.T', '6594.T', '6701.T', '6702.T', '6703.T', '6723.T', '6724.T',
            '6728.T', '6752.T', '6758.T', '6762.T', '6770.T', '6806.T', '6841.T', '6856.T', '6857.T', '6861.T',
            '6869.T', '6902.T', '6920.T', '6923.T', '6952.T', '6954.T', '6971.T', '6976.T', '6981.T', '7003.T',
            '7004.T', '7011.T', '7012.T', '7013.T', '7201.T', '7202.T', '7203.T', '7211.T', '7261.T', '7267.T',
            '7269.T', '7270.T', '7272.T', '7731.T', '7733.T', '7735.T', '7751.T', '7832.T', '7911.T', '7912.T',
            '7951.T', '7974.T', '8001.T', '8002.T', '8015.T', '8020.T', '8028.T', '8031.T', '8035.T', '8053.T',
            '8058.T', '8076.T', '8233.T', '8252.T', '8253.T', '8267.T', '8303.T', '8304.T', '8306.T', '8308.T',
            '8309.T', '8316.T', '8331.T', '8354.T', '8411.T', '8473.T', '8585.T', '8593.T', '8601.T', '8604.T',
            '8628.T', '8630.T', '8697.T', '8725.T', '8750.T', '8766.T', '8795.T', '8801.T', '8802.T', '8830.T',
            '9001.T', '9005.T', '9007.T', '9008.T', '9009.T', '9020.T', '9021.T', '9022.T', '9031.T', '9041.T',
            '9042.T', '9062.T', '9064.T', '9086.T', '9101.T', '9104.T', '9107.T', '9201.T', '9202.T', '9301.T',
            '9432.T', '9433.T', '9434.T', '9435.T', '9437.T', '9501.T', '9502.T', '9503.T', '9531.T', '9532.T',
            '9613.T', '9678.T', '9684.T', '9735.T', '9766.T', '9983.T', '9984.T',
            # JPX400追加銘柄（例）
            '1379.T', '1414.T', '1419.T', '1570.T', '1662.T', '1878.T', '2432.T', '2433.T', '2811.T', '3038.T',
            '3659.T', '3765.T', '4324.T', '4385.T', '4543.T', '4751.T', '4768.T', '6055.T', '6067.T', '6088.T',
            '6121.T', '6141.T', '6142.T', '6194.T', '6199.T', '6273.T', '6287.T', '6370.T', '6448.T', '6460.T',
            '6481.T', '6504.T', '6645.T', '6674.T', '6753.T', '6965.T', '7004.T', '7014.T', '7021.T', '7148.T',
            '7832.T', '8086.T', '8218.T', '8411.T', '8439.T', '8570.T', '8804.T', '9020.T', '9021.T', '9058.T'
        ]
    }
}


def get_market_symbols(market_name):
    """市場インデックスのシンボルリストを取得"""
    if market_name in MARKET_INDICES:
        return MARKET_INDICES[market_name]['symbols']
    return []


def get_available_markets():
    """利用可能な市場インデックスを取得"""
    return {
        name: info['name'] 
        for name, info in MARKET_INDICES.items()
    }