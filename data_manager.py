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
            return True, required_start, required_end
        
        # 必要な範囲がデータベースの範囲内かチェック
        required_start_dt = datetime.strptime(required_start, '%Y-%m-%d')
        required_end_dt = datetime.strptime(required_end, '%Y-%m-%d')
        first_date_dt = datetime.strptime(first_date, '%Y-%m-%d')
        last_date_dt = datetime.strptime(last_date, '%Y-%m-%d')
        
        # 昨日までの最新データを取得（今日は取引中の可能性があるため）
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        # 更新が必要な範囲を計算
        fetch_start = required_start
        fetch_end = yesterday_str
        
        # 必要な開始日がDBの開始日より前の場合
        if required_start_dt < first_date_dt:
            fetch_start = required_start
        # DBに必要な開始日以降のデータがある場合
        elif required_start_dt >= first_date_dt:
            fetch_start = None
        
        # 必要な終了日がDBの終了日より後の場合、または昨日より古い場合
        if required_end_dt > last_date_dt or last_date_dt < yesterday:
            if fetch_start is None:
                # 既存データの次の日から取得
                next_day = last_date_dt + timedelta(days=1)
                fetch_start = next_day.strftime('%Y-%m-%d')
            fetch_end = yesterday_str
        else:
            if fetch_start is None:
                return False, None, None
        
        return True, fetch_start, fetch_end
    
    def get_company_name(self, symbol):
        """yfinanceから会社名を取得してDBに保存"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 会社名を取得（複数の属性を試す）
            company_name = None
            for name_field in ['longName', 'shortName', 'name']:
                if name_field in info and info[name_field]:
                    company_name = info[name_field]
                    break
            
            if not company_name:
                company_name = symbol  # フォールバック
            
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
            return symbol
    
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
        # まず会社名を取得
        company_name = self.get_company_name(symbol)
        
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


def get_japanese_stock_data(symbol, start_date, end_date, db_manager=None):
    """日本株データを取得する関数（データベース優先）"""
    if db_manager is None:
        db_manager = StockDataManager()
    
    print(f"  {symbol}のデータを取得中...")
    
    # 1990-01-01から昨日までの完全なデータを確保
    full_start = "1990-01-01"
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        # データベースの更新が必要かチェック
        needs_update, fetch_start, fetch_end = db_manager.needs_update(symbol, full_start, yesterday)
        
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
db_manager = StockDataManager()