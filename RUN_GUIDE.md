# 🎯 HOW TO RUN THE DASHBOARD

## ✅ Setup Complete! Here's How to Start:

### Option 1: Using the Run Script (Easiest)
```bash
cd /Users/danial/workspaces/esignal
./run.sh
```

### Option 2: Manual Steps
```bash
# 1. Navigate to project
cd /Users/danial/workspaces/esignal

# 2. Activate virtual environment
source venv/bin/activate

# 3. Create .env file (first time only)
cp .env.example .env

# 4. Edit .env and add your Gemini API key
nano .env
# Add: GEMINI_API_KEY=your_actual_key_here
# Save: Ctrl+X, Y, Enter

# 5. Run the dashboard
streamlit run dashboard/app.py
```

## 🔑 Getting Your Gemini API Key

1. **Visit:** https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click** "Create API Key"
4. **Copy** the key
5. **Paste** into `.env` file:
   ```
   GEMINI_API_KEY=your_copied_key_here
   ```

## 📱 What Happens When You Run It

1. Terminal shows: `You can now view your Streamlit app in your browser.`
2. Browser automatically opens to: `http://localhost:8501`
3. Dashboard loads with default stocks (AAPL, GOOGL, MSFT, TSLA, NVDA)

## 🎨 Using the Dashboard

### Sidebar Controls
- **Market Status** - Shows if market is open/closed
- **Add Ticker** - Type symbol (e.g., "TSLA") and click "Add"
- **Watchlist** - View and remove stocks with ❌ button
- **Auto-refresh** - Toggle automatic updates
- **Refresh Now** - Manual refresh button

### Tab 1: Market Overview 📊
- Real-time stock prices
- Price changes (green ↑ / red ↓)
- Volume and market cap
- Moving averages

### Tab 2: AI News & Analysis 📰
- Market summary from Gemini AI
- Individual stock sentiment analysis
- News headlines and summaries
- Sentiment scores (😊 😟 😐)

### Tab 3: Trading Signals 🎯
- **Top Opportunities** - Best buy signals
- Each signal shows:
  - 🟢 BUY / 🔴 SELL / 🟡 HOLD
  - Confidence percentage
  - Entry, target, and stop-loss prices
  - Risk/reward ratio
  - Detailed reasoning
  - Technical indicators

### Tab 4: Detailed Charts 📈
- Interactive candlestick charts
- Volume bars
- Moving average lines
- 3-month historical data
- Technical indicators summary

## 🛑 How to Stop the Dashboard

Press `Ctrl + C` in the terminal

## 🔧 Troubleshooting

### Issue: "streamlit: command not found"
**Solution:**
```bash
source venv/bin/activate
pip install streamlit
```

### Issue: "ModuleNotFoundError: No module named 'services'"
**Solution:** Make sure you're running from the project root:
```bash
cd /Users/danial/workspaces/esignal
streamlit run dashboard/app.py
```

### Issue: "Gemini AI not available"
**Solution:** 
1. Check `.env` file exists: `ls -la .env`
2. Check it has your API key: `cat .env`
3. Make sure key starts with `GEMINI_API_KEY=`

### Issue: "No data for stock symbol"
**Solution:**
- Check ticker symbol spelling (use uppercase)
- Try popular symbols: AAPL, GOOGL, MSFT, TSLA
- Check if market is open (9:30 AM - 4:00 PM ET)

### Issue: Dashboard looks broken
**Solution:**
- Refresh browser (Cmd+R or Ctrl+R)
- Clear browser cache
- Try different browser (Chrome recommended)

## 📊 Popular Stock Symbols to Try

### Tech
```
AAPL    Apple
GOOGL   Google
MSFT    Microsoft
AMZN    Amazon
META    Meta (Facebook)
TSLA    Tesla
NVDA    NVIDIA
```

### Finance
```
JPM     JPMorgan Chase
BAC     Bank of America
GS      Goldman Sachs
```

### Consumer
```
WMT     Walmart
DIS     Disney
NKE     Nike
SBUX    Starbucks
```

### ETFs
```
SPY     S&P 500
QQQ     NASDAQ 100
DIA     Dow Jones
```

## 🎯 Quick Test Run

1. **Start the dashboard:**
   ```bash
   cd /Users/danial/workspaces/esignal
   ./run.sh
   ```

2. **Wait for browser to open** (or go to http://localhost:8501)

3. **Add a stock:**
   - Type "TSLA" in sidebar
   - Click "➕ Add to Watchlist"

4. **Explore tabs:**
   - View live price in Market Overview
   - Check AI analysis in News tab
   - Look for trading signals in Signals tab
   - View charts in Charts tab

5. **Stop when done:**
   - Press `Ctrl + C` in terminal

## 📚 Next Steps

### 1. Configure Your Settings
Edit `.env` file to customize:
```bash
nano .env
```

Example customizations:
```
# Your favorite stocks
DEFAULT_TICKERS=AAPL,TSLA,NVDA,AMD,GOOGL

# Refresh every 30 seconds
REFRESH_INTERVAL=30

# More conservative RSI thresholds
RSI_OVERSOLD=25
RSI_OVERBOUGHT=75
```

### 2. Learn the Indicators
- **RSI < 30** = Oversold (potential buy)
- **RSI > 70** = Overbought (potential sell)
- **MACD Crossover** = Trend change
- **Golden Cross** = Bullish signal (50-day MA crosses above 200-day MA)
- **Death Cross** = Bearish signal (50-day MA crosses below 200-day MA)

### 3. Practice Paper Trading
- Don't invest real money immediately
- Track signals and see how they perform
- Learn from AI reasoning
- Understand risk/reward ratios

### 4. Stay Informed
- Read the AI summaries
- Check multiple indicators
- Never rely on just one signal
- Always do your own research

## ⚠️ Important Reminders

1. **Not Financial Advice** - This is educational only
2. **Market Risk** - You can lose money trading
3. **Do Research** - Always verify information
4. **Start Small** - Never risk more than you can afford to lose
5. **Practice First** - Paper trade before using real money

## 🎉 You're All Set!

The dashboard is fully functional and ready to use. Enjoy exploring the markets!

### Quick Command Reference
```bash
# Run dashboard
./run.sh

# Or manually
source venv/bin/activate
streamlit run dashboard/app.py

# Run tests
python tests/test_services.py

# Stop dashboard
Ctrl + C
```

---

**Need Help?**
- Check README.md for full documentation
- Review QUICKSTART.md for detailed setup
- See DESIGN.md for architecture details

**Happy Trading! 📈💰**
