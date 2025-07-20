"""
Utility Functions Module for CycleMACD

Contains common utility functions and helper methods.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environment
import matplotlib.pyplot as plt
import japanize_matplotlib
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# フォントをクリアしてからjapanize_matplotlibをインポート
import matplotlib.font_manager
matplotlib.font_manager.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import japanize_matplotlib

font = {"family": "IPAexGothic"}
matplotlib.rc('font', **font)


def validate_date_range(start_date, end_date):
    """日付範囲の検証"""
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt >= end_dt:
            return False, "開始日は終了日より前である必要があります"
        
        if end_dt > datetime.now():
            return False, "終了日は現在日より後にはできません"
        
        return True, "OK"
    except ValueError:
        return False, "日付形式が正しくありません (YYYY-MM-DD)"


def validate_timeframe(timeframe):
    """時間軸の検証"""
    valid_timeframes = ['D', 'W', 'M']
    if timeframe not in valid_timeframes:
        return False, f"無効な時間軸です。{valid_timeframes}のいずれかを指定してください"
    return True, "OK"


def validate_symbol(symbol):
    """シンボルの検証"""
    if not symbol or not isinstance(symbol, str):
        return False, "シンボルが指定されていません"
    
    # 基本的な文字チェック
    if len(symbol.strip()) == 0:
        return False, "シンボルが空です"
    
    return True, "OK"


def calculate_annualized_return(cumulative_return, periods, timeframe='M'):
    """年率リターンを計算"""
    periods_per_year = 252 if timeframe == 'D' else (52 if timeframe == 'W' else 12)
    years = periods / periods_per_year
    
    if years <= 0:
        return 0
    
    annualized = (1 + cumulative_return) ** (1/years) - 1
    return annualized


def calculate_max_drawdown(returns):
    """最大ドローダウンを計算"""
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    return drawdown.min()


def calculate_sharpe_ratio(returns, risk_free_rate=0.0, timeframe='M'):
    """シャープレシオを計算"""
    periods_per_year = 252 if timeframe == 'D' else (52 if timeframe == 'W' else 12)
    
    if returns.std() == 0:
        return 0
    
    excess_returns = returns.mean() - risk_free_rate / periods_per_year
    sharpe = excess_returns / returns.std() * np.sqrt(periods_per_year)
    return sharpe


def calculate_volatility(returns, timeframe='M'):
    """年率ボラティリティを計算"""
    periods_per_year = 252 if timeframe == 'D' else (52 if timeframe == 'W' else 12)
    return returns.std() * np.sqrt(periods_per_year)


def format_percentage(value, decimal_places=2):
    """パーセンテージフォーマット"""
    return f"{value * 100:.{decimal_places}f}%"


def format_currency(value, currency_symbol="¥", decimal_places=2):
    """通貨フォーマット"""
    return f"{currency_symbol}{value:,.{decimal_places}f}"


def get_timeframe_name(timeframe):
    """時間軸の日本語名を取得"""
    timeframe_names = {
        'D': '日足',
        'W': '週足', 
        'M': '月足'
    }
    return timeframe_names.get(timeframe, timeframe)


def get_timeframe_multiplier(timeframe):
    """時間軸のMACDパラメータ乗数を取得"""
    multipliers = {
        'D': 20,  # 日足は月足の20倍
        'W': 4,   # 週足は月足の4倍
        'M': 1    # 月足は基準
    }
    return multipliers.get(timeframe, 1)


def sanitize_filename(filename):
    """ファイル名をサニタイズ"""
    import re
    # 危険な文字を除去
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 連続するアンダースコアを1つにまとめる
    sanitized = re.sub(r'_+', '_', sanitized)
    # 先頭・末尾のアンダースコアを除去
    sanitized = sanitized.strip('_')
    return sanitized


def get_trading_days_per_year(timeframe):
    """時間軸ごとの年間取引日数を取得"""
    trading_days = {
        'D': 252,  # 年間約252営業日
        'W': 52,   # 年間52週
        'M': 12    # 年間12ヶ月
    }
    return trading_days.get(timeframe, 252)


def create_default_japanese_symbols():
    """デフォルトの日本株シンボルリストを作成"""
    return [
        {"code": "7203.T", "name": "トヨタ自動車"},
        {"code": "6758.T", "name": "ソニーグループ"},
        {"code": "9984.T", "name": "ソフトバンクグループ"},
        {"code": "6861.T", "name": "キーエンス"},
        {"code": "4519.T", "name": "中外製薬"},
        {"code": "8306.T", "name": "三菱UFJフィナンシャル・グループ"},
        {"code": "6098.T", "name": "リクルートホールディングス"},
        {"code": "4063.T", "name": "信越化学工業"},
        {"code": "9983.T", "name": "ファーストリテイリング"},
        {"code": "7974.T", "name": "任天堂"},
        {"code": "NIY=F", "name": "日経平均先物"},
    ]


def setup_matplotlib_japanese():
    """matplotlib日本語設定"""
    # 既に設定済みのため、この関数は互換性のためのプレースホルダー
    pass


def print_backtest_summary(results, symbol):
    """バックテスト結果サマリーを表示"""
    if not results:
        print(f"{symbol}: 結果データがありません")
        return
    
    print(f"\n=== {symbol} バックテスト結果 ===")
    print(f"戦略総リターン: {format_percentage(results.get('total_return_strategy', 0))}")
    print(f"市場総リターン: {format_percentage(results.get('total_return_market', 0))}")
    print(f"取引回数: {results.get('trades', 0)}")
    print(f"勝率: {format_percentage(results.get('win_rate', 0))}")
    print(f"最大ドローダウン: {format_percentage(results.get('max_drawdown', 0))}")
    print(f"シャープレシオ: {results.get('sharpe_ratio', 0):.2f}")
    print(f"年率ボラティリティ: {format_percentage(results.get('volatility', 0))}")


def calculate_trade_statistics_summary(trades_list):
    """取引リストから統計サマリーを計算"""
    if not trades_list:
        return {}
    
    df_trades = pd.DataFrame(trades_list)
    
    profitable_trades = df_trades[df_trades['pnl'] > 0]
    losing_trades = df_trades[df_trades['pnl'] < 0]
    
    win_rate = len(profitable_trades) / len(df_trades) * 100 if len(df_trades) > 0 else 0
    avg_profit = profitable_trades['pnl'].mean() if len(profitable_trades) > 0 else 0
    avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
    pl_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
    
    return {
        'total_trades': len(df_trades),
        'winning_trades': len(profitable_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'avg_profit': avg_profit,
        'avg_loss': avg_loss,
        'pl_ratio': pl_ratio,
        'total_pnl': df_trades['pnl'].sum(),
        'max_profit': df_trades['pnl'].max(),
        'max_loss': df_trades['pnl'].min()
    }


def create_performance_summary_dict(strategy_returns, market_returns, trades, timeframe='M'):
    """パフォーマンスサマリー辞書を作成"""
    total_return_strategy = (1 + strategy_returns).cumprod().iloc[-1] - 1 if len(strategy_returns) > 0 else 0
    total_return_market = (1 + market_returns).cumprod().iloc[-1] - 1 if len(market_returns) > 0 else 0
    
    # 勝率計算
    winning_trades = len(strategy_returns[strategy_returns > 0])
    total_trades = len(strategy_returns[strategy_returns != 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # 最大ドローダウン
    max_drawdown = calculate_max_drawdown(strategy_returns)
    
    # シャープレシオ
    sharpe_ratio = calculate_sharpe_ratio(strategy_returns, timeframe=timeframe)
    
    # ボラティリティ
    volatility = calculate_volatility(strategy_returns, timeframe=timeframe)
    
    return {
        'total_return_strategy': total_return_strategy,
        'total_return_market': total_return_market,
        'trades': trades,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'volatility': volatility
    }


def get_default_judgment_date():
    """
    日本時間に基づいてスクリーニングの判定日を取得
    
    Rules:
    - 日本時間0-9時: 前日
    - 土曜日: 前金曜日
    - 日曜日: 前金曜日
    - 月曜日～金曜日 10時以降: 当日
    """
    from datetime import datetime, timedelta
    
    # UTCから日本時間を計算 (UTC+9)
    now_utc = datetime.utcnow()
    now_jst = now_utc + timedelta(hours=9)
    
    # 時間チェック (0-9時の場合は前日)
    if now_jst.hour < 10:
        target_date = now_jst.date() - timedelta(days=1)
    else:
        target_date = now_jst.date()
    
    # 曜日チェック (土日の場合は前の金曜日)
    weekday = target_date.weekday()  # 0=月曜日, 6=日曜日
    
    if weekday == 5:  # 土曜日
        target_date = target_date - timedelta(days=1)  # 金曜日
    elif weekday == 6:  # 日曜日
        target_date = target_date - timedelta(days=2)  # 金曜日
    
    return target_date.strftime('%Y-%m-%d')


def get_trading_day_before(date_str, days=1):
    """指定した日付から指定日数前の取引日を取得"""
    from datetime import datetime, timedelta
    
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    for _ in range(days):
        date = date - timedelta(days=1)
        # 土日を避ける
        while date.weekday() >= 5:  # 土曜日(5)、日曜日(6)
            date = date - timedelta(days=1)
    
    return date.strftime('%Y-%m-%d')


def validate_judgment_date(date_str):
    """判定日の妥当性をチェック"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if date > today:
            return False, "判定日は今日以前の日付を指定してください"
        
        # あまりに古い日付もチェック
        min_date = datetime(1990, 1, 1).date()
        if date < min_date:
            return False, "判定日は1990年1月1日以降を指定してください"
        
        return True, "OK"
    except ValueError:
        return False, "日付形式が正しくありません (YYYY-MM-DD)"