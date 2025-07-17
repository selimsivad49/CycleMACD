import yfinance as yf
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

font = {"family":"IPAexGothic"}
matplotlib.rc('font', **font)

# 代替データソース用の関数
def get_japanese_stock_data(symbol, start_date, end_date):
    """日本株データを取得する代替関数"""
    try:
        # まずyfinanceを試す
        ticker_formats = [f"{symbol}.T", f"{symbol}.TO"]
        
        for ticker_format in ticker_formats:
            try:
                stock = yf.Ticker(ticker_format)
                data = stock.history(start=start_date, end=end_date, interval='1mo')
                
                if not data.empty and len(data) > 26:
                    print(f"  {ticker_format}で成功！")
                    return data
                    
            except Exception as e:
                continue
        
        # yfinanceで失敗した場合の代替手段
        print(f"  {symbol}: yfinanceで取得できませんでした")
        return None
        
    except Exception as e:
        print(f"  データ取得エラー: {e}")
        return None

class MACDBacktester:
    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = None
        self.trades = []  # 取引履歴を保存するリスト
        
    def fetch_data(self):
        """株価データを取得"""
        try:
            print(f"  {self.symbol}のデータを取得中...")
            self.data = get_japanese_stock_data(self.symbol, self.start_date, self.end_date)
            
            if self.data is not None and not self.data.empty:
                print(f"  {self.symbol}: データ取得成功（{len(self.data)}件）")
                return True
            else:
                print(f"  {self.symbol}: データ取得失敗")
                return False
                
        except Exception as e:
            print(f"  データ取得エラー: {e}")
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
        
        current_position = 0
        entry_date = None
        entry_price = None
        
        for i in range(2, len(self.data)):
            current_date = self.data.index[i]
            current_price = self.data['Close'].iloc[i]
            
            # 2か月前が0以下で前月が0超の場合：買いシグナル
            if (self.data['Histogram'].iloc[i-2] <= 0 and 
                self.data['Histogram'].iloc[i-1] > 0):
                
                # 前のポジションをクローズ
                if current_position == -1:
                    # ショートポジションを決済
                    pnl = entry_price - current_price
                    self.trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'direction': 'SHORT',
                        'pnl': pnl,
                        'return_pct': pnl / entry_price * 100
                    })
                
                # 新しいロングポジションを開く
                self.data.loc[self.data.index[i], 'Signal_Buy'] = 1
                self.data.loc[self.data.index[i], 'Position'] = 1
                current_position = 1
                entry_date = current_date
                entry_price = current_price
            
            # 2か月前が0超で前月が0以下の場合：売りシグナル
            elif (self.data['Histogram'].iloc[i-2] > 0 and 
                  self.data['Histogram'].iloc[i-1] <= 0):
                
                # 前のポジションをクローズ
                if current_position == 1:
                    # ロングポジションを決済
                    pnl = current_price - entry_price
                    self.trades.append({
                        'entry_date': entry_date,
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'direction': 'LONG',
                        'pnl': pnl,
                        'return_pct': pnl / entry_price * 100
                    })
                
                # 新しいショートポジションを開く
                self.data.loc[self.data.index[i], 'Signal_Sell'] = 1
                self.data.loc[self.data.index[i], 'Position'] = -1
                current_position = -1
                entry_date = current_date
                entry_price = current_price
            
            # ポジション継続
            else:
                if i > 0:
                    prev_pos = self.data['Position'].iloc[i-1]
                    if prev_pos == 1 and self.data['Histogram'].iloc[i-1] > 0:
                        self.data.loc[self.data.index[i], 'Position'] = 1
                    elif prev_pos == -1 and self.data['Histogram'].iloc[i-1] <= 0:
                        self.data.loc[self.data.index[i], 'Position'] = -1
        
        # 最後のポジションが残っている場合、最終日で決済
        if current_position != 0:
            final_date = self.data.index[-1]
            final_price = self.data['Close'].iloc[-1]
            
            if current_position == 1:
                pnl = final_price - entry_price
                direction = 'LONG'
            else:
                pnl = entry_price - final_price
                direction = 'SHORT'
            
            self.trades.append({
                'entry_date': entry_date,
                'exit_date': final_date,
                'entry_price': entry_price,
                'exit_price': final_price,
                'direction': direction,
                'pnl': pnl,
                'return_pct': pnl / entry_price * 100
            })
        
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
    
    def get_trade_history(self):
        """取引履歴を取得"""
        if not self.trades:
            return pd.DataFrame()
        
        df_trades = pd.DataFrame(self.trades)
        df_trades['holding_days'] = (df_trades['exit_date'] - df_trades['entry_date']).dt.days
        
        return df_trades
    
    def get_trade_statistics(self):
        """取引統計をJSONフォーマットで取得"""
        if not self.trades:
            return {}
        
        df_trades = self.get_trade_history()
        
        # 全体統計
        profitable_trades = df_trades[df_trades['pnl'] > 0]
        losing_trades = df_trades[df_trades['pnl'] < 0]
        win_rate = len(profitable_trades) / len(df_trades) * 100
        avg_profit = profitable_trades['pnl'].mean() if len(profitable_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        pl_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
        
        overall_stats = {
            'total_trades': len(df_trades),
            'win_rate': win_rate,
            'winning_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'pl_ratio': pl_ratio,
            'max_profit': df_trades['pnl'].max(),
            'max_loss': df_trades['pnl'].min(),
            'avg_holding_days': df_trades['holding_days'].mean(),
            'total_pnl': df_trades['pnl'].sum()
        }
        
        # Long/Short別統計
        long_trades = df_trades[df_trades['direction'] == 'LONG']
        short_trades = df_trades[df_trades['direction'] == 'SHORT']
        
        direction_stats = {}
        
        for direction, trades_df in [('LONG', long_trades), ('SHORT', short_trades)]:
            if len(trades_df) > 0:
                profitable = trades_df[trades_df['pnl'] > 0]
                losing = trades_df[trades_df['pnl'] < 0]
                win_rate_dir = len(profitable) / len(trades_df) * 100
                avg_profit_dir = profitable['pnl'].mean() if len(profitable) > 0 else 0
                avg_loss_dir = losing['pnl'].mean() if len(losing) > 0 else 0
                pl_ratio_dir = abs(avg_profit_dir / avg_loss_dir) if avg_loss_dir != 0 else 0
                total_profit_dir = trades_df['pnl'].sum()
                
                # 方向別最大ドローダウン計算
                trades_sorted = trades_df.sort_values('exit_date')
                cumulative_pnl = trades_sorted['pnl'].cumsum()
                running_max = cumulative_pnl.expanding().max()
                drawdown = cumulative_pnl - running_max
                max_dd_dir = drawdown.min()
                
                direction_stats[direction] = {
                    'trade_count': len(trades_df),
                    'win_rate': win_rate_dir,
                    'winning_trades': len(profitable),
                    'losing_trades': len(losing),
                    'total_profit': total_profit_dir,
                    'avg_profit': avg_profit_dir,
                    'avg_loss': avg_loss_dir,
                    'pl_ratio': pl_ratio_dir,
                    'max_drawdown': max_dd_dir,
                    'max_profit': trades_df['pnl'].max(),
                    'max_loss': trades_df['pnl'].min(),
                    'avg_holding_days': trades_df['holding_days'].mean()
                }
            else:
                direction_stats[direction] = {
                    'trade_count': 0,
                    'win_rate': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_profit': 0,
                    'avg_profit': 0,
                    'avg_loss': 0,
                    'pl_ratio': 0,
                    'max_drawdown': 0,
                    'max_profit': 0,
                    'max_loss': 0,
                    'avg_holding_days': 0
                }
        
        return {
            'overall': overall_stats,
            'by_direction': direction_stats
        }
    
    def print_trade_history(self):
        """取引履歴を表示"""
        if not self.trades:
            print("取引履歴がありません")
            return
        
        df_trades = self.get_trade_history()
        
        print(f"\n=== {self.symbol} 取引履歴 ===")
        print(f"総取引数: {len(df_trades)}")
        
        for i, trade in df_trades.iterrows():
            print(f"\n取引 {i+1}:")
            print(f"  方向: {trade['direction']}")
            print(f"  エントリー: {trade['entry_date'].strftime('%Y-%m-%d')} @ {trade['entry_price']:.2f}")
            print(f"  イグジット: {trade['exit_date'].strftime('%Y-%m-%d')} @ {trade['exit_price']:.2f}")
            print(f"  保有日数: {trade['holding_days']}日")
            print(f"  損益: {trade['pnl']:.2f} ({trade['return_pct']:.2f}%)")
        
        # 統計情報
        profitable_trades = df_trades[df_trades['pnl'] > 0]
        losing_trades = df_trades[df_trades['pnl'] < 0]
        win_rate = len(profitable_trades) / len(df_trades) * 100
        avg_profit = profitable_trades['pnl'].mean() if len(profitable_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        pl_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
        
        print(f"\n=== 取引統計（全体） ===")
        print(f"勝率: {win_rate:.1f}% ({len(profitable_trades)}/{len(df_trades)})")
        print(f"平均利益: {avg_profit:.2f}")
        print(f"平均損失: {avg_loss:.2f}")
        print(f"P/L比: {pl_ratio:.2f}")
        print(f"平均保有日数: {df_trades['holding_days'].mean():.1f}日")
        print(f"最大利益: {df_trades['pnl'].max():.2f}")
        print(f"最大損失: {df_trades['pnl'].min():.2f}")
        
        # Long/Short別統計
        long_trades = df_trades[df_trades['direction'] == 'LONG']
        short_trades = df_trades[df_trades['direction'] == 'SHORT']
        
        for direction, trades_df in [('LONG', long_trades), ('SHORT', short_trades)]:
            if len(trades_df) > 0:
                profitable = trades_df[trades_df['pnl'] > 0]
                losing = trades_df[trades_df['pnl'] < 0]
                win_rate_dir = len(profitable) / len(trades_df) * 100
                avg_profit_dir = profitable['pnl'].mean() if len(profitable) > 0 else 0
                avg_loss_dir = losing['pnl'].mean() if len(losing) > 0 else 0
                pl_ratio_dir = abs(avg_profit_dir / avg_loss_dir) if avg_loss_dir != 0 else 0
                total_profit_dir = trades_df['pnl'].sum()
                
                # 方向別最大ドローダウン計算
                trades_sorted = trades_df.sort_values('exit_date')
                cumulative_pnl = trades_sorted['pnl'].cumsum()
                running_max = cumulative_pnl.expanding().max()
                drawdown = cumulative_pnl - running_max
                max_dd_dir = drawdown.min()
                
                print(f"\n=== {direction}取引統計 ===")
                print(f"取引数: {len(trades_df)}")
                print(f"勝率: {win_rate_dir:.1f}% ({len(profitable)}/{len(trades_df)})")
                print(f"総利益: {total_profit_dir:.2f}")
                print(f"平均利益: {avg_profit_dir:.2f}")
                print(f"平均損失: {avg_loss_dir:.2f}")
                print(f"P/L比: {pl_ratio_dir:.2f}")
                print(f"最大ドローダウン: {max_dd_dir:.2f}")
                print(f"最大利益: {trades_df['pnl'].max():.2f}")
                print(f"最大損失: {trades_df['pnl'].min():.2f}")
                print(f"平均保有日数: {trades_df['holding_days'].mean():.1f}日")
    
    def plot_results(self, save_file=True):
        """結果をプロット"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 1. 株価とシグナル
        ax1 = axes[0]
        ax1.plot(self.data.index, self.data['Close'], label='価格', linewidth=2, color='#2E86AB')
        buy_signals = self.data[self.data['Signal_Buy'] == 1]
        sell_signals = self.data[self.data['Signal_Sell'] == 1]
        
        ax1.scatter(buy_signals.index, buy_signals['Close'], 
                   color='green', marker='^', s=100, label='買いシグナル', zorder=5)
        ax1.scatter(sell_signals.index, sell_signals['Close'], 
                   color='red', marker='v', s=100, label='売りシグナル', zorder=5)
        
        ax1.set_title(f'{self.symbol} - 株価と売買シグナル', fontsize=14, fontweight='bold')
        ax1.set_ylabel('価格', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 2. MACDヒストグラム
        ax2 = axes[1]
        colors = ['#28a745' if x > 0 else '#dc3545' for x in self.data['Histogram']]
        ax2.bar(self.data.index, self.data['Histogram'], color=colors, alpha=0.7, width=20)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_title('MACDヒストグラム', fontsize=14, fontweight='bold')
        ax2.set_ylabel('ヒストグラム', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 3. 累積リターン比較
        ax3 = axes[2]
        ax3.plot(self.data.index, (self.data['Cumulative_Strategy'] - 1) * 100, 
                label='MACD戦略', linewidth=2, color='#007bff')
        ax3.plot(self.data.index, (self.data['Cumulative_Returns'] - 1) * 100, 
                label='バイ&ホールド', linewidth=2, alpha=0.7, color='#6c757d')
        
        ax3.set_title('累積リターン比較', fontsize=14, fontweight='bold')
        ax3.set_ylabel('リターン (%)', fontsize=12)
        ax3.set_xlabel('日付', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_file:
            # Save plot as file
            filename = f"{self.symbol}_macd_analysis.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Chart saved as {filename}")
            plt.close()
            return filename
        else:
            # Return the figure for web app use
            return fig
    
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


def analyze_multiple_stocks(symbols, start_date, end_date):
    """複数銘柄の分析"""
    results = []
    
    for symbol in symbols:
        print(f"\n{symbol}を分析中...")
        backtester = MACDBacktester(symbol, start_date, end_date)
        data = backtester.backtest()
        
        if data is not None:
            results.append(backtester.results)
            backtester.print_summary()
        else:
            print(f"{symbol}のデータ取得に失敗しました")
    
    # 結果をDataFrameにまとめる
    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('total_return_strategy', ascending=False)
        
        print("\n=== 全銘柄結果サマリー ===")
        print(df_results.to_string(index=False))
        
        return df_results
    
    return None


# 使用例
if __name__ == "__main__":
    # 分析期間設定
    start_date = "2000-01-01"
    end_date = "2024-12-31"
    
    # 分析対象銘柄（例：日本の代表的な銘柄）
    symbols = [
        "7203",  # トヨタ自動車
        "6758",  # ソニーグループ
        "9984",  # ソフトバンクグループ
        "6861",  # キーエンス
        "4519",  # 中外製薬
        "8306",  # 三菱UFJフィナンシャル・グループ
        "6098",  # リクルートホールディングス
        "4063",  # 信越化学工業
        "9983",  # ファーストリテイリング
        "7974"  # 任天堂
    ]
    
    # 複数銘柄の分析実行
    # results_df = analyze_multiple_stocks(symbols, start_date, end_date)
    
    # 個別銘柄の詳細分析例
    print("\n=== 個別分析例 ===")
    backtester = MACDBacktester("4519", start_date, end_date)
    data = backtester.backtest()
    
    if data is not None:
        backtester.plot_results()
        backtester.print_trade_history()
