# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CycleMACD is a comprehensive Japanese stock trading strategy backtesting system that implements MACD histogram-based trading signals with multi-timeframe analysis. The system features a Flask web application interface, SQLite-based data persistence, and supports daily, weekly, and monthly backtesting with detailed trade history tracking and Long/Short performance analysis.

## Dependencies and Setup

Install required packages:
```bash
pip install -r requirements.txt
```

Core dependencies:
- Flask 3.0+ (web framework)
- yfinance 0.2+ (stock data retrieval) 
- pandas 2.0+ (data manipulation)
- matplotlib 3.5+ (plotting)
- japanize-matplotlib (Japanese font support)
- sqlite3 (built-in, database storage)

## Running the System

### Web Application
```bash
python3 app.py
# or
python3 run_webapp.py
```
Access at `http://localhost:5000`

### Command Line Analysis
```bash
python3 cyclemacd.py
```

### Testing
```bash
python3 simple_test.py        # Basic functionality tests
python3 test_cyclemacd.py     # Unit tests
```

## Architecture

### Core Components

**StockDataManager Class** - SQLite-based data persistence:
- Manages historical data storage in `yf_history.db`
- Creates symbol-specific tables with sanitized names (e.g., "NIY=F" → "stock_NIY_F")
- Implements incremental data updates (fetches only missing data ranges)
- Handles data from 1990-01-01 to yesterday for comprehensive historical coverage

**MACDBacktester Class** - Multi-timeframe backtesting engine:
- `__init__(symbol, start_date, end_date, timeframe='M')` - Supports 'D'(daily), 'W'(weekly), 'M'(monthly)
- `fetch_data()` - Database-first data retrieval with yfinance fallback
- `resample_data()` - Converts daily data to weekly/monthly as needed
- `calculate_macd()` - Timeframe-adaptive MACD parameters (daily uses 20x monthly params)
- `generate_signals()` - 2-month lag trading logic (compares i-2 vs i-1 histogram for i-period entry)
- `get_trade_statistics()` - Comprehensive Long/Short trade analysis
- `get_trade_history()` - Detailed trade-by-trade records with P&L tracking

### Trading Strategy Logic

**Signal Generation**:
- Buy signal: MACD histogram crosses from ≤0 to >0 (comparing 2 months ago vs 1 month ago)
- Sell signal: MACD histogram crosses from >0 to ≤0 (comparing 2 months ago vs 1 month ago)
- Entry timing: Uses 2-month lag to ensure realistic trading (data available before entry)

**Trade Tracking**:
- Records entry/exit dates, prices, direction (LONG/SHORT)
- Calculates P&L, return percentages, holding periods
- Separate statistics for Long vs Short positions
- Tracks win rates, P/L ratios, max drawdowns by direction

### Database Schema

**symbols_meta table**: symbol, table_name, first_date, last_date, last_updated
**stock_{symbol} tables**: date, open, high, low, close, volume, dividends, stock_splits

### Web Application Structure

**Flask Routes**:
- `GET /` - Main interface with timeframe selection
- `POST /analyze` - Multi-symbol backtesting with timeframe parameter
- `GET /chart/<symbol>` - Individual chart generation with trade statistics
- `GET /health` - Health check endpoint

**Frontend Features**:
- Bootstrap 5 responsive design
- Timeframe selector (daily/weekly/monthly)
- Long/Short statistics display in results table and chart modals
- Interactive chart generation with trade statistics breakdown

### Data Flow

1. **Data Acquisition**: Check SQLite DB → fetch missing data from yfinance → store incrementally
2. **Data Processing**: Daily data → resample to target timeframe → calculate timeframe-adjusted MACD
3. **Signal Generation**: Apply 2-month lag logic → generate buy/sell signals
4. **Trade Execution**: Track position changes → record detailed trade history
5. **Analysis**: Calculate overall + Long/Short specific performance metrics
6. **Visualization**: Generate charts with signals + comprehensive trade statistics

### Symbol Support

Handles multiple ticker formats through sanitization:
- Japanese stocks: "7203.T", "6758.T" 
- Futures: "NIY=F", "ES=F"
- International: Various exchanges with special character handling

### Timeframe Considerations

**MACD Parameters**:
- Daily: fast=240, slow=520, signal=180 (20x monthly)
- Weekly: fast=48, slow=104, signal=36 (4x monthly)  
- Monthly: fast=12, slow=26, signal=9 (standard)

**Annualization Factors**:
- Daily: 252 trading days/year
- Weekly: 52 weeks/year
- Monthly: 12 months/year

## Development Container Setup

Node.js 20 + Python 3.11 devcontainer with pre-installed trading analysis stack and Japanese font support.

### Python Environment
- Interpreter: `/usr/bin/python3`
- Package manager: `pip3` (install with --break-system-packages if needed)
- Database: `yf_history.db` (auto-created)

## Performance Metrics

**Overall Statistics**: Total returns, win rate, trade count, Sharpe ratio, max drawdown, volatility
**Long/Short Breakdown**: Separate analysis for each trade direction including P/L ratios and direction-specific drawdowns
**Trade History**: Individual trade records with entry/exit details, holding periods, and profitability analysis