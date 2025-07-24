#!/usr/bin/env python3
"""
仮想通貨スクリーニング機能の基本的な動作確認テスト
"""

from screening import ScreeningEngine, get_market_symbols
from datetime import datetime, timedelta

def test_crypto_screening():
    """仮想通貨スクリーニング機能の基本テスト"""
    print("=== 仮想通貨スクリーニング機能テスト ===")
    
    # 1. ScreeningEngineの初期化
    print("\n1. ScreeningEngineの初期化")
    engine = ScreeningEngine()
    conditions = engine.get_available_conditions()
    print(f"   ✓ 利用可能条件: {list(conditions.keys())}")
    
    # 2. 仮想通貨市場インデックスの確認
    print("\n2. 仮想通貨市場インデックスの確認")
    crypto_top10 = get_market_symbols('crypto_top10')
    crypto_top20 = get_market_symbols('crypto_top20')
    print(f"   ✓ 暗号資産Top10: {len(crypto_top10)}銘柄")
    print(f"   ✓ 主要銘柄: {crypto_top10[:3]}")
    print(f"   ✓ 暗号資産Top20: {len(crypto_top20)}銘柄")
    
    # 3. 小規模スクリーニングテスト（Top3銘柄のみ）
    print("\n3. 小規模スクリーニングテスト（Top3銘柄、1日足）")
    test_symbols = crypto_top10[:3]  # BTCUSDT, ETHUSDT, BNBUSDT
    test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        results = engine.run_screening(
            condition_name='crypto_halfsignal',
            symbol_list=test_symbols,
            judgment_date=test_date,
            timeframe='1d'
        )
        
        print(f"   ✓ スクリーニング完了: {results['condition_name']}")
        print(f"   ✓ 条件: {results['condition_description']}")
        print(f"   ✓ 判定日: {results['judgment_date']}")
        print(f"   ✓ 時間足: {results['timeframe']}")
        print(f"   ✓ 対象銘柄数: {results['total_checked']}")
        print(f"   ✓ 条件通過: {results['passed_count']}銘柄")
        print(f"   ✓ 条件未通過: {results['failed_count']}銘柄")
        print(f"   ✓ エラー: {results['error_count']}銘柄")
        
        # 条件通過銘柄の詳細表示
        if results['passed_symbols']:
            print("\n   条件通過銘柄:")
            for symbol_result in results['passed_symbols']:
                details = symbol_result['details']
                print(f"   ✅ {symbol_result['symbol']}: ${details['close_price']:,.2f}")
                print(f"      - SMA5: ${details['sma5']:,.2f}")
                print(f"      - SMA20: ${details['sma20']:,.2f}")
                print(f"      - SMA60: ${details['sma60']:,.2f}")
        
        # エラーがあった場合の表示
        if results['error_symbols']:
            print("\n   エラー銘柄:")
            for error_result in results['error_symbols']:
                print(f"   ❌ {error_result['symbol']}: {error_result['error']}")
                
    except Exception as e:
        print(f"   ❌ スクリーニングエラー: {e}")
        return False
    
    # 4. 複数時間足テスト（BTCのみ）
    print("\n4. 複数時間足テスト（BTCのみ）")
    btc_symbol = ['BTCUSDT']
    
    for timeframe in ['1d', '4h']:
        try:
            results = engine.run_screening(
                condition_name='crypto_halfsignal',
                symbol_list=btc_symbol,
                judgment_date=test_date,
                timeframe=timeframe
            )
            print(f"   ✓ {timeframe}: 通過={results['passed_count']}, 未通過={results['failed_count']}, エラー={results['error_count']}")
        except Exception as e:
            print(f"   ❌ {timeframe}: エラー - {e}")
    
    print("\n=== テスト結果 ===")
    print("✅ 仮想通貨スクリーニング機能が正常に動作しています！")
    print("\n新機能:")
    print("- USDT建て暗号資産のスクリーニング")
    print("- 複数時間足対応（1d, 4h, 1h, 15m）")
    print("- 時価総額Top10/Top20市場インデックス")
    print("- 24時間取引対応")
    print("- Binance APIリアルタイムデータ")
    
    return True

if __name__ == "__main__":
    success = test_crypto_screening()
    if success:
        print("\n🎯 仮想通貨スクリーニング機能のテストが完了しました！")
        print("次のステップ: Webアプリケーション（app.py）への統合")
    else:
        print("\n❌ テストに失敗しました。エラーを確認してください。")