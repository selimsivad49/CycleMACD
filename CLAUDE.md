# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CycleMACD is a sophisticated Japanese stock trading strategy backtesting system that implements MACD histogram-based trading signals with multi-timeframe analysis, stock screening capabilities, and comprehensive data persistence. The system features a Flask web application interface, SQLite-based data management, and supports daily, weekly, and monthly backtesting with detailed trade history tracking, Long/Short performance analysis, and advanced screening conditions.

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

### Dependencies
```bash
pip install -r requirements.txt
```

Core dependencies: Flask 3.0+, yfinance 0.2+, pandas 2.0+, matplotlib 3.5+, japanize-matplotlib, numpy 1.20+, seaborn 0.11+

## High-Level Architecture

### Core Module Structure

**data_manager.py** - SQLite-based data persistence layer:
- **StockDataManager**: Manages `yf_history.db` with symbol-specific tables
- **Incremental Updates**: Fetches only missing data ranges (1990-01-01 to yesterday)
- **Symbol Sanitization**: Handles special characters (e.g., "NIY=F" → "stock_NIY_F")
- **Company Name Resolution**: Automatic fetching and storage of company metadata

**strategies.py** - Multi-timeframe backtesting engine:
- **MACDBacktester**: Core backtesting with timeframes D/W/M
- **Adaptive Parameters**: Timeframe-specific MACD scaling (Daily: 20x, Weekly: 4x, Monthly: 1x)
- **2-Month Lag Logic**: Realistic signal generation (compares i-2 vs i-1 for i-period entry)
- **Long/Short Analytics**: Separate performance tracking by trade direction

**screening.py** - Advanced stock screening system:
- **HalfSignal**: SMA-based screening with complex candlestick analysis
- **ScreeningEngine**: Batch processing across market indices (Nikkei 225, JPX400)
- **Judgment Date Logic**: Japanese trading hours and calendar-aware validation

**utils.py** - Utility functions and Japanese market support:
- **Trading Day Calculations**: Japanese time zone and market calendar logic
- **Performance Metrics**: Sharpe ratio, volatility, drawdown calculations
- **Default Symbol Management**: Pre-configured Japanese stock lists

**app.py** - Flask web application with comprehensive routing:
- **Multi-interface Support**: Main UI, legacy interface, screening, backtesting
- **Dynamic Symbol Management**: Add/validate symbols with company name resolution
- **Chart Generation**: Matplotlib-based visualization with trade statistics

### Data Flow and Architecture Patterns

**Data Acquisition Pipeline**:
1. Database check for existing data ranges in SQLite
2. Gap analysis to identify missing periods
3. yfinance API calls for missing data only
4. Incremental storage with metadata updates
5. Symbol validation and company name resolution

**Multi-Timeframe Processing**:
1. Daily data acquisition and storage
2. Timeframe-specific resampling (D→W→M)
3. Adaptive MACD parameter scaling by timeframe
4. Signal generation with 2-month lag for realism
5. Performance calculation with appropriate annualization factors

**Web Application Request Flow**:
1. Route handling with parameter validation
2. Database-first data retrieval
3. Strategy execution (backtesting or screening)
4. Chart generation and statistical analysis
5. Template rendering with comprehensive results

### Flask Application Architecture

**Route Structure**:
- `GET /` - Main parameter selection interface with symbol management
- `GET /old` - Legacy multi-symbol analysis interface  
- `POST /add_symbol` - Dynamic symbol addition with yfinance validation
- `POST /analyze` - Multi-symbol backtesting execution
- `GET /chart/<symbol>` - Individual chart generation with trade statistics
- `GET /backtest` - Single-symbol detailed backtest results
- `GET /screening` - Stock screening execution and results display
- `GET /health` - Application health check

**Template Architecture**:
- **parameter_selection.html**: Main interface with symbol selection, timeframe options, screening controls
- **backtest_result.html**: Comprehensive single-symbol results with charts and statistics
- **screening_result.html**: Advanced screening results with accordion displays and backtest links
- **index.html**: Legacy multi-symbol analysis interface

### Japanese Market Integration

**Market Indices Support**:
- **Nikkei 225**: 225+ carefully curated symbols with .T suffix
- **JPX400**: Extended symbol list including JPX400 additional constituents
- **Symbol Validation**: yfinance compatibility checking before database storage

**Trading Calendar Logic**:
- **Japanese Time Zone**: JST-aware date calculations
- **Market Hours**: 0-9 JST defaults to previous day for judgment dates
- **Weekend Handling**: Saturday/Sunday defaults to previous Friday
- **Holiday Awareness**: Integration with Japanese trading calendar

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
1. Market index symbol retrieval (Nikkei 225/JPX400)
2. Judgment date validation with Japanese trading calendar
3. Batch condition checking across all symbols
4. Results categorization (passed/failed/error) with detailed analytics
5. Interactive results display with direct backtest integration

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