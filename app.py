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
import matplotlib.font_manager
matplotlib.font_manager.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import japanize_matplotlib

# Import our MACD backtester
from cyclemacd import MACDBacktester, analyze_multiple_stocks

app = Flask(__name__)

# Default Japanese stock symbols
DEFAULT_SYMBOLS = [
    {"code": "7203", "name": "トヨタ自動車"},
    {"code": "6758", "name": "ソニーグループ"},
    {"code": "9984", "name": "ソフトバンクグループ"},
    {"code": "6861", "name": "キーエンス"},
    {"code": "4519", "name": "中外製薬"},
    {"code": "8306", "name": "三菱UFJフィナンシャル・グループ"},
    {"code": "6098", "name": "リクルートホールディングス"},
    {"code": "4063", "name": "信越化学工業"},
    {"code": "9983", "name": "ファーストリテイリング"},
    {"code": "7974", "name": "任天堂"}
]

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html', symbols=DEFAULT_SYMBOLS)

@app.route('/analyze', methods=['POST'])
def analyze():
    """株式分析を実行"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        start_date = data.get('start_date', '2020-01-01')
        end_date = data.get('end_date', '2024-12-31')
        
        if not symbols:
            return jsonify({'error': '銘柄を選択してください'}), 400
        
        # 複数銘柄の分析実行
        results = []
        for symbol in symbols:
            backtester = MACDBacktester(symbol, start_date, end_date)
            data_result = backtester.backtest()
            
            if data_result is not None:
                results.append({
                    'symbol': symbol,
                    'data': backtester.results,
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
        start_date = request.args.get('start_date', '2020-01-01')
        end_date = request.args.get('end_date', '2024-12-31')
        
        backtester = MACDBacktester(symbol, start_date, end_date)
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
        plt.close()
        
        return jsonify({
            'chart': plot_url,
            'results': backtester.results
        })
        
    except Exception as e:
        return jsonify({'error': f'チャート生成中にエラーが発生しました: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'OK', 'service': 'CycleMACD Web App'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)