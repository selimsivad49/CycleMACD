# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CycleMACD is a sophisticated financial trading analysis system that combines Japanese stock backtesting with cryptocurrency screening capabilities. The system implements MACD histogram-based trading signals for stocks with multi-timeframe analysis, while providing advanced SMA-based screening for both Japanese equities and USDT-paired cryptocurrencies. Features include Flask web application interface, dual SQLite database architecture, comprehensive data persistence, and supports daily/weekly/monthly backtesting with detailed trade history tracking, Long/Short performance analysis, and advanced screening conditions across multiple asset classes.

## Common Commands

### Development and Execution
```bash
# Web Application (Primary Interface)
python3 run_webapp.py          # User-friendly launcher with startup messages
python3 app.py                 # Direct Flask application launch

# Command Line Analysis
python3 cyclemacd.py           # Direct backtesting execution

# Testing and Validation
python3 simple_test.py         # Basic functionality validation using standard libraries
python3 test_cyclemacd.py      # Comprehensive unit tests with dummy data generation
```

### Database Management
```bash
# Stock database metadata maintenance  
python3 fix_metadata.py         # Fix inconsistencies between metadata and actual data
python3 fix_metadata.py --auto  # Auto-fix without confirmation

# Manual database validation
python3 -c "from data_manager import StockDataManager; dm = StockDataManager(); print(dm.validate_all_metadata())"

# Cryptocurrency database testing
python3 test_crypto.py           # Basic crypto data manager functionality test
python3 test_crypto_screening.py # Cryptocurrency screening system test
```

### Dependencies
```bash
pip install -r requirements.txt
```

Core dependencies: Flask 3.0+, yfinance 0.2+, pandas 2.0+, matplotlib 3.5+, japanize-matplotlib, numpy 1.20+, seaborn 0.11+, python-binance 1.0.29+

## High-Level Architecture

### Core Module Structure

**data_manager.py** - SQLite-based data persistence layer for Japanese stocks:
- **StockDataManager**: Manages `yf_history.db` with symbol-specific tables
- **Incremental Updates**: Fetches only missing data ranges (1990-01-01 to yesterday)
- **Symbol Sanitization**: Handles special characters (e.g., "NIY=F" → "stock_NIY_F")
- **Company Name Resolution**: Automatic fetching and storage of company metadata

**crypto_data_manager.py** - Binance API-based cryptocurrency data management:
- **CryptoDataManager**: Manages `crypto_history.db` with timeframe-specific tables
- **Multi-Timeframe Support**: 1d, 4h, 1h, 15m intervals with separate table storage
- **USDT Pairs**: Top 20 market cap cryptocurrencies (excluding stablecoins)
- **24/7 Trading**: No market hours restrictions, continuous data availability
- **Binance Integration**: Real-time data fetching without API keys for historical data

**strategies.py** - Multi-timeframe backtesting engine:
- **MACDBacktester**: Core backtesting with timeframes D/W/M
- **Adaptive Parameters**: Timeframe-specific MACD scaling (Daily: 20x, Weekly: 4x, Monthly: 1x)
- **2-Month Lag Logic**: Realistic signal generation (compares i-2 vs i-1 for i-period entry)
- **Long/Short Analytics**: Separate performance tracking by trade direction

**screening.py** - Advanced dual-asset screening system:
- **HalfSignal**: SMA-based screening for Japanese stocks with complex candlestick analysis
- **CryptoHalfSignal**: Cryptocurrency adaptation with multi-timeframe support and 24/7 logic
- **ScreeningEngine**: Unified batch processing across both asset classes
- **Market Indices**: Japanese stocks (Nikkei 225, JPX400) + Crypto (Top10/Top20 USDT pairs)
- **Visual Charts**: 60-day candlestick charts with SMA overlays and judgment day indicators
- **Dual Calendar Logic**: Japanese trading hours for stocks, continuous for cryptocurrencies

**utils.py** - Utility functions and Japanese market support:
- **Trading Day Calculations**: Japanese time zone and market calendar logic
- **Performance Metrics**: Sharpe ratio, volatility, drawdown calculations
- **Default Symbol Management**: Pre-configured Japanese stock lists

**app.py** - Flask web application with dual-asset support:
- **Multi-interface Support**: Main UI, legacy interface, unified screening, backtesting
- **Dynamic Symbol Management**: Add/validate symbols with company name resolution for stocks
- **Dual Asset Routing**: Automatic stock/crypto detection and appropriate data manager selection
- **Chart Generation**: Matplotlib-based visualization with trade statistics for both asset classes
- **Timeframe Selection**: Dynamic UI adaptation for cryptocurrency multi-timeframe analysis

### Data Flow and Architecture Patterns

**Dual Data Acquisition Pipeline**:
1. **Stock Pipeline**: Database check in `yf_history.db` → Gap analysis → yfinance API → Incremental storage
2. **Crypto Pipeline**: Database check in `crypto_history.db` → Gap analysis → Binance API → Multi-timeframe storage
3. **Symbol Validation**: Stock symbols via yfinance info, crypto symbols via Binance market data
4. **Metadata Management**: Company names for stocks, market cap ranking for cryptocurrencies
5. **Error Handling**: Graceful degradation with detailed logging for both data sources

**Multi-Timeframe Processing**:
1. Daily data acquisition and storage
2. Timeframe-specific resampling (D→W→M)
3. Adaptive MACD parameter scaling by timeframe
4. Signal generation with 2-month lag for realism
5. Performance calculation with appropriate annualization factors

**Web Application Request Flow**:
1. Route handling with parameter validation and asset type detection
2. **Stock Flow**: Database-first data retrieval from yf_history.db → Strategy execution
3. **Crypto Flow**: Database-first data retrieval from crypto_history.db → Multi-timeframe screening
4. Chart generation with asset-appropriate formatting (¥ for stocks, USDT for crypto)
5. Template rendering with unified results display and asset-specific metadata

### Flask Application Architecture

**Route Structure**:
- `GET /` - Main parameter selection interface with symbol management
- `GET /old` - Legacy multi-symbol analysis interface  
- `POST /add_symbol` - Dynamic symbol addition with yfinance validation
- `POST /analyze` - Multi-symbol backtesting execution
- `GET /chart/<symbol>` - Individual chart generation with trade statistics
- `GET /backtest` - Single-symbol detailed backtest results
- `GET /screening` - Unified screening execution for both stocks and cryptocurrencies with timeframe support
- `GET /health` - Application health check

**Template Architecture**:
- **parameter_selection.html**: Main interface with dynamic stock/crypto switching, timeframe selection, unified screening controls
- **backtest_result.html**: Comprehensive single-symbol results with charts and statistics
- **screening_result.html**: Unified screening results with asset-appropriate displays and chart generation
- **index.html**: Legacy multi-symbol analysis interface (stocks only)

### Multi-Asset Market Integration

**Stock Market Indices Support**:
- **Nikkei 225**: 225+ carefully curated symbols with .T suffix
- **JPX400**: Extended symbol list including JPX400 additional constituents
- **TPX10**: Top 10 market cap Japanese stocks
- **Symbol Validation**: yfinance compatibility checking before database storage

**Cryptocurrency Market Indices Support**:
- **Crypto Top10**: Top 10 market cap USDT-paired cryptocurrencies
- **Crypto Top20**: Top 20 market cap USDT-paired cryptocurrencies (excluding stablecoins)
- **Binance Integration**: Real-time symbol validation via Binance market data
- **Market Coverage**: BTC, ETH, BNB, XRP, ADA, DOGE, SOL, DOT, AVAX, SHIB, LTC, UNI, LINK, BCH, XLM, ALGO, VET, FIL, ATOM

**Trading Calendar Logic**:
- **Stock Markets**: JST-aware date calculations with 0-9 JST defaults to previous day
- **Weekend Handling**: Saturday/Sunday defaults to previous Friday for stocks
- **Holiday Awareness**: Integration with Japanese trading calendar for stocks
- **Cryptocurrency Markets**: 24/7 trading with no market hour restrictions
- **Dual Logic**: Asset-type detection automatically applies appropriate calendar rules

### Trading Strategy Implementation

**MACD Signal Logic**:
- **Buy Signal**: MACD histogram crosses from ≤0 to >0 (2-month lag comparison)
- **Sell Signal**: MACD histogram crosses from >0 to ≤0 (2-month lag comparison)
- **Position Management**: Automatic Long/Short position reversal on signal changes

**Timeframe Scaling**:
- **Daily**: MACD(240,520,180) - 20x monthly parameters for high-frequency data
- **Weekly**: MACD(48,104,36) - 4x monthly parameters for weekly sampling
- **Monthly**: MACD(12,26,9) - Standard parameters for monthly analysis

**Performance Analytics**:
- **Overall Metrics**: Total return, Sharpe ratio, maximum drawdown, win rate
- **Direction-Specific**: Separate Long/Short trade statistics and P&L analysis
- **Trade History**: Individual trade records with entry/exit details and holding periods

### Stock Screening Architecture

**HalfSignal Screening Conditions**:
1. **SMA Hierarchy**: 5日SMA > 20日SMA > 60日SMA (ascending order requirement)
2. **Trend Confirmation**: 5-day SMA rising compared to previous day
3. **Candlestick Analysis**: Real body crossing 5SMA by ≥50% with body intersection validation

**Screening Workflow**:
1. Market index symbol retrieval (Nikkei 225/JPX400/Manual Input with parsing)
2. Judgment date validation with Japanese trading calendar
3. Batch condition checking across all symbols
4. Chart generation for passed symbols (60-day candlesticks + SMA + judgment day markers)
5. Results categorization (passed/failed/error) with visual analytics
6. Interactive accordion display with direct backtest and minkabu.jp integration

**Manual Symbol Input**: Supports comma/space/newline separated symbols with comment support (#)

### Database Schema

**symbols_meta table**: `symbol, table_name, company_name, first_date, last_date, last_updated`
**stock_{symbol} tables**: `date, open, high, low, close, volume, dividends, stock_splits`

### Key Development Patterns

**Modular Strategy Design**: Strategies are self-contained classes with standardized interfaces for backtesting and screening

**Database-First Approach**: All data operations check SQLite first, with yfinance as fallback for missing data

**Timeframe Abstraction**: Core logic handles daily data with automatic resampling and parameter scaling for weekly/monthly analysis

**Japanese Market Specialization**: Trading calendar, time zone handling, and symbol formats optimized for Japanese market operations

**Error Resilience**: Comprehensive error handling with graceful degradation and detailed error reporting for data acquisition failures

## Environment Setup

### Development Container
Node.js 20 + Python 3.11 with pre-installed trading analysis stack and Japanese font support (japanize-matplotlib)

### Python Configuration
- Interpreter: `/usr/bin/python3`
- Package manager: `pip3` (use --break-system-packages if needed in containerized environments)
- Database: `yf_history.db` (automatically created on first run)
- Chart Output: Matplotlib with Japanese font support for proper character rendering