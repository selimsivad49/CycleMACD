# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CycleMACD is a Japanese stock trading strategy backtesting system that implements MACD histogram-based trading signals for monthly stock data analysis. The system fetches Japanese stock data using yfinance and performs comprehensive backtesting with performance metrics.

## Dependencies and Setup

The required Python packages are pre-installed in the devcontainer:
- yfinance (stock data retrieval)
- pandas (data manipulation)
- numpy (numerical computing)
- matplotlib (plotting)
- seaborn (statistical visualization)
- jupyter (notebook environment)

If packages are missing, install manually:
```bash
pip3 install yfinance pandas numpy matplotlib seaborn jupyter
```

## Running the System

### Main Analysis
```bash
python3 cyclemacd.py
```
This executes the full analysis pipeline:
- Analyzes 10 predefined Japanese stocks (Toyota, Sony, SoftBank, etc.)
- Runs MACD histogram-based backtests for 2020-2024 period
- Generates performance summaries and visualizations

### Testing
```bash
python3 simple_test.py
```
Runs basic functionality tests using standard library only (no external dependencies required).

## Architecture

### Core Components

**MACDBacktester Class** - Main backtesting engine with methods:
- `fetch_data()` - Retrieves Japanese stock data via yfinance (tries both .T and .TO suffixes)
- `calculate_macd()` - Computes MACD, signal line, and histogram using EMA (12, 26, 9)
- `generate_signals()` - Creates buy/sell signals based on histogram zero-crossing
- `backtest()` - Executes full backtesting pipeline
- `calculate_stats()` - Computes performance metrics (returns, Sharpe ratio, max drawdown, win rate)
- `plot_results()` - Generates 3-panel visualization (price + signals, MACD histogram, cumulative returns)

**Trading Strategy Logic**:
- Buy signal: MACD histogram crosses above zero
- Sell signal: MACD histogram crosses below zero
- Position holding: Maintains position while histogram stays on same side of zero

**get_japanese_stock_data()** - Handles Japanese stock data retrieval with error handling for different ticker formats.

**analyze_multiple_stocks()** - Batch processing function for multiple symbols with results aggregation.

### Data Flow
1. Stock data fetched monthly from yfinance
2. MACD indicators calculated (EMA12 - EMA26, signal line, histogram)
3. Trading signals generated from histogram zero-crossings
4. Returns calculated and performance metrics computed
5. Results visualized and summarized

### Japanese Stock Symbol Format
The system handles Japanese stock symbols by trying multiple formats:
- `{symbol}.T` (Tokyo Stock Exchange)
- `{symbol}.TO` (alternative format)

Default test symbols include major Japanese companies like Toyota (7203), Sony (6758), etc.

## Development Container Setup

The project uses a Node.js-based devcontainer that has been extended for Python development:

### Container Features:
- **Base**: Node.js 20 with Python 3.11
- **Python packages**: Pre-installed trading analysis stack
- **VS Code extensions**: Python, Jupyter, debugging support
- **Environment**: Configured for both Node.js and Python development

### Container Rebuild:
After modifying `.devcontainer/` files, rebuild the container:
1. Command Palette: "Dev Containers: Rebuild Container"
2. Or restart the codespace/devcontainer

### Python Environment:
- **Interpreter**: `/usr/bin/python3`
- **Package manager**: `pip3`
- **Working directory**: `/workspace`

## Performance Metrics
- Total returns (strategy vs buy-and-hold)
- Win rate and trade count
- Maximum drawdown
- Sharpe ratio (annualized)
- Volatility (annualized)