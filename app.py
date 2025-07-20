#!/usr/bin/env python3
"""
CycleMACD Web Application
Flask-based web interface for Japanese stock MACD backtesting
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 日本語フォントの設定
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# フォントをクリアしてからjapanize_matplotlibをインポート
# import matplotlib.font_manager
# matplotlib.font_manager.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import japanize_matplotlib

# Import from modular components
from strategies import MACDBacktester, analyze_multiple_stocks
from utils import create_default_japanese_symbols
from data_manager import StockDataManager

app = Flask(__name__)

font = {"family":"IPAexGothic"}
matplotlib.rc('font', **font)

# Database manager instance
db_manager = StockDataManager()

@app.route('/')
def index():
    """パラメータ選択ページ"""
    # DBから登録済みシンボルを取得
    registered_symbols = db_manager.get_all_registered_symbols()
    
    # デフォルトの日付範囲
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')  # 5年前
    
    return render_template('parameter_selection.html', 
                         symbols=registered_symbols,
                         default_start_date=start_date,
                         default_end_date=end_date)

@app.route('/old')
def old_index():
    """旧メインページ（後方互換性のため）"""
    # Default Japanese stock symbols from utils module
    DEFAULT_SYMBOLS = create_default_japanese_symbols()
    return render_template('index.html', symbols=DEFAULT_SYMBOLS)

@app.route('/add_symbol', methods=['POST'])
def add_symbol():
    """新しいシンボルを追加"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').strip().upper()
        
        if not symbol:
            return jsonify({'error': 'シンボルが指定されていません'}), 400
        
        # 新しいシンボルを追加
        company_name = db_manager.add_symbol_with_name(symbol)
        
        if company_name is None:
            return jsonify({
                'error': f'シンボル "{symbol}" はyfinanceで見つかりませんでした。正しいシンボルを入力してください。'
            }), 400
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'company_name': company_name
        })
        
    except Exception as e:
        return jsonify({'error': f'シンボル追加中にエラーが発生しました: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """株式分析を実行"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        start_date = data.get('start_date', '2000-01-01')
        end_date = data.get('end_date', '2024-12-31')
        timeframe = data.get('timeframe', 'M')  # デフォルトは月足
        
        if not symbols:
            return jsonify({'error': '銘柄を選択してください'}), 400
        
        # 複数銘柄の分析実行
        results = []
        for symbol in symbols:
            backtester = MACDBacktester(symbol, start_date, end_date, timeframe)
            data_result = backtester.backtest()
            
            if data_result is not None:
                trade_stats = backtester.get_trade_statistics()
                results.append({
                    'symbol': symbol,
                    'data': backtester.results,
                    'trade_statistics': trade_stats,
                    'success': True
                })
            else:
                results.append({
                    'symbol': symbol,
                    'error': 'データ取得に失敗しました',
                    'success': False
                })
        
        return jsonify({
            'results': results,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': f'分析中にエラーが発生しました: {str(e)}'}), 500

@app.route('/chart/<symbol>')
def generate_chart(symbol):
    """個別銘柄のチャートを生成"""
    try:
        start_date = request.args.get('start_date', '2000-01-01')
        end_date = request.args.get('end_date', '2024-12-31')
        timeframe = request.args.get('timeframe', 'M')  # デフォルトは月足
        
        backtester = MACDBacktester(symbol, start_date, end_date, timeframe)
        data = backtester.backtest()
        
        if data is None:
            return jsonify({'error': 'データ取得に失敗しました'}), 400
        
        # チャート生成
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 1. 株価とシグナル
        ax1 = axes[0]
        ax1.plot(data.index, data['Close'], label='価格', linewidth=2)
        buy_signals = data[data['Signal_Buy'] == 1]
        sell_signals = data[data['Signal_Sell'] == 1]
        
        ax1.scatter(buy_signals.index, buy_signals['Close'], 
                   color='green', marker='^', s=100, label='買いシグナル')
        ax1.scatter(sell_signals.index, sell_signals['Close'], 
                   color='red', marker='v', s=100, label='売りシグナル')
        
        ax1.set_title(f'{symbol} - 株価と売買シグナル')
        ax1.set_ylabel('価格')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. MACDヒストグラム
        ax2 = axes[1]
        colors = ['green' if x > 0 else 'red' for x in data['Histogram']]
        ax2.bar(data.index, data['Histogram'], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_title('MACDヒストグラム')
        ax2.set_ylabel('ヒストグラム')
        ax2.grid(True, alpha=0.3)
        
        # 3. 累積リターン比較
        ax3 = axes[2]
        ax3.plot(data.index, (data['Cumulative_Strategy'] - 1) * 100, 
                label='戦略', linewidth=2)
        ax3.plot(data.index, (data['Cumulative_Returns'] - 1) * 100, 
                label='バイ&ホールド', linewidth=2, alpha=0.7)
        
        ax3.set_title('累積リターン比較')
        ax3.set_ylabel('リターン (%)')
        ax3.set_xlabel('日付')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 画像をBase64エンコード
        img = BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
         # Save plot as file for debug
        filename = f"macd_analysis.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 取引統計を取得
        trade_stats = backtester.get_trade_statistics()
        
        return jsonify({
            'chart': plot_url,
            'results': backtester.results,
            'trade_statistics': trade_stats
        })
        
    except Exception as e:
        return jsonify({'error': f'チャート生成中にエラーが発生しました: {str(e)}'}), 500

@app.route('/backtest')
def get_backtest():
    """GET方式でのバックテスト実行（保存用1画面表示）"""
    try:
        # パラメータ取得
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date', '2020-01-01')
        end_date = request.args.get('end_date', '2024-12-31')
        timeframe = request.args.get('timeframe', 'M')
        strategy = request.args.get('strategy', 'CycleMacd')
        
        # パラメータ検証
        if not symbol:
            return render_template('backtest_result.html', 
                                 error="シンボルが指定されていません。", 
                                 params={'symbol': '', 'start_date': start_date, 
                                        'end_date': end_date, 'timeframe': timeframe, 'strategy': strategy})
        
        if timeframe not in ['D', 'W', 'M']:
            return render_template('backtest_result.html', 
                                 error="無効な時間軸です。D（日足）、W（週足）、M（月足）のいずれかを指定してください。", 
                                 params={'symbol': symbol, 'start_date': start_date, 
                                        'end_date': end_date, 'timeframe': timeframe, 'strategy': strategy})
        
        if strategy.lower() not in ['cyclemacd', 'cycle_macd']:
            return render_template('backtest_result.html', 
                                 error="サポートされていない戦略です。現在はCycleMACDのみサポートしています。", 
                                 params={'symbol': symbol, 'start_date': start_date, 
                                        'end_date': end_date, 'timeframe': timeframe, 'strategy': strategy})
        
        # バックテスト実行
        backtester = MACDBacktester(symbol, start_date, end_date, timeframe)
        data = backtester.backtest()
        
        if data is None:
            return render_template('backtest_result.html', 
                                 error="データ取得またはバックテストに失敗しました。", 
                                 params={'symbol': symbol, 'start_date': start_date, 
                                        'end_date': end_date, 'timeframe': timeframe, 'strategy': strategy})
        
        # チャート生成
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        # 1. 株価とシグナル
        ax1 = axes[0]
        ax1.plot(data.index, data['Close'], label='価格', linewidth=2, color='#2E86AB')
        buy_signals = data[data['Signal_Buy'] == 1]
        sell_signals = data[data['Signal_Sell'] == 1]
        
        ax1.scatter(buy_signals.index, buy_signals['Close'], 
                   color='green', marker='^', s=100, label='買いシグナル', zorder=5)
        ax1.scatter(sell_signals.index, sell_signals['Close'], 
                   color='red', marker='v', s=100, label='売りシグナル', zorder=5)
        
        timeframe_names = {'D': '日足', 'W': '週足', 'M': '月足'}
        ax1.set_title(f'{symbol} - 株価と売買シグナル ({timeframe_names[timeframe]})', fontsize=14, fontweight='bold')
        ax1.set_ylabel('価格', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 2. MACDヒストグラム
        ax2 = axes[1]
        colors = ['#28a745' if x > 0 else '#dc3545' for x in data['Histogram']]
        ax2.bar(data.index, data['Histogram'], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_title('MACDヒストグラム', fontsize=14, fontweight='bold')
        ax2.set_ylabel('ヒストグラム', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 3. 累積リターン比較
        ax3 = axes[2]
        ax3.plot(data.index, (data['Cumulative_Strategy'] - 1) * 100, 
                label='CycleMacd戦略', linewidth=2, color='#007bff')
        ax3.plot(data.index, (data['Cumulative_Returns'] - 1) * 100, 
                label='バイ&ホールド', linewidth=2, alpha=0.7, color='#6c757d')
        
        ax3.set_title('累積リターン比較', fontsize=14, fontweight='bold')
        ax3.set_ylabel('リターン (%)', fontsize=12)
        ax3.set_xlabel('日付', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 画像をBase64エンコード
        img = BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        chart_data = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # 取引統計取得
        trade_stats = backtester.get_trade_statistics()
        
        # 結果データ準備
        results = backtester.results
        
        return render_template('backtest_result.html', 
                             results=results,
                             trade_statistics=trade_stats,
                             chart_data=chart_data,
                             params={'symbol': symbol, 'start_date': start_date, 
                                    'end_date': end_date, 'timeframe': timeframe, 'strategy': strategy})
        
    except Exception as e:
        return render_template('backtest_result.html', 
                             error=f'バックテスト実行中にエラーが発生しました: {str(e)}', 
                             params={'symbol': symbol or '', 'start_date': start_date, 
                                    'end_date': end_date, 'timeframe': timeframe, 'strategy': strategy})

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'OK', 'service': 'CycleMACD Web App'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)