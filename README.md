# CycleMACD - Japanese Stock MACD Backtesting System

## 概要 / Overview

CycleMACDは、日本株のMACDヒストグラム戦略によるバックテストシステムです。Webアプリケーションとして動作し、複数の日本株銘柄を同時に分析できます。

CycleMACD is a backtesting system for Japanese stocks using MACD histogram strategy. It operates as a web application and can analyze multiple Japanese stock symbols simultaneously.

![CycleMACD Demo](https://img.shields.io/badge/Demo-Live-green) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0+-red)

## 主な機能 / Key Features

### 📊 分析機能 / Analytics
- **MACDヒストグラム戦略**: ゼロライン交差による売買シグナル生成
- **複数銘柄同時分析**: 最大10銘柄を一括でバックテスト
- **パフォーマンス指標**: リターン、勝率、最大ドローダウン、シャープレシオ
- **期間指定**: 任意の日付範囲でのバックテスト実行

### 🖥️ Webアプリケーション / Web Application
- **レスポンシブUI**: Bootstrap 5ベースの現代的なインターフェース
- **リアルタイムチャート**: matplotlib による詳細な可視化
- **インタラクティブ操作**: ブラウザから簡単に操作可能

### 📈 対象銘柄 / Target Stocks
- 7203: トヨタ自動車 (Toyota Motor)
- 6758: ソニーグループ (Sony Group)
- 9984: ソフトバンクグループ (SoftBank Group)
- 6861: キーエンス (Keyence)
- 4519: 中外製薬 (Chugai Pharmaceutical)
- 8306: 三菱UFJフィナンシャル・グループ (MUFG)
- 6098: リクルートホールディングス (Recruit Holdings)
- 4063: 信越化学工業 (Shin-Etsu Chemical)
- 9983: ファーストリテイリング (Fast Retailing)
- 7974: 任天堂 (Nintendo)

## セットアップ / Setup

### 必要な環境 / Requirements
- Python 3.11+
- pip (Python package manager)

### インストール / Installation

1. **リポジトリのクローン / Clone Repository**
```bash
git clone https://github.com/YOUR_USERNAME/CycleMACD.git
cd CycleMACD
```

2. **依存パッケージのインストール / Install Dependencies**
```bash
pip install -r requirements.txt
```

### 起動方法 / Launch

**簡単起動 / Easy Launch:**
```bash
python3 run_webapp.py
```

**直接起動 / Direct Launch:**
```bash
python3 app.py
```

**アクセス / Access:**
ブラウザで `http://localhost:5000` を開いてください

## 使用方法 / Usage

1. **銘柄選択**: 分析したい銘柄にチェックを入れる
2. **期間設定**: 開始日と終了日を指定 (デフォルト: 2020-01-01 ～ 2024-12-31)
3. **分析開始**: 「分析開始」ボタンをクリック
4. **結果確認**: 各銘柄のパフォーマンス指標を確認
5. **チャート表示**: 個別銘柄の詳細チャートを表示

## MACD戦略 / MACD Strategy

### 戦略ロジック / Strategy Logic
- **買いシグナル**: MACDヒストグラムが0を上回る
- **売りシグナル**: MACDヒストグラムが0を下回る
- **パラメータ**: EMA12, EMA26, Signal9 (標準設定)

### パフォーマンス指標 / Performance Metrics
- **戦略リターン**: MACD戦略による総リターン
- **市場リターン**: バイ&ホールド戦略との比較
- **勝率**: 利益を上げた取引の割合
- **最大ドローダウン**: 最大損失期間
- **シャープレシオ**: リスク調整後リターン

## ファイル構成 / File Structure

```
CycleMACD/
├── app.py                 # メインFlaskアプリケーション
├── cyclemacd.py          # MACD分析エンジン
├── run_webapp.py         # 起動スクリプト
├── requirements.txt      # 依存パッケージ
├── README.md            # プロジェクト説明書
├── README_webapp.md     # Webアプリ詳細説明
├── CLAUDE.md            # Claude Code用設定
├── templates/
│   └── index.html       # Webページテンプレート
├── static/
│   ├── css/
│   │   └── style.css    # スタイルシート
│   └── js/
│       └── app.js       # JavaScript
├── simple_test.py       # 基本機能テスト
└── test_cyclemacd.py    # 単体テスト
```

## API エンドポイント / API Endpoints

- `GET /`: メインページ
- `POST /analyze`: 株式分析実行
- `GET /chart/<symbol>`: 個別銘柄チャート生成
- `GET /health`: ヘルスチェック

## 技術スタック / Tech Stack

### バックエンド / Backend
- **Python 3.11+**: メイン言語
- **Flask 3.0+**: Webフレームワーク
- **pandas 2.0+**: データ処理
- **numpy**: 数値計算
- **matplotlib**: グラフ生成
- **yfinance**: 株価データ取得

### フロントエンド / Frontend
- **Bootstrap 5**: UIフレームワーク
- **Vanilla JavaScript**: インタラクション
- **Font Awesome**: アイコン

## 開発・テスト / Development & Testing

### 基本テスト実行 / Run Basic Tests
```bash
python3 simple_test.py
```

### 単体テスト実行 / Run Unit Tests
```bash
python3 test_cyclemacd.py
```

## 注意事項 / Important Notes

⚠️ **免責事項 / Disclaimer**
- このシステムは教育・研究目的のデモンストレーションです
- 実際の投資判断には使用しないでください
- 過去のパフォーマンスは将来の結果を保証しません
- 投資は自己責任で行ってください

## ライセンス / License

このプロジェクトはMITライセンスの下で公開されています。

## 貢献 / Contributing

プルリクエストやイシューは歓迎します。大きな変更を行う前に、まずイシューを作成して議論してください。

## 作成者 / Author

🤖 Generated with [Claude Code](https://claude.ai/code)

## バージョン履歴 / Version History

- **v1.0.0** (2025-01-13): 初回リリース
  - MACDバックテストエンジン
  - Flask Webアプリケーション
  - 10銘柄対応
  - チャート生成機能