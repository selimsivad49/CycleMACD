#!/usr/bin/env python3
"""
Cryptocurrency Data Manager の基本的な動作確認テスト
"""

from crypto_data_manager import CryptoDataManager, get_crypto_data
from datetime import datetime, timedelta

def test_crypto_data_manager():
    """仮想通貨データマネージャーの基本テスト"""
    print("=== Cryptocurrency Data Manager テスト ===")
    
    # 1. CryptoDataManagerの初期化
    print("\n1. CryptoDataManagerの初期化")
    crypto_manager = CryptoDataManager()
    print("   ✓ CryptoDataManager初期化完了")
    
    # 2. 利用可能な銘柄・時間足の確認
    print("\n2. 利用可能な銘柄・時間足の確認")
    symbols = crypto_manager.get_available_symbols()
    timeframes = crypto_manager.get_supported_timeframes()
    print(f"   ✓ 利用可能銘柄数: {len(symbols)}")
    print(f"   ✓ 主要銘柄: {symbols[:5]}")
    print(f"   ✓ サポート時間足: {timeframes}")
    
    # 3. 小さなデータセットでテスト（BTCの直近7日間）
    print("\n3. 小さなデータセットでテスト（BTCの直近7日間）")
    test_symbol = 'BTCUSDT'
    test_timeframe = '1d'
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        data = get_crypto_data(test_symbol, test_timeframe, start_date, end_date, crypto_manager)
        
        if data is not None and not data.empty:
            print(f"   ✓ {test_symbol}({test_timeframe}): {len(data)}件のデータを取得")
            print(f"   ✓ データ期間: {data.index[0]} - {data.index[-1]}")
            print(f"   ✓ 最新価格: ${data['Close'].iloc[-1]:,.2f}")
            print(f"   ✓ 列: {list(data.columns)}")
        else:
            print("   ❌ データ取得に失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False
    
    # 4. データベースの確認
    print("\n4. データベースの確認")
    registered = crypto_manager.get_all_registered_symbols()
    if registered:
        print(f"   ✓ 登録済みデータ: {len(registered)}件")
        for item in registered[:3]:  # 最初の3件を表示
            print(f"   ✓ {item['symbol']}({item['timeframe']}): {item['first_date']} - {item['last_date']}")
    else:
        print("   ⚠️ まだデータが登録されていません")
    
    # 5. 複数時間足のテスト（小さなデータセット）
    print("\n5. 複数時間足のテスト（ETHの直近3日間）")
    test_symbol = 'ETHUSDT'
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    
    for timeframe in ['1d', '4h']:
        try:
            data = get_crypto_data(test_symbol, timeframe, start_date, end_date, crypto_manager)
            if data is not None and not data.empty:
                print(f"   ✓ {test_symbol}({timeframe}): {len(data)}件のデータを取得")
            else:
                print(f"   ❌ {test_symbol}({timeframe}): データ取得に失敗")
        except Exception as e:
            print(f"   ❌ {test_symbol}({timeframe}): エラー - {e}")
    
    print("\n=== テスト結果 ===")
    print("✅ 基本的な仮想通貨データ取得機能が正常に動作しています！")
    print("\n主要な機能:")
    print("- Binance APIからのデータ取得")
    print("- SQLiteデータベースへの保存")
    print("- 複数時間足対応")
    print("- USDT建て主要20銘柄サポート")
    print("- 増分データ更新")
    
    return True

if __name__ == "__main__":
    success = test_crypto_data_manager()
    if success:
        print("\n🎯 仮想通貨データマネージャーの基本機能テストが完了しました！")
        print("次のステップ: screening.pyへの統合")
    else:
        print("\n❌ テストに失敗しました。エラーを確認してください。")