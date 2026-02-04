# 📈 Stock Market Dashboard with AI-Powered Swing Trading

A comprehensive Python dashboard that provides live stock market data, AI-powered news analysis using Google's Gemini API, and intelligent swing trading recommendations.

## 🌟 Features

- **Live Market Data**: Real-time stock prices, volume, and key metrics
- **Portfolio Management**: Track your holdings, shares, and P/L in real-time
- **AI News Analysis**: Gemini-powered sentiment analysis and news summaries
- **Swing Trading Signals**: Technical indicator-based buy/sell recommendations
- **Personalized Recommendations**: Get signals specific to your portfolio
- **Interactive Charts**: Beautiful visualizations with Plotly
- **Multi-Stock Support**: Track multiple tickers simultaneously
- **Transaction History**: Complete audit trail of all trades
- **Performance Analytics**: Win rate, avg returns, and more
- **Auto-Refresh**: Real-time updates of market data

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Gemini API key (get one at https://makersuite.google.com/app/apikey)

### Installation

1. Clone the repository:
```bash
cd /Users/danial/workspaces/esignal
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running the Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

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
├── services/         # Core business logic services
├── models/           # Data models
├── utils/            # Helper functions and indicators
├── dashboard/        # Streamlit UI
└── tests/           # Unit tests
```

## 🔧 Configuration

Edit `.env` file to customize:

- `GEMINI_API_KEY`: Your Gemini API key (required)
- `DEFAULT_TICKERS`: Comma-separated list of default stock symbols
- `REFRESH_INTERVAL`: Dashboard refresh interval in seconds
- `RSI_OVERSOLD/OVERBOUGHT`: RSI threshold values

## 📈 Trading Strategy

The dashboard uses multiple technical indicators for swing trading:

- **RSI**: Identifies overbought/oversold conditions
- **MACD**: Detects trend changes and momentum
- **Bollinger Bands**: Measures volatility and price levels
- **Moving Averages**: Shows trend direction and support/resistance
- **Volume Analysis**: Confirms price movements

### Signal Generation

- **BUY**: RSI < 30, MACD bullish crossover, volume spike
- **SELL**: RSI > 70, MACD bearish crossover, resistance hit
- **HOLD**: Mixed signals or neutral conditions

## ⚠️ Disclaimer

**This tool is for educational and informational purposes only.**

- NOT financial advice
- Always do your own research
- Past performance ≠ future results
- Trading involves significant risk
- Consult a financial advisor before investing

## 🛠️ Technologies

- **Streamlit**: Web dashboard framework
- **yfinance**: Live stock market data
- **Gemini AI**: News analysis and insights
- **pandas-ta**: Technical indicators
- **Plotly**: Interactive charts
- **pandas/numpy**: Data processing

## 📝 License

MIT License - feel free to use and modify

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For questions or issues, please open a GitHub issue.

---

**Happy Trading! 🚀📊**
