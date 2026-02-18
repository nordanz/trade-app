# 📚 Beginner's Guide to Trading

Welcome! This guide will help you understand the basics of stock trading and how to use the strategies in this dashboard.

---

## 1. What Is Stock Trading?

Stock trading means buying and selling shares of a company. You profit when you **buy low and sell high** (or short-sell high and cover low).

There are two main styles this dashboard supports:

| Style | Holding Period | Goal | Risk Level |
|-------|---------------|------|------------|
| **Day Trading** | Minutes to hours (closed by end of day) | Small, frequent gains (0.5–3%) | Higher — fast decisions required |
| **Swing Trading** | Days to weeks | Larger moves (3–10%) | Moderate — more time to decide |

> **Which should I start with?** If you're new, start with **swing trading**. It's slower, less stressful, and gives you time to think.

---

## 2. Key Concepts You Need to Know

### Price Action
- **Open** — the price when the market opens
- **Close** — the price when the market closes
- **High / Low** — the highest and lowest price during the day
- **Volume** — how many shares were traded (high volume = more interest)

### Support & Resistance
- **Support** — a price level where the stock tends to stop falling (buyers step in)
- **Resistance** — a price level where the stock tends to stop rising (sellers step in)
- When price **breaks through** resistance with high volume, it often keeps going up (**breakout**)

### Trends
- **Uptrend** — price is making higher highs and higher lows 📈
- **Downtrend** — price is making lower highs and lower lows 📉
- **Sideways** — price is bouncing between support and resistance ↔️

> **Rule of thumb:** Trade *with* the trend, not against it.

---

## 3. Technical Indicators Explained

These are math-based tools that help you decide when to buy or sell. The dashboard calculates them for you automatically.

### RSI (Relative Strength Index)
- Scale: 0–100
- **Below 30** = oversold → stock may be due for a bounce (potential BUY)
- **Above 70** = overbought → stock may be due for a pullback (potential SELL)
- Think of it like a rubber band — the more stretched, the more likely it snaps back

### MACD (Moving Average Convergence Divergence)
- Shows momentum and trend direction
- **MACD line crosses above signal line** → bullish (BUY signal)
- **MACD line crosses below signal line** → bearish (SELL signal)

### Bollinger Bands
- Three lines around the price: upper band, middle band, lower band
- Price near the **lower band** → potentially oversold
- Price near the **upper band** → potentially overbought
- The bands widen when volatility is high and narrow when it's low

### VWAP (Volume Weighted Average Price)
- The "fair price" for the day, weighted by volume
- **Price above VWAP** → buyers are in control (bullish)
- **Price below VWAP** → sellers are in control (bearish)
- Used mainly for **day trading**

### ATR (Average True Range)
- Measures how much a stock typically moves per day
- Used to set **stop-loss** and **take-profit** distances
- Higher ATR = more volatile stock

---

## 4. The 6 Strategies in This Dashboard

### Day Trading Strategies

#### 🎯 VWAP Trading
**Idea:** Trade around the Volume Weighted Average Price.
- **Buy** when price crosses above VWAP with high volume
- **Sell** when price crosses below VWAP with high volume
- **Exit** when price reverts back to VWAP
- **Best for:** Large, liquid stocks (AAPL, MSFT, SPY)

#### 🔓 Opening Range Breakout (ORB)
**Idea:** The first 30 minutes set the range for the day.
- **Buy** when price breaks above the first 30-minute high
- **Sell** when price breaks below the first 30-minute low
- **Exit** at 2× the opening range size
- **Best for:** Stocks with strong morning volatility

#### 🚀 Momentum / Gap-and-Go
**Idea:** Stocks that gap up/down on news tend to keep moving.
- **Buy** when stock gaps up >2% and RSI + MACD confirm momentum
- **Sell** when stock gaps down >2% with bearish momentum
- **Exit** when momentum exhausts (RSI hits extreme)
- **Best for:** Earnings plays, news-driven stocks

### Swing Trading Strategies

#### ↩️ Mean Reversion (Bollinger Bands)
**Idea:** Prices stretched too far from the average tend to snap back.
- **Buy** when price hits the lower Bollinger Band AND RSI < 30
- **Sell** when price hits the upper Bollinger Band AND RSI > 70
- **Exit** when price returns to the middle band
- **Best for:** Range-bound, non-trending stocks

#### 📐 Fibonacci Retracement
**Idea:** In a trend, pullbacks often stop at specific levels (38.2%, 50%, 61.8%).
- **Buy** when price pulls back to a Fib level in an uptrend
- **Sell** when price bounces to a Fib level in a downtrend
- **Exit** at the 1.618 Fibonacci extension
- **Best for:** Trending stocks with clear swing points

#### 💥 Breakout Trading
**Idea:** When price breaks out of a consolidation range with volume, a big move follows.
- **Buy** when price breaks above resistance + volume >2× average + strong trend (ADX >25)
- **Sell** when price breaks below support under the same conditions
- **Exit** at 2× the risk distance (risk:reward = 1:2)
- **Best for:** Stocks that have been consolidating for weeks

---

## 5. Reading a Signal

When the dashboard generates a signal, here's what each field means:

| Field | What It Means |
|-------|--------------|
| **Signal** | BUY 🟢, SELL 🔴, or HOLD 🟡 |
| **Confidence** | How strong the signal is (60–98%). Higher = more indicators agree |
| **Entry Price** | The price to enter the trade (usually current price) |
| **Stop Loss** | Exit here if the trade goes against you (limits your loss) |
| **Target Price** | Exit here to take your profit |
| **R:R Ratio** | Risk-to-Reward — e.g., 1:2 means you risk $1 to make $2 |
| **Reasoning** | Plain-English explanation of why the signal was generated |

---

## 6. Risk Management Rules

These rules will save you from large losses. **Follow them always.**

### The 2% Rule
Never risk more than **2% of your total account** on a single trade.

> Example: $10,000 account → max risk per trade = $200.
> If your stop loss is $2 away from entry, you can buy 100 shares.

### Always Use a Stop Loss
- A stop loss is a price where you automatically exit a losing trade
- The dashboard calculates stop losses using ATR (so they adapt to volatility)
- **Never move your stop loss further away** — only tighten it

### Risk:Reward Ratio
- Only take trades where the potential reward is **at least 1.5× the risk**
- Example: If you risk $100, your target should be at least $150 profit
- The dashboard shows this as the R:R ratio

### Start Small
- Begin with **paper trading** (simulated trades) or very small positions
- Track your trades in the Portfolio tab
- Review your performance weekly

---

## 7. Common Mistakes to Avoid

| Mistake | Why It's Bad | What to Do Instead |
|---------|-------------|-------------------|
| No stop loss | One bad trade can wipe out weeks of gains | Always set a stop loss before entering |
| Overtrading | More trades ≠ more profit; commissions and bad entries add up | Wait for high-confidence signals (>70%) |
| Chasing | Buying after a stock already moved 10% | Wait for a pullback or the next setup |
| Revenge trading | Trying to "win back" a loss immediately | Walk away; the market will be there tomorrow |
| Ignoring the trend | Buying in a downtrend hoping for a reversal | Trade with the trend, not against it |
| Too much size | Risking 10%+ of your account on one trade | Follow the 2% rule |

---

## 8. How to Use This Dashboard as a Beginner

### Step-by-step workflow:

1. **Start in the 🌊 Swing Trading tab** — pick the Mean Reversion strategy
2. **Enter a stock** you're interested in (or use SPY to practice)
3. **Read the signal** — focus on confidence, entry, stop loss, and target
4. **Check the chart** — does the setup make visual sense?
5. **Check the 📰 AI News tab** — is there any major news that could override the technical signal?
6. **If everything aligns**, record the trade in your 💼 Portfolio tab
7. **Monitor** — check back daily, respect your stop loss and target
8. **Review** — after the trade closes, check your performance stats

### Suggested starting stocks:
- **SPY** — S&P 500 ETF (very liquid, predictable)
- **QQQ** — NASDAQ 100 ETF
- **AAPL** — Apple (high volume, well-behaved charts)

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **ATR** | Average True Range — measures typical daily price movement |
| **Bollinger Bands** | Bands around price showing 2 standard deviations from the 20-day average |
| **Breakout** | When price moves above resistance or below support with conviction |
| **Consolidation** | Price trading in a tight range before a big move |
| **MACD** | Momentum indicator based on moving average crossovers |
| **Mean Reversion** | The idea that extreme prices tend to return to the average |
| **Pullback** | A temporary dip in an uptrend (or bounce in a downtrend) |
| **RSI** | Relative Strength Index — measures overbought/oversold conditions |
| **Stop Loss** | A preset exit point to limit losses |
| **VWAP** | Volume Weighted Average Price — the "fair" intraday price |
| **Volume** | Number of shares traded — confirms the strength of a move |

---

> ⚠️ **Disclaimer:** This guide and this dashboard are for **educational purposes only**. They are not financial advice. Trading involves significant risk — you can lose money. Always do your own research and consider consulting a financial advisor.
