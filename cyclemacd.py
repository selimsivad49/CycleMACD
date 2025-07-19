#!/usr/bin/env python3
"""
CycleMACD - Japanese Stock MACD Backtesting System

Main module for command-line usage and imports.
Web application functionality is in app.py.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environment
import matplotlib.pyplot as plt
import japanize_matplotlib
from datetime import datetime, timedelta
import warnings
import sqlite3
import os
warnings.filterwarnings('ignore')

# Import from modular components
from data_manager import StockDataManager, get_japanese_stock_data, db_manager
from strategies import MACDBacktester, analyze_multiple_stocks
from utils import (
    setup_matplotlib_japanese, 
    create_default_japanese_symbols,
    get_timeframe_name
)

# 日本語フォント設定
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# フォントをクリアしてからjapanize_matplotlibをインポート
import matplotlib.font_manager
matplotlib.font_manager.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import japanize_matplotlib

font = {"family": "IPAexGothic"}
matplotlib.rc('font', **font)


# 使用例とメイン実行部分
if __name__ == "__main__":
    # 分析期間設定
    start_date = "2000-01-01"
    end_date = "2024-12-31"
    
    # 分析対象銘柄（例：日本の代表的な銘柄）
    symbols = [
        "7203.T",   # トヨタ自動車
        "6758.T",   # ソニーグループ
        "9984.T",   # ソフトバンクグループ
        "6861.T",   # キーエンス
        "4519.T",   # 中外製薬
        "8306.T",   # 三菱UFJフィナンシャル・グループ
        "6098.T",   # リクルートホールディングス
        "4063.T",   # 信越化学工業
        "9983.T",   # ファーストリテイリング
        "7974.T",   # 任天堂
        "NIY=F",    # 日経平均先物
        "ES=F",     # S&P500 mini先物
    ]
    
    # 複数銘柄の分析実行
    # results_df = analyze_multiple_stocks(symbols, start_date, end_date)
    
    # 個別銘柄の詳細分析例
    print("\n=== 個別分析例（月足） ===")
    backtester = MACDBacktester("ES=F", start_date, end_date, timeframe='M')
    data = backtester.backtest()
    
    if data is not None:
        backtester.plot_results()
        backtester.print_trade_history()