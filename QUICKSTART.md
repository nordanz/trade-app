# 🚀 Quick Start Guide

## Setup (5 minutes)

### 1. Run the setup script
```bash
cd /Users/danial/workspaces/esignal
./setup.sh
```

### 2. Get your Gemini API key
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key (it's free!)
3. Copy the key

### 3. Configure your environment
```bash
# Edit the .env file
nano .env

# Add your API key:
GEMINI_API_KEY=your_actual_api_key_here

# Save and exit (Ctrl+X, then Y, then Enter)
```

### 4. Run the dashboard
```bash
# Activate virtual environment
source venv/bin/activate

# Start the dashboard
python dashboard/app.py
```

The dashboard will open in your browser at `http://127.0.0.1:8050`

## Using the Dashboard

### Adding Stocks
1. Use the sidebar to add stock tickers (e.g., AAPL, GOOGL, TSLA)
2. Click "➕ Add to Watchlist"
3. View live data instantly!

### Features

#### 📊 Market Overview
- Live stock prices and metrics
- Volume and market cap
- Moving averages (20, 50, 200-day)
- Price change percentages

#### 📰 AI News & Analysis
- AI-generated market summaries
- Stock-specific sentiment analysis
- News relevance scores
- Positive/Negative/Neutral indicators

#### 🎯 Trading Signals
- Swing trading recommendations
- Buy/Sell/Hold signals
- Entry, target, and stop-loss prices
- Confidence levels (0-100%)
- Risk/reward ratios
- Technical indicator breakdown

#### 📈 Detailed Charts
- Interactive candlestick charts
- Volume charts
- Moving average overlays
- 3-month historical data

### Auto-Refresh
- Enable/disable in sidebar
- Updates every 60 seconds by default
- Manual refresh button available

## Testing

Run the test suite to verify everything works:
```bash
source venv/bin/activate
python tests/test_services.py
```

## Popular Stock Tickers

### Tech Giants
- AAPL (Apple)
- GOOGL (Google)
- MSFT (Microsoft)
- AMZN (Amazon)
- META (Meta/Facebook)
- NVDA (NVIDIA)
- TSLA (Tesla)

### Financial
- JPM (JPMorgan)
- GS (Goldman Sachs)
- BAC (Bank of America)

### Consumer
- WMT (Walmart)
- DIS (Disney)
- NKE (Nike)
- SBUX (Starbucks)

### ETFs
- SPY (S&P 500)
- QQQ (NASDAQ 100)
- DIA (Dow Jones)

## Troubleshooting

### "Module not found" error
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Gemini API not available"
- Check that GEMINI_API_KEY is set in .env
- Verify your API key is valid
- Check for quota limits

### "No data available for symbol"
- Verify the ticker symbol is correct
- Check market hours (US markets: 9:30 AM - 4:00 PM ET)
- Some tickers may not be available on Yahoo Finance

### Charts not loading
- Clear browser cache
- Check internet connection
- Try refreshing the page

## Tips for Swing Trading

1. **Entry Points**
   - Look for RSI < 30 (oversold)
   - Wait for MACD bullish crossover
   - Check volume confirmation

2. **Exit Strategy**
   - Set stop loss at 3-5% below entry
   - Target 5-10% profit
   - Use trailing stops to protect gains

3. **Risk Management**
   - Never risk more than 2% per trade
   - Diversify across sectors
   - Don't chase momentum

4. **Best Practices**
   - Follow the trend
   - Wait for confirmation
   - Be patient with entries
   - Let winners run, cut losers quickly

## Customization

### Change default tickers
Edit `.env` file:
```
DEFAULT_TICKERS=AAPL,GOOGL,MSFT,TSLA,NVDA
```

### Adjust refresh interval
Edit `.env` file:
```
REFRESH_INTERVAL=30  # seconds
```

### Modify RSI thresholds
Edit `.env` file:
```
RSI_OVERSOLD=25
RSI_OVERBOUGHT=75
```

## Support

- Check the README.md for detailed documentation
- Review DESIGN.md for architecture details
- Open GitHub issues for bugs or feature requests

---

**Remember:** This is for educational purposes only. Always do your own research before investing!
