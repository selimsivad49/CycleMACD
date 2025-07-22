#!/usr/bin/env python3
"""
yf_historyデータベースのsymbols_metaテーブルのfirst_date/last_dateを修正

実際のテーブルデータとメタデータの不整合を修正します。
"""

from data_manager import StockDataManager
import sys

def main():
    """メタデータの修正を実行"""
    db_manager = StockDataManager()
    
    print("=== yf_history データベース メタデータ修正ツール ===")
    
    # 修正前の状態をチェック
    print("\n1. 修正前の整合性チェック...")
    validation_result = db_manager.validate_all_metadata()
    
    print(f"   総シンボル数: {validation_result['total_symbols']}")
    print(f"   整合性OK: {validation_result['consistent_count']}")
    print(f"   不整合: {validation_result['inconsistent_count']}")
    print(f"   テーブル欠損: {validation_result['missing_table_count']}")
    
    if validation_result['inconsistent_count'] > 0:
        print("\n不整合シンボルの詳細:")
        for item in validation_result['inconsistent_symbols'][:5]:  # 最初の5件のみ表示
            print(f"   {item['symbol']}: メタ[{item['meta_first']}～{item['meta_last']}] vs 実際[{item['actual_first']}～{item['actual_last']}] ({item['record_count']}件)")
        
        if len(validation_result['inconsistent_symbols']) > 5:
            print(f"   ... 他 {len(validation_result['inconsistent_symbols']) - 5} 件")
    
    if validation_result['missing_table_count'] > 0:
        print("\nテーブル欠損シンボル:")
        for item in validation_result['missing_tables']:
            if 'error' in item:
                print(f"   {item['symbol']}: エラー - {item['error']}")
            else:
                print(f"   {item['symbol']}: テーブル '{item['table_name']}' が見つかりません")
    
    # 修正が必要かどうか確認
    if validation_result['inconsistent_count'] == 0:
        print("\n全てのメタデータが整合性を保っています。修正は不要です。")
        return
    
    # ユーザー確認
    print(f"\n2. メタデータ修正の実行")
    print(f"   {validation_result['inconsistent_count']} 個のシンボルのメタデータを修正します。")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("   自動実行モードで修正を開始...")
    else:
        response = input("   修正を実行しますか？ (y/N): ").strip().lower()
        if response != 'y':
            print("   修正をキャンセルしました。")
            return
    
    # 修正実行
    print("\n修正を実行中...")
    fix_result = db_manager.fix_metadata_dates()
    
    print(f"\n修正完了！")
    print(f"   対象シンボル数: {fix_result['total_symbols']}")
    print(f"   修正済み: {fix_result['fixed_count']}")
    print(f"   変更なし: {fix_result['unchanged_count']}")
    print(f"   エラー: {fix_result['error_count']}")
    
    # 修正後の確認
    print("\n3. 修正後の整合性チェック...")
    final_validation = db_manager.validate_all_metadata()
    
    print(f"   整合性OK: {final_validation['consistent_count']}")
    print(f"   不整合: {final_validation['inconsistent_count']}")
    
    if final_validation['inconsistent_count'] == 0:
        print("\n✅ 全ての不整合が修正されました！")
    else:
        print(f"\n⚠️  まだ {final_validation['inconsistent_count']} 個の不整合があります。")
        print("   手動での確認が必要な可能性があります。")

if __name__ == "__main__":
    main()