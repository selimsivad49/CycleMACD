"""
Data Management Module for CycleMACD

Handles stock data retrieval, storage, and management using SQLite database.
Supports incremental data updates and multiple ticker formats.
"""

import yfinance as yf
import pandas as pd
import sqlite3
import os
import re
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# データベース設定
DB_NAME = "yf_history.db"

class StockDataManager:
    """SQLite-based stock data persistence manager"""
    
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 既存テーブルの構造を確認
        cursor.execute("PRAGMA table_info(symbols_meta)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'symbols_meta' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            # テーブルが存在しない場合は作成
            cursor.execute('''
                CREATE TABLE symbols_meta (
                    symbol TEXT PRIMARY KEY,
                    table_name TEXT,
                    company_name TEXT,
                    first_date TEXT,
                    last_date TEXT,
                    last_updated TEXT
                )
            ''')
        elif 'company_name' not in columns:
            # company_nameカラムが存在しない場合は追加
            cursor.execute('ALTER TABLE symbols_meta ADD COLUMN company_name TEXT')
        
        conn.commit()
        conn.close()
    
    def create_symbol_table(self, symbol):
        """銘柄用のテーブルを作成"""
        table_name = self._sanitize_table_name(symbol)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                date TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                dividends REAL,
                stock_splits REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return table_name
    
    def _sanitize_table_name(self, symbol):
        """シンボル名をテーブル名として使えるようにサニタイズ"""
        # 英数字とアンダースコア以外を除去し、stockプレフィックスを追加
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', symbol)
        # 連続するアンダースコアを1つにまとめる
        sanitized = re.sub(r'_+', '_', sanitized)
        # 先頭・末尾のアンダースコアを除去
        sanitized = sanitized.strip('_')
        return f"stock_{sanitized}"
    
    def get_table_name(self, symbol):
        """銘柄のテーブル名を取得"""
        return self._sanitize_table_name(symbol)
    
    def get_data_range(self, symbol):
        """データベースに保存されているデータの範囲を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT first_date, last_date FROM symbols_meta WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0], result[1]
        return None, None
    
    def save_data(self, symbol, data):
        """データをデータベースに保存"""
        if data.empty:
            return
        
        table_name = self.create_symbol_table(symbol)
        
        conn = sqlite3.connect(self.db_path)
        
        # データを準備
        data_to_save = data.copy()
        data_to_save.index = data_to_save.index.strftime('%Y-%m-%d')
        data_to_save = data_to_save.reset_index()
        data_to_save.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits']
        
        # 既存データを削除してから挿入（重複回避）
        cursor = conn.cursor()
        for _, row in data_to_save.iterrows():
            cursor.execute(f'DELETE FROM {table_name} WHERE date = ?', (row['date'],))
        
        # データ挿入
        data_to_save.to_sql(table_name, conn, if_exists='append', index=False)
        
        # メタデータ更新
        first_date = data_to_save['date'].min()
        last_date = data_to_save['date'].max()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 会社名を取得（既存の場合は保持）
        cursor.execute('SELECT company_name FROM symbols_meta WHERE symbol = ?', (symbol,))
        existing_name = cursor.fetchone()
        company_name = existing_name[0] if existing_name else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO symbols_meta (symbol, table_name, company_name, first_date, last_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, table_name, company_name, first_date, last_date, current_time))
        
        conn.commit()
        conn.close()
        
        print(f"  {symbol}: データベースに保存 ({first_date} - {last_date})")
    
    def load_data(self, symbol, start_date, end_date):
        """データベースからデータを読み込み"""
        table_name = self.get_table_name(symbol)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = f'''
                SELECT * FROM {table_name}
                WHERE date >= ? AND date <= ?
                ORDER BY date
            '''
            
            data = pd.read_sql_query(query, conn, params=(start_date, end_date))
            
            if not data.empty:
                data['date'] = pd.to_datetime(data['date'])
                data.set_index('date', inplace=True)
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
                print(f"  {symbol}: データベースから読み込み ({len(data)}件)")
                return data
            
        except Exception as e:
            print(f"  {symbol}: データベース読み込みエラー - {e}")
        finally:
            conn.close()
        
        return pd.DataFrame()
    
    def needs_update(self, symbol, required_start, required_end):
        """データの更新が必要かチェック"""
        first_date, last_date = self.get_data_range(symbol)
        
        if first_date is None or last_date is None:
            print(f'required_start/required_end: {required_start} / {required_end}')
            return True, required_start, required_end
        
        # 必要な範囲がデータベースの範囲内かチェック
        required_start_dt = datetime.strptime(required_start, '%Y-%m-%d')
        required_end_dt = datetime.strptime(required_end, '%Y-%m-%d')
        first_date_dt = datetime.strptime(first_date, '%Y-%m-%d')
        last_date_dt = datetime.strptime(last_date, '%Y-%m-%d')
        
        # 更新が必要な範囲を計算
        fetch_start = required_start
        fetch_end = required_end
        
        # 取得不要
        if first_date_dt <= required_start_dt and required_end_dt <= last_date_dt:
            return False, None, None

        # 取得範囲設定
        if required_start_dt < first_date_dt:
            fetch_start = required_start
        else:
            fetch_start = required_end

        if last_date_dt < required_end_dt:
            fetch_end = required_end
        else:
            fetch_end = required_start

        print(f'required_start/required_end: {required_start} / {required_end}')
        print(f'first_date/last_date       : {first_date} / {last_date}')
        print(f'fetch_start/fetch_end      : {fetch_start} / {fetch_end}')
        return True, fetch_start, fetch_end
    
    def get_company_name(self, symbol):
        """yfinanceから会社名を取得してDBに保存"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # シンボルが有効かチェック（infoが空またはregularMarketPriceがない場合は無効）
            if not info or len(info) < 5:
                print(f"  {symbol}: yfinanceで見つかりませんでした")
                return None
            
            # 会社名を取得（複数の属性を試す）
            company_name = None
            for name_field in ['longName', 'shortName', 'name']:
                if name_field in info and info[name_field]:
                    company_name = info[name_field]
                    break
            
            if not company_name:
                # 会社名が取得できない場合もシンボルが無効とみなす
                print(f"  {symbol}: 会社名を取得できませんでした")
                return None
            
            # DBに保存
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE symbols_meta SET company_name = ? WHERE symbol = ?
            ''', (company_name, symbol))
            conn.commit()
            conn.close()
            
            print(f"  {symbol}: 会社名を取得・保存 ({company_name})")
            return company_name
            
        except Exception as e:
            print(f"  {symbol}: 会社名取得エラー - {e}")
            return None
    
    def get_all_registered_symbols(self):
        """登録済みシンボルと会社名のリストを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, company_name, first_date, last_date 
            FROM symbols_meta 
            ORDER BY symbol
        ''')
        results = cursor.fetchall()
        conn.close()
        
        symbols_list = []
        for symbol, company_name, first_date, last_date in results:
            # 会社名がない場合は取得
            if not company_name:
                company_name = self.get_company_name(symbol)
            
            symbols_list.append({
                'symbol': symbol,
                'company_name': company_name or symbol,
                'first_date': first_date,
                'last_date': last_date
            })
        
        return symbols_list
    
    def add_symbol_with_name(self, symbol):
        """新しいシンボルを会社名と共に追加"""
        # まず会社名を取得（yfinanceで見つからない場合はNoneが返される）
        company_name = self.get_company_name(symbol)
        
        if company_name is None:
            # yfinanceで見つからない場合はDBに登録しない
            return None
        
        # シンボルテーブルを作成
        table_name = self.create_symbol_table(symbol)
        
        # メタデータに追加（データはまだないので日付はNULL）
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT OR REPLACE INTO symbols_meta (symbol, table_name, company_name, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (symbol, table_name, company_name, current_time))
        
        conn.commit()
        conn.close()
        
        return company_name
    
    def fix_metadata_dates(self, symbol=None):
        """
        メタデータテーブルのfirst_date/last_dateを実際のデータに基づいて修正
        
        Args:
            symbol: 修正対象のシンボル（Noneの場合は全シンボル）
        
        Returns:
            dict: 修正結果の統計情報
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 対象シンボルを取得
        if symbol:
            cursor.execute('SELECT symbol, table_name FROM symbols_meta WHERE symbol = ?', (symbol,))
            symbols_to_fix = cursor.fetchall()
        else:
            cursor.execute('SELECT symbol, table_name FROM symbols_meta')
            symbols_to_fix = cursor.fetchall()
        
        fixed_count = 0
        error_count = 0
        results = []
        
        for sym, table_name in symbols_to_fix:
            try:
                # 実際のテーブルから最小・最大日付を取得
                cursor.execute(f'SELECT MIN(date), MAX(date), COUNT(*) FROM {table_name}')
                result = cursor.fetchone()
                
                if result and result[0] and result[1]:
                    actual_first_date, actual_last_date, record_count = result
                    
                    # メタデータの現在の値を取得
                    cursor.execute('SELECT first_date, last_date FROM symbols_meta WHERE symbol = ?', (sym,))
                    meta_result = cursor.fetchone()
                    old_first_date, old_last_date = meta_result if meta_result else (None, None)
                    
                    # メタデータを更新
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        UPDATE symbols_meta 
                        SET first_date = ?, last_date = ?, last_updated = ?
                        WHERE symbol = ?
                    ''', (actual_first_date, actual_last_date, current_time, sym))
                    
                    # 結果を記録
                    result_info = {
                        'symbol': sym,
                        'old_first_date': old_first_date,
                        'old_last_date': old_last_date,
                        'new_first_date': actual_first_date,
                        'new_last_date': actual_last_date,
                        'record_count': record_count,
                        'changed': (old_first_date != actual_first_date or old_last_date != actual_last_date)
                    }
                    results.append(result_info)
                    
                    if result_info['changed']:
                        fixed_count += 1
                        print(f"  {sym}: 修正 {old_first_date}～{old_last_date} → {actual_first_date}～{actual_last_date} ({record_count}件)")
                    else:
                        print(f"  {sym}: 変更なし {actual_first_date}～{actual_last_date} ({record_count}件)")
                else:
                    print(f"  {sym}: データなし（テーブル: {table_name}）")
                    error_count += 1
                    
            except Exception as e:
                print(f"  {sym}: エラー - {e}")
                error_count += 1
        
        conn.commit()
        conn.close()
        
        return {
            'total_symbols': len(symbols_to_fix),
            'fixed_count': fixed_count,
            'error_count': error_count,
            'unchanged_count': len(symbols_to_fix) - fixed_count - error_count,
            'results': results
        }
    
    def validate_all_metadata(self):
        """
        全シンボルのメタデータと実データの整合性をチェック
        
        Returns:
            dict: チェック結果の詳細
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT symbol, table_name, first_date, last_date FROM symbols_meta')
        all_symbols = cursor.fetchall()
        
        inconsistent_symbols = []
        missing_tables = []
        consistent_symbols = []
        
        for symbol, table_name, meta_first, meta_last in all_symbols:
            try:
                # テーブルの存在確認
                cursor.execute(f'SELECT MIN(date), MAX(date), COUNT(*) FROM {table_name}')
                result = cursor.fetchone()
                
                if result and result[0] and result[1]:
                    actual_first, actual_last, count = result
                    
                    if meta_first != actual_first or meta_last != actual_last:
                        inconsistent_symbols.append({
                            'symbol': symbol,
                            'meta_first': meta_first,
                            'meta_last': meta_last,
                            'actual_first': actual_first,
                            'actual_last': actual_last,
                            'record_count': count
                        })
                    else:
                        consistent_symbols.append({
                            'symbol': symbol,
                            'first_date': actual_first,
                            'last_date': actual_last,
                            'record_count': count
                        })
                else:
                    missing_tables.append({
                        'symbol': symbol,
                        'table_name': table_name
                    })
                    
            except Exception as e:
                missing_tables.append({
                    'symbol': symbol,
                    'table_name': table_name,
                    'error': str(e)
                })
        
        conn.close()
        
        return {
            'total_symbols': len(all_symbols),
            'consistent_count': len(consistent_symbols),
            'inconsistent_count': len(inconsistent_symbols),
            'missing_table_count': len(missing_tables),
            'consistent_symbols': consistent_symbols,
            'inconsistent_symbols': inconsistent_symbols,
            'missing_tables': missing_tables
        }


def get_japanese_stock_data(symbol, start_date, end_date, db_manager=None):
    """日本株データを取得する関数（データベース優先）"""
    if db_manager is None:
        db_manager = StockDataManager()
    
    print(f"  {symbol}({start_date} - {end_date})のデータを取得中...")
    
    try:
        # データベースの更新が必要かチェック（要求された範囲のみ）
        needs_update, fetch_start, fetch_end = db_manager.needs_update(symbol, start_date, end_date)
        print(f"  needs_update: {needs_update}({fetch_start} - {fetch_end})")
        
        # 新しいデータが必要な場合、yfinanceから取得
        if needs_update and fetch_start and fetch_end:
            print(f"  {symbol}: yfinanceから取得中 ({fetch_start} - {fetch_end})")
            
            # 日本株のティッカー形式を試す
            ticker_formats = [symbol]
            
            new_data = None
            for ticker_format in ticker_formats:
                try:
                    stock = yf.Ticker(ticker_format)
                    new_data = stock.history(start=fetch_start, end=fetch_end, interval='1d')
                    
                    if not new_data.empty:
                        print(f"  {ticker_format}で成功！({len(new_data)}件)")
                        break
                        
                except Exception as e:
                    continue
            
            if new_data is not None and not new_data.empty:
                # データベースに保存
                db_manager.save_data(symbol, new_data)
            else:
                print(f"  {symbol}: yfinanceからのデータ取得に失敗")
        
        # データベースから要求された期間のデータを読み込み
        data = db_manager.load_data(symbol, start_date, end_date)
        
        if not data.empty:
            return data
        else:
            print(f"  {symbol}: 要求された期間のデータが見つかりません")
            return None
            
    except Exception as e:
        print(f"  {symbol}: データ取得エラー - {e}")
        return None


# グローバルインスタンス（後方互換性のため）
# db_manager = StockDataManager()  # コメントアウト：必要時に初期化