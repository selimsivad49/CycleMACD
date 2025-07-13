#!/usr/bin/env python3
"""
CycleMACD動作確認用のテストスクリプト
実際のyfinanceの代わりにダミーデータを使用
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ダミーデータ生成関数
def generate_dummy_stock_data(symbol, start_date, end_date, initial_price=1000):
    """ダミーの株価データを生成"""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # 月次データを生成
    dates = pd.date_range(start=start, end=end, freq='M')
    n_periods = len(dates)
    
    # ランダムウォークで価格を生成
    np.random.seed(42)  # 再現性のため
    returns = np.random.normal(0.01, 0.1, n_periods)  # 月次リターン
    
    prices = [initial_price]
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))
    
    # データフレーム作成
    data = pd.DataFrame({
        'Open': prices[:-1],
        'High': [p * (1 + np.random.uniform(0, 0.05)) for p in prices[:-1]],
        'Low': [p * (1 - np.random.uniform(0, 0.05)) for p in prices[:-1]],
        'Close': prices[1:],
        'Volume': np.random.randint(1000000, 10000000, n_periods)
    }, index=dates)
    
    return data

# 元のコードを一部修正してダミーデータを使用
class MACDBacktester:
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = None
        
    def fetch_data(self):
        """株価データを取得（ダミーデータ使用）"""
        try:
            print(f"  {self.symbol}のダミーデータを生成中...")
            self.data = generate_dummy_stock_data(self.symbol, self.start_date, self.end_date)
            
            if self.data is not None and not self.data.empty:
                print(f"  {self.symbol}: データ生成成功（{len(self.data)}件）")
                return True
            else:
                print(f"  {self.symbol}: データ生成失敗")
                return False
                
        except Exception as e:
            print(f"  データ生成エラー: {e}")
            return False
    
    def calculate_macd(self, fast=12, slow=26, signal=9):
        """MACD、シグナル、ヒストグラムを計算"""
        close = self.data['Close']
        
        # 指数移動平均の計算
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        
        # MACD計算
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        # データフレームに追加
        self.data['MACD'] = macd
        self.data['Signal'] = signal_line
        self.data['Histogram'] = histogram
        
        return self.data
    
    def generate_signals(self):
        """売買シグナルを生成"""
        # ヒストグラムが0を上回る/下回るタイミングを検出
        self.data['Position'] = 0
        self.data['Signal_Buy'] = 0
        self.data['Signal_Sell'] = 0
        
        for i in range(1, len(self.data)):
            # 前回が0以下で今回が0超の場合：買いシグナル
            if (self.data['Histogram'].iloc[i-1] <= 0 and 
                self.data['Histogram'].iloc[i] > 0):
                self.data.loc[self.data.index[i], 'Signal_Buy'] = 1
                self.data.loc[self.data.index[i], 'Position'] = 1
            
            # 前回が0超で今回が0以下の場合：売りシグナル
            elif (self.data['Histogram'].iloc[i-1] > 0 and 
                  self.data['Histogram'].iloc[i] <= 0):
                self.data.loc[self.data.index[i], 'Signal_Sell'] = 1
                self.data.loc[self.data.index[i], 'Position'] = -1
            
            # ポジション継続
            else:
                if i > 0:
                    prev_pos = self.data['Position'].iloc[i-1]
                    if prev_pos == 1 and self.data['Histogram'].iloc[i] > 0:
                        self.data.loc[self.data.index[i], 'Position'] = 1
                    elif prev_pos == -1 and self.data['Histogram'].iloc[i] <= 0:
                        self.data.loc[self.data.index[i], 'Position'] = -1
        
        return self.data
    
    def backtest(self):
        """バックテストを実行"""
        # データ取得
        if not self.fetch_data():
            return None
        
        # MACD計算
        self.calculate_macd()
        
        # シグナル生成
        self.generate_signals()
        
        # リターン計算
        self.data['Returns'] = self.data['Close'].pct_change()
        self.data['Strategy_Returns'] = self.data['Position'].shift(1) * self.data['Returns']
        
        # 累積リターン計算
        self.data['Cumulative_Returns'] = (1 + self.data['Returns']).cumprod()
        self.data['Cumulative_Strategy'] = (1 + self.data['Strategy_Returns']).cumprod()
        
        # 統計情報計算
        self.calculate_stats()
        
        return self.data
    
    def calculate_stats(self):
        """戦略の統計情報を計算"""
        strategy_returns = self.data['Strategy_Returns'].dropna()
        market_returns = self.data['Returns'].dropna()
        
        # 基本統計
        total_return_strategy = self.data['Cumulative_Strategy'].iloc[-1] - 1
        total_return_market = self.data['Cumulative_Returns'].iloc[-1] - 1
        
        # 取引回数
        trades = len(self.data[self.data['Signal_Buy'] == 1])
        
        # 勝率計算
        winning_trades = len(strategy_returns[strategy_returns > 0])
        total_trades = len(strategy_returns[strategy_returns != 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 最大ドローダウン
        cumulative = (1 + strategy_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # シャープレシオ
        sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(12) if strategy_returns.std() > 0 else 0
        
        self.results = {
            'symbol': self.symbol,
            'total_return_strategy': total_return_strategy,
            'total_return_market': total_return_market,
            'trades': trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'volatility': strategy_returns.std() * np.sqrt(12)
        }
        
        return self.results
    
    def print_summary(self):
        """結果サマリーを表示"""
        if self.results:
            print(f"\n=== {self.symbol} バックテスト結果 ===")
            print(f"戦略総リターン: {self.results['total_return_strategy']:.2%}")
            print(f"市場総リターン: {self.results['total_return_market']:.2%}")
            print(f"取引回数: {self.results['trades']}")
            print(f"勝率: {self.results['win_rate']:.2%}")
            print(f"最大ドローダウン: {self.results['max_drawdown']:.2%}")
            print(f"シャープレシオ: {self.results['sharpe_ratio']:.2f}")
            print(f"年率ボラティリティ: {self.results['volatility']:.2%}")

# テスト実行
if __name__ == "__main__":
    print("=== CycleMACD 動作確認テスト ===")
    
    # テスト期間
    start_date = "2020-01-01"
    end_date = "2024-12-31"
    
    # トヨタ自動車でテスト
    print("\nトヨタ自動車（7203）のダミーデータでテスト実行")
    backtester = MACDBacktester("7203", start_date, end_date)
    data = backtester.backtest()
    
    if data is not None:
        backtester.print_summary()
        print("\n✅ コードは正常に動作しています！")
        print("\n主要な機能:")
        print("- MACDヒストグラムによる売買シグナル生成")
        print("- バックテスト実行")
        print("- 統計情報計算（勝率、シャープレシオ、最大ドローダウンなど）")
        print("- 結果の可視化機能")
    else:
        print("❌ バックテスト実行に失敗しました")