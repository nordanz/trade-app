# 💼 Portfolio Management Feature Guide

## Overview

The portfolio management system allows you to:
- 📊 Track your stock holdings and shares
- 💰 Monitor profit/loss in real-time
- 📈 Get personalized trading recommendations
- 📜 View transaction history
- 🎯 Save and track trading signals
- 📊 Analyze your trading performance

## Features

### 1. Portfolio Tracking

#### Add Positions
1. Go to **"💼 My Portfolio"** tab
2. Click **"➕ Add New Position"**
3. Enter:
   - Ticker symbol (e.g., AAPL)
   - Number of shares
   - Purchase price
   - Purchase date
   - Notes (optional)
4. Click **"💾 Add to Portfolio"**

#### View Holdings
- See all your positions at a glance
- Real-time current prices
- Profit/loss for each position
- Total portfolio value
- Cost basis calculations

#### Sell Positions
1. Find the stock in your portfolio
2. Click **"📉 Sell"** button
3. Enter:
   - Number of shares to sell
   - Sell price
   - Notes (optional)
4. Click **"✅ Confirm Sell"**

### 2. Portfolio Summary

The dashboard shows:
- **Total Invested**: Your total cost basis
- **Current Value**: Current portfolio value
- **Total P/L**: Overall profit/loss ($ and %)
- **Positions**: Number of stocks you own

### 3. Position Details

For each stock, see:
- **Symbol**: Stock ticker
- **Shares**: Number of shares owned
- **Avg Price**: Your average purchase price
- **Current**: Current market price
- **Cost Basis**: Total amount invested
- **Value**: Current value of position
- **P/L**: Profit/loss ($ and %)

Color coding:
- 🟢 Green = Profitable position
- 🔴 Red = Losing position

### 4. Trading Recommendations

#### Portfolio-Specific Signals

In the **"🎯 Trading Signals"** tab:

1. **Toggle Portfolio View**
   - Check "💼 Show signals for my portfolio only"
   - See signals ONLY for stocks you own

2. **Smart Recommendations**

   **For BUY signals on owned stocks:**
   ```
   💡 Recommendation: Consider adding to your position
   - Current shares: 10 at avg $150.00
   - Suggested entry: $145.00
   - This would lower your avg if price < $150.00
   ```

   **For SELL signals on owned stocks:**
   ```
   💡 Recommendation: Consider selling your 10 shares
   - You bought at: $150.00
   - Current price: $165.00
   - Target sell: $170.00
   - Your P/L: +10.00%
   ```

3. **Portfolio Indicators**
   - Stocks in your portfolio show: **💼 IN PORTFOLIO**
   - Easy to identify your holdings vs watchlist

### 5. Transaction History

#### View Transactions
1. Click **"📜 History"** button next to any position
2. See all transactions for that stock:
   - Date
   - Type (BUY/SELL)
   - Shares
   - Price
   - Total value

#### Track All Transactions
- All buys and sells are automatically recorded
- Complete audit trail of your trading activity
- Export-ready data

### 6. Signal History

#### Save Trading Signals
1. In "Trading Signals" tab
2. Click **"💾 Save Signal"** on any recommendation
3. Signal saved with:
   - Date
   - Symbol
   - Signal type (BUY/SELL)
   - Entry/target/stop prices
   - Confidence level
   - Reasoning

#### Track Signal Performance
- View all saved signals
- See which ones are still open
- Track actual results vs predictions
- Calculate win rate

### 7. Performance Statistics

The dashboard shows:
- **Closed Trades**: Number of completed signals
- **Win Rate**: Percentage of profitable trades
- **Avg Return**: Average return per trade
- **Best Trade**: Your biggest winner

## Database Structure

### Tables Created

1. **portfolio**
   - Your current stock holdings
   - Tracks shares and average price

2. **transactions**
   - Complete history of all buys/sells
   - Audit trail for tax purposes

3. **signal_history**
   - Saved trading recommendations
   - Track performance over time

4. **watchlist**
   - Stocks you're monitoring
   - Separate from portfolio

### Data Storage

- Database file: `portfolio.db`
- Located in project root
- SQLite (no external database needed)
- Backed up with your files

## Use Cases

### 1. Track Investments
```
Example:
- Buy 10 AAPL @ $150
- Buy 5 more AAPL @ $160
- System calculates avg: $153.33
- Current price: $165
- Your P/L: +$116.70 (+7.14%)
```

### 2. Get Sell Signals
```
You own 10 TSLA @ $200
System generates: SELL signal
Recommendation shows:
- Your entry: $200
- Current: $220
- Target: $230
- Your P/L: +10%
→ Consider taking profits!
```

### 3. Get Buy Signals
```
You own 5 NVDA @ $500
System generates: BUY signal at $480
Recommendation shows:
- Adding 5 more shares at $480
- Would lower avg to $490
- Good for accumulation strategy
```

### 4. Review Performance
```
Signal History shows:
- 10 signals saved
- 7 were BUY, 3 were SELL
- Win rate: 70%
- Avg return: +8.5%
→ Strategy is working!
```

## Best Practices

### 1. Regular Updates
- Add positions as you buy
- Record sells immediately
- Keep notes on why you bought/sold

### 2. Save Important Signals
- Save signals you act on
- Close signals when you exit
- Track what works vs what doesn't

### 3. Review Performance
- Check win rate monthly
- Analyze best/worst trades
- Adjust strategy based on data

### 4. Use Recommendations
- Check "Portfolio Only" signals daily
- Focus on your holdings first
- Don't chase new positions

### 5. Risk Management
- Never go all-in on one stock
- Follow stop-loss recommendations
- Take profits at targets

## Tips & Tricks

### Averaging Down
When you add to an existing position:
- System automatically calculates new avg price
- Lower avg = better cost basis
- Only average down on quality stocks

### Position Sizing
- Keep positions balanced
- No single stock > 10% of portfolio
- Diversify across sectors

### Signal Confidence
- Only act on signals > 70% confidence
- Higher confidence = better odds
- Still do your own research

### Transaction Notes
Add notes like:
- "Following BUY signal from 2026-02-01"
- "Taking profits at resistance"
- "Stop loss triggered"
- "Averaging down on dip"

## Troubleshooting

### Can't Add Position
- Check ticker symbol is correct
- Make sure price > 0
- Ensure shares > 0

### Wrong Average Price
- Database calculates automatically
- Check transaction history
- Each buy adjusts the average

### Missing Transactions
- Only buys through dashboard are saved
- Manually add existing positions
- Use correct purchase date

### Signal Not Saving
- Check internet connection
- Ensure database is writable
- Check for error messages

## Data Privacy

- All data stored locally
- No cloud sync (your data stays private)
- SQLite database file: `portfolio.db`
- Backup recommended

## Backup & Export

### Backup Database
```bash
cp portfolio.db portfolio_backup_$(date +%Y%m%d).db
```

### View Data Directly
```bash
sqlite3 portfolio.db
.tables
SELECT * FROM portfolio;
.exit
```

### Export to CSV
Use Python script or SQLite command:
```bash
sqlite3 portfolio.db
.mode csv
.output portfolio_export.csv
SELECT * FROM portfolio;
.output transactions_export.csv
SELECT * FROM transactions;
.exit
```

## Example Workflow

### Daily Routine
1. Open dashboard
2. Check "My Portfolio" tab
3. Review P/L for each position
4. Go to "Trading Signals" tab
5. Enable "Portfolio Only" view
6. Review recommendations for holdings
7. Save signals you want to track
8. Execute trades in your broker
9. Record trades in dashboard

### Weekly Review
1. Check performance statistics
2. Review transaction history
3. Analyze signal history
4. Calculate actual vs expected returns
5. Adjust strategy as needed

### Monthly Analysis
1. Review closed signals
2. Calculate win rate
3. Identify best performers
4. Learn from losing trades
5. Update risk parameters

## Summary

The portfolio management system gives you:
- ✅ Complete tracking of holdings
- ✅ Real-time P/L calculations
- ✅ Personalized trading recommendations
- ✅ Transaction history
- ✅ Signal tracking
- ✅ Performance analytics
- ✅ All data stored locally

**Remember:** This is a tracking and analysis tool. Always:
- Do your own research
- Follow your risk tolerance
- Never invest more than you can lose
- Consult a financial advisor for major decisions

---

**Happy Trading! 💼📈**
