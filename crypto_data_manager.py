"""
Cryptocurrency Data Management Module for CycleMACD

Handles crypto data retrieval from Binance API, storage, and management using SQLite database.
Supports multiple timeframes and USDT-paired cryptocurrencies.
"""

import pandas as pd
import sqlite3
import os
import re
from datetime import datetime, timedelta
from binance.client import Client
import warnings
warnings.filterwarnings('ignore')

# データベース設定
CRYPTO_DB_NAME = "crypto_history.db"

# 時価総額Top20のUSDT建て銘柄（ステーブルコイン除く）
TOP_CRYPTO_SYMBOLS = [
    'BTCUSDT',   # Bitcoin
    'ETHUSDT',   # Ethereum
    'BNBUSDT',   # BNB
    'XRPUSDT',   # XRP
    'ADAUSDT',   # Cardano
    'DOGEUSDT',  # Dogecoin
    'SOLUSDT',   # Solana
    'SUIUSDT',   # Sui
    # 'HYPEUSDT',  # HyperLiquid
    'DOTUSDT',   # Polkadot
    'AVAXUSDT',  # Avalanche
    'SHIBUSDT',  # Shiba Inu
    'LTCUSDT',   # Litecoin
    'UNIUSDT',   # Uniswap
    'LINKUSDT',  # Chainlink
    'BCHUSDT',   # Bitcoin Cash
    'XLMUSDT',   # Stellar
    'ALGOUSDT',  # Algorand
    'VETUSDT',   # VeChain
    'FILUSDT',   # Filecoin
    'ATOMUSDT',  # Cosmos
]

# サポートされる時間足
SUPPORTED_TIMEFRAMES = {
    '1d': Client.KLINE_INTERVAL_1DAY,
    '4h': Client.KLINE_INTERVAL_4HOUR,
    '1h': Client.KLINE_INTERVAL_1HOUR,
    '15m': Client.KLINE_INTERVAL_15MINUTE,
}

class CryptoDataManager:
    """Binance API-based cryptocurrency data persistence manager"""
    
    def __init__(self, db_path=CRYPTO_DB_NAME):
        self.db_path = db_path
        self.client = Client()  # API keyなしでも履歴データは取得可能
        self.init_database()
    
    def init_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # メタデータテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbols_meta (
                symbol TEXT,
                timeframe TEXT,
                table_name TEXT,
                first_date TEXT,
                last_date TEXT,
                last_updated TEXT,
                PRIMARY KEY (symbol, timeframe)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_symbol_table(self, symbol, timeframe):
        """銘柄・時間足用のテーブルを作成"""
        table_name = self._get_table_name(symbol, timeframe)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp TEXT PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                quote_volume REAL,
                trades_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return table_name
    
    def _get_table_name(self, symbol, timeframe):
        """銘柄・時間足のテーブル名を取得"""
        # 例: crypto_BTCUSDT_1d, crypto_ETHUSDT_4h
        sanitized_symbol = re.sub(r'[^a-zA-Z0-9_]', '_', symbol)
        sanitized_timeframe = re.sub(r'[^a-zA-Z0-9_]', '_', timeframe)
        return f"crypto_{sanitized_symbol}_{sanitized_timeframe}"
    
    def get_data_range(self, symbol, timeframe):
        """データベースに保存されているデータの範囲を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT first_date, last_date FROM symbols_meta 
            WHERE symbol = ? AND timeframe = ?
        ''', (symbol, timeframe))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0], result[1]
        return None, None
    
    def save_data(self, symbol, timeframe, data):
        """データをデータベースに保存"""
        if data.empty:
            return
        
        table_name = self.create_symbol_table(symbol, timeframe)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # データを準備
        data_to_save = data.copy()
        data_to_save = data_to_save.reset_index()
        data_to_save.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trades_count']
        
        # timestampを文字列に変換（SQLite対応）
        data_to_save['timestamp'] = data_to_save['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 既存データを削除してから挿入（重複回避）
        for _, row in data_to_save.iterrows():
            cursor.execute(f'DELETE FROM {table_name} WHERE timestamp = ?', (row['timestamp'],))
        
        # データ挿入
        data_to_save.to_sql(table_name, conn, if_exists='append', index=False)
        
        # メタデータ更新
        new_first_date = data_to_save['timestamp'].min()
        new_last_date = data_to_save['timestamp'].max()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 既存のメタデータを取得
        cursor.execute('''
            SELECT first_date, last_date FROM symbols_meta 
            WHERE symbol = ? AND timeframe = ?
        ''', (symbol, timeframe))
        existing = cursor.fetchone()
        
        if existing:
            existing_first_date, existing_last_date = existing
            
            # first_dateは既存の方が古い場合は保持、新しいデータの方が古い場合は更新
            first_date = min(existing_first_date, new_first_date) if existing_first_date else new_first_date
            
            # last_dateは既存の方が新しい場合は保持、新しいデータの方が新しい場合は更新
            last_date = max(existing_last_date, new_last_date) if existing_last_date else new_last_date
        else:
            first_date = new_first_date
            last_date = new_last_date
        
        cursor.execute('''
            INSERT OR REPLACE INTO symbols_meta (symbol, timeframe, table_name, first_date, last_date, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbol, timeframe, table_name, first_date, last_date, current_time))
        
        conn.commit()
        conn.close()
        
        print(f"  {symbol}({timeframe}): データベースに保存 ({first_date} - {last_date})")
    
    def load_data(self, symbol, timeframe, start_date, end_date):
        """データベースからデータを読み込み"""
        table_name = self._get_table_name(symbol, timeframe)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = f'''
                SELECT * FROM {table_name}
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            '''
            
            data = pd.read_sql_query(query, conn, params=(start_date, end_date))
            
            if not data.empty:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data.set_index('timestamp', inplace=True)
                data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote_Volume', 'Trades_Count']
                print(f"  {symbol}({timeframe}): データベースから読み込み ({len(data)}件)")
                return data
            
        except Exception as e:
            print(f"  {symbol}({timeframe}): データベース読み込みエラー - {e}")
        finally:
            conn.close()
        
        return pd.DataFrame()
    
    def needs_update(self, symbol, timeframe, required_start, required_end):
        """データの更新が必要かチェック（データの抜けを適切に処理）"""
        first_date, last_date = self.get_data_range(symbol, timeframe)
        
        # データが全くない場合
        if first_date is None or last_date is None:
            return True, required_start, required_end, True  # 初回フラグを追加
        
        # 必要な範囲がデータベースの範囲内かチェック
        required_start_dt = pd.to_datetime(required_start)
        required_end_dt = pd.to_datetime(required_end)
        first_date_dt = pd.to_datetime(first_date)
        last_date_dt = pd.to_datetime(last_date)

        # 必要な範囲が完全にデータベースの範囲内にある場合は取得不要
        if first_date_dt <= required_start_dt and required_end_dt <= last_date_dt:
            return False, None, None, False

        # データの抜けを適切に処理するため、取得範囲を設定
        fetch_start = required_start
        fetch_end = required_end
        
        # より古いデータが必要な場合（データの抜けを避けるため既存の開始日まで取得）
        if required_start_dt < first_date_dt:
            fetch_start = required_start
            fetch_end = max(required_end, first_date)  # 既存データとの間を埋める
            
        # より新しいデータが必要な場合
        elif last_date_dt < required_end_dt:
            fetch_start = max(required_start, last_date)  # 既存データの最後から
            fetch_end = required_end
            
        # 既存データの範囲内だが、データの抜けがある可能性がある場合の追加処理は
        # 実際のデータ取得時に行う

        return True, fetch_start, fetch_end, False
    
    def fetch_from_binance(self, symbol, timeframe, start_date, end_date, is_initial=False):
        """Binance APIからデータを取得（最低1000本保証）"""
        try:
            print(f"  {symbol}({timeframe}): Binanceから取得中 ({start_date} - {end_date})")
            
            # Binanceの時間足形式に変換
            binance_interval = SUPPORTED_TIMEFRAMES.get(timeframe)
            if not binance_interval:
                raise ValueError(f"サポートされていない時間足: {timeframe}")
            
            # 初回取得の場合は最低1000本のデータを確保する
            if is_initial:
                # 現在日時から1000本分遡って開始日を計算
                from datetime import datetime, timedelta
                
                # 時間足に応じた期間を計算
                timeframe_hours = {
                    '1d': 24,
                    '4h': 4,
                    '1h': 1,
                    '15m': 0.25
                }
                
                hours_per_candle = timeframe_hours.get(timeframe, 24)
                total_hours = 1000 * hours_per_candle
                total_days = int(total_hours / 24) + 1  # 余裕を持たせる
                
                # より古い開始日を設定
                extended_start = (datetime.now() - timedelta(days=total_days)).strftime('%Y-%m-%d')
                if pd.to_datetime(extended_start) < pd.to_datetime(start_date):
                    start_date = extended_start
                    print(f"  {symbol}({timeframe}): 最低1000本確保のため開始日を {start_date} に変更")
            
            # 文字列の日付をms形式に変換
            if isinstance(start_date, str):
                start_date = start_date + " 00:00:00"
            if isinstance(end_date, str):
                end_date = end_date + " 23:59:59"
            
            all_data = []
            current_start = start_date
            
            # データを分割して取得（1000本制限対応）
            while True:
                # Binance APIから履歴データ取得
                klines = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=binance_interval,
                    start_str=current_start,
                    end_str=end_date,
                    limit=1000
                )
                
                if not klines:
                    break
                
                all_data.extend(klines)
                
                # 1000本未満の場合は終了
                if len(klines) < 1000:
                    break
                
                # 次の開始点を設定（最後のタイムスタンプの次）
                last_timestamp = klines[-1][0]
                last_dt = pd.to_datetime(last_timestamp, unit='ms')
                
                # 時間足に応じて次の開始時間を設定
                if timeframe == '1d':
                    next_start = last_dt + timedelta(days=1)
                elif timeframe == '4h':
                    next_start = last_dt + timedelta(hours=4)
                elif timeframe == '1h':
                    next_start = last_dt + timedelta(hours=1)
                elif timeframe == '15m':
                    next_start = last_dt + timedelta(minutes=15)
                else:
                    break
                
                current_start = next_start.strftime('%Y-%m-%d %H:%M:%S')
                
                # 終了日を超えた場合は終了
                if next_start >= pd.to_datetime(end_date):
                    break
            
            if not all_data:
                print(f"  {symbol}({timeframe}): データが見つかりませんでした")
                return pd.DataFrame()
            
            # DataFrame変換
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades_count', 
                'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
            ])
            
            # 必要な列のみ選択・変換
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trades_count']]
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 重複削除
            df = df.drop_duplicates(subset=['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # 数値型に変換
            for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['trades_count'] = pd.to_numeric(df['trades_count'], errors='coerce').astype(int)
            
            print(f"  {symbol}({timeframe}): {len(df)}件のデータを取得")
            return df
            
        except Exception as e:
            print(f"  {symbol}({timeframe}): Binance API エラー - {e}")
            return pd.DataFrame()
    
    def get_available_symbols(self):
        """利用可能なシンボルリストを取得"""
        return TOP_CRYPTO_SYMBOLS.copy()
    
    def get_supported_timeframes(self):
        """サポートされる時間足リストを取得"""
        return list(SUPPORTED_TIMEFRAMES.keys())
    
    def get_all_registered_symbols(self):
        """登録済みシンボルと時間足のリストを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, timeframe, first_date, last_date 
            FROM symbols_meta 
            ORDER BY symbol, timeframe
        ''')
        results = cursor.fetchall()
        conn.close()
        
        symbols_list = []
        for symbol, timeframe, first_date, last_date in results:
            symbols_list.append({
                'symbol': symbol,
                'timeframe': timeframe,
                'first_date': first_date,
                'last_date': last_date
            })
        
        return symbols_list


def get_crypto_data(symbol, timeframe, start_date, end_date, crypto_manager=None):
    """仮想通貨データを取得する関数（データベース優先）"""
    if crypto_manager is None:
        crypto_manager = CryptoDataManager()
    
    # 引数検証
    if symbol not in TOP_CRYPTO_SYMBOLS:
        print(f"  {symbol}: サポートされていない銘柄です")
        return None
    
    if timeframe not in SUPPORTED_TIMEFRAMES:
        print(f"  {timeframe}: サポートされていない時間足です")
        return None
    
    print(f"  {symbol}({timeframe}, {start_date} - {end_date})のデータを取得中...")
    
    try:
        # データベースの更新が必要かチェック
        needs_update, fetch_start, fetch_end, is_initial = crypto_manager.needs_update(symbol, timeframe, start_date, end_date)
        
        # 新しいデータが必要な場合、Binance APIから取得
        if needs_update and fetch_start and fetch_end:
            new_data = crypto_manager.fetch_from_binance(symbol, timeframe, fetch_start, fetch_end, is_initial)
            
            if not new_data.empty:
                # データベースに保存
                crypto_manager.save_data(symbol, timeframe, new_data)
            else:
                print(f"  {symbol}({timeframe}): Binanceからのデータ取得に失敗")
        
        # データベースから要求された期間のデータを読み込み
        data = crypto_manager.load_data(symbol, timeframe, start_date, end_date)
        
        if not data.empty:
            return data
        else:
            print(f"  {symbol}({timeframe}): 要求された期間のデータが見つかりません")
            return None
            
    except Exception as e:
        print(f"  {symbol}({timeframe}): データ取得エラー - {e}")
        return None


# グローバルインスタンス
# crypto_manager = CryptoDataManager()  # コメントアウト：必要時に初期化