# 📈 Stock Market Dashboard with AI-Powered Trading

A comprehensive Python dashboard that provides live stock market data, AI-powered news analysis using Google's Gemini API, and intelligent trading recommendations across **6 built-in strategies**. Built with **Dash (Plotly)** for a professional, high-performance analytical experience.

## 🌟 Features

- **Live Market Data**: Real-time stock prices, volume, and key metrics via `yfinance`
- **Dash-Powered UI**: Modern, responsive, and interactive dashboard using `Dash Bootstrap Components`
- **Portfolio Management**: Track your holdings, shares, and P/L in real-time
- **AI News Analysis**: Gemini-powered sentiment analysis and news summaries
- **6 Trading Strategies**: 3 day trading + 3 swing trading strategies
- **Integrated Backtesting**: Professional backtesting engine available inline on strategy pages
- **News Impact Controller**: Tune how news sentiment affects signals
- **Interactive Graphs**: High-performance Plotly visualizations with full interactivity
- **Beginner's Guide**: In-app learning page for new traders
- **Multi-Stock Scanner**: Scan watchlists for opportunities
- **Audit Trail**: Complete history of trades and performance tracking
- **Strategy Comparison**: Compare multiple strategy performances side-by-side

## 📊 Trading Strategies

### Day Trading (Intraday — positions closed by EOD)

| Strategy | Key Idea | Entry Signal | Best For |
|----------|----------|-------------|----------|
| **VWAP** | Trade around Volume Weighted Average Price | Price crosses VWAP with volume confirmation | Liquid large-caps with intraday volatility |
| **Opening Range Breakout (ORB)** | Trade the break of the first 30-min range | Price breaks above/below opening range with volume | Stocks with strong morning momentum |
| **Momentum / Gap-and-Go** | Ride gap openings with follow-through | Gap >2% + RSI/MACD momentum confirmation | Earnings plays, catalyst-driven gaps |

### Swing Trading (Multi-day — hold 3–7+ days)

| Strategy | Key Idea | Entry Signal | Best For |
|----------|----------|-------------|----------|
| **Mean Reversion (Bollinger Bands)** | Buy low / sell high within a range | Price at BB extreme + RSI oversold/overbought | Range-bound stocks with clear support/resistance |
| **Fibonacci Retracement** | Enter on pullbacks within a trend | Price retraces to 38.2%, 50%, or 61.8% Fib level | Trending stocks with clear swing highs/lows |
| **Breakout Trading** | Enter on confirmed breakouts | Price breaks support/resistance + volume spike + ADX >25 | Consolidating stocks before big moves |

### Signal Generation Pipeline

Every signal goes through three layers:

1. **Core Technical Indicators** — RSI, MACD, Bollinger Bands, trend detection
2. **Strategy-Specific Logic** — VWAP proximity, Fib levels, breakout confirmation, etc.
3. **News Sentiment Overlay** — Gemini AI sentiment score boosts or dampens signals

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Gemini API key (get one at https://makersuite.google.com/app/apikey)

### Installation

**Option 1: Quick Setup (Recommended)**

1. Clone the repository:
```bash
git clone <repository-url>
cd esignal
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

**Option 2: Manual Installation**

1. Clone the repository:
```bash
git clone <repository-url>
cd esignal
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or: venv\Scripts\activate  # On Windows
```

3. Install the package:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the Dashboard

**Using the CLI command (after installation):**
```bash
esignal
```

**Or manually with Python/Dash:**
```bash
python dashboard/app.py
```

The dashboard will open in your browser at `http://127.0.0.1:8050`

## 📊 Usage

1. **Add Stocks**: Enter ticker symbols (e.g., AAPL, GOOGL) in the sidebar
2. **Track Portfolio**: Add your holdings in the "My Portfolio" tab
3. **View Live Data**: See real-time prices, charts, and technical indicators
4. **Read AI Analysis**: Get Gemini-powered news summaries and sentiment
5. **Trading Signals**: Review swing trading recommendations
6. **Portfolio Signals**: Enable "Portfolio Only" to see signals for stocks you own
7. **Save Signals**: Track signal performance over time
8. **Auto-Refresh**: Dashboard updates automatically every 60 seconds

## 🏗️ Architecture

```
esignal/
├── config/           # Configuration and settings
├── services/         # Core business logic
│   ├── market_data_service.py        # Live stock data (yfinance)
│   ├── gemini_service.py             # AI news analysis (Gemini)
│   ├── trading_strategy_service.py   # Signal generation engine
│   ├── strategies.py                 # Strategy registry
│   ├── day_trading_strategies.py     # VWAP, ORB, Momentum
│   ├── swing_trading_strategies.py   # Mean Reversion, Fib, Breakout
│   ├── backtest_service.py           # Backtesting engine
│   └── portfolio_service.py          # Portfolio DB (SQLite)
├── models/           # Data models (StockData, TradingSignal)
├── utils/            # Technical indicators & helpers
├── dashboard/        # Dash UI
│   ├── app.py                        # Main app with multi-page routing
│   └── components/                   # One component per page (Day/Swing/Portfolio/etc.)
└── tests/            # Unit tests
```

## 🔧 Configuration

Edit `.env` file to customize:

- `GEMINI_API_KEY`: Your Gemini API key (required)
- `DEFAULT_TICKERS`: Comma-separated list of default stock symbols
- `REFRESH_INTERVAL`: Dashboard refresh interval in seconds
- `RSI_OVERSOLD/OVERBOUGHT`: RSI threshold values

## 📈 How Signals Work

Each signal is scored on a point system combining multiple factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| RSI | 2 pts | Oversold (<30) → BUY, Overbought (>70) → SELL |
| MACD | 1 pt | Bullish/bearish crossover |
| Strategy-specific | 2 pts | VWAP distance, Fib level, breakout, etc. |
| Trend (swing only) | 1 pt | Daily uptrend/downtrend context |
| News sentiment | 1-4 pts | AI-scored sentiment with relevance weighting |

**Confidence** = ratio of buy vs sell points, capped at 98%.

### Risk Management

- **Day trades**: Stop loss at 1× ATR, target at 1.5× ATR
- **Swing trades**: Stop loss at 1.5× ATR, target at 3× ATR
- **Minimum confidence**: 60% (configurable)
- **Scanner filter**: Only surfaces signals above your threshold

## ⚠️ Disclaimer

**This tool is for educational and informational purposes only.**

- NOT financial advice
- Always do your own research
- Past performance ≠ future results
- Trading involves significant risk
- Consult a financial advisor before investing

## 🛠️ Technologies

- **Dash / Plotly**: Modern analytical web dashboard framework
- **Dash Bootstrap Components (DBC)**: Professional UI/UX layout
- **yfinance**: Live stock market data
- **Gemini AI**: News analysis and insights
- **Backtesting.py**: High-performance strategy simulation
- **pandas-ta**: Technical indicators
- **pandas/numpy**: Data processing

## 📝 License

MIT License - feel free to use and modify

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For questions or issues, please open a GitHub issue.

---

**Happy Trading! 🚀📊**
