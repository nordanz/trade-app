"""
Beginner's Guide Tab - In-app educational content for new traders.
Covers trading basics, indicators, strategies, risk management, and glossary.
"""

import streamlit as st


def render_beginner_guide_page():
    """Render the beginner's guide as an interactive in-app tab."""
    st.markdown(
        "New to trading? Start here. This guide covers everything you need to "
        "understand the strategies and signals in this dashboard."
    )

    # ------------------------------------------------------------------ #
    # Sections as expandable blocks so the page isn't overwhelming
    # ------------------------------------------------------------------ #

    # --- Section 1 ---------------------------------------------------- #
    with st.expander("1️⃣  What Is Stock Trading?", expanded=True):
        st.markdown("""
Stock trading means buying and selling shares of a company.
You profit when you **buy low and sell high**.

This dashboard supports two styles:

| Style | Holding Period | Typical Gain | Risk Level |
|-------|---------------|-------------|------------|
| **Day Trading** | Minutes to hours (closed by EOD) | 0.5 – 3 % | Higher — fast decisions |
| **Swing Trading** | Days to weeks | 3 – 10 % | Moderate — more thinking time |

> **Starting out?** Begin with **swing trading** — it's slower, less stressful,
> and gives you time to learn.
        """)

    # --- Section 2 ---------------------------------------------------- #
    with st.expander("2️⃣  Key Concepts"):
        st.markdown("""
#### Price Action
| Term | Meaning |
|------|---------|
| **Open** | Price when the market opens |
| **Close** | Price when the market closes |
| **High / Low** | Highest and lowest price during the session |
| **Volume** | How many shares were traded — high volume = more conviction |

#### Support & Resistance
- **Support** — a price floor where buyers step in
- **Resistance** — a price ceiling where sellers step in
- A **breakout** happens when price pushes through resistance with high volume

#### Trends
- 📈 **Uptrend** — higher highs and higher lows
- 📉 **Downtrend** — lower highs and lower lows
- ↔️ **Sideways** — bouncing between support and resistance

> **Rule of thumb:** Trade *with* the trend, not against it.
        """)

    # --- Section 3 ---------------------------------------------------- #
    with st.expander("3️⃣  Technical Indicators Explained"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
**RSI (Relative Strength Index)**
- Scale: 0 – 100
- Below **30** → oversold (potential BUY)
- Above **70** → overbought (potential SELL)
- Think of a rubber band — the more stretched, the more likely it snaps back

**MACD**
- Shows momentum & trend direction
- MACD line **crosses above** signal → bullish
- MACD line **crosses below** signal → bearish

**ATR (Average True Range)**
- How much a stock typically moves per day
- Used to size stop-loss and take-profit
            """)

        with col2:
            st.markdown("""
**Bollinger Bands**
- Three lines around price (upper, middle, lower)
- Price near **lower band** → potentially oversold
- Price near **upper band** → potentially overbought
- Bands widen with high volatility, narrow with low

**VWAP (Volume Weighted Average Price)**
- The "fair price" for the day, weighted by volume
- Price **above** VWAP → buyers in control
- Price **below** VWAP → sellers in control
- Mainly used for day trading

**Fibonacci Levels**
- Key pullback levels: 38.2 %, 50 %, 61.8 %
- In a trend, price often bounces at these levels
            """)

    # --- Section 4 ---------------------------------------------------- #
    with st.expander("4️⃣  The 6 Strategies in This Dashboard"):
        st.subheader("Day Trading Strategies")

        st.markdown("""
| Strategy | Idea | Entry | Exit | Best For |
|----------|------|-------|------|----------|
| 🎯 **VWAP** | Trade around fair value | Price crosses VWAP + high volume | Price reverts to VWAP | Large-cap liquid stocks |
| 🔓 **Opening Range Breakout** | First 30 min sets the range | Price breaks above/below that range | 2× the range size | Morning volatility plays |
| 🚀 **Momentum / Gap-and-Go** | Gaps tend to continue | Gap >2 % + RSI & MACD confirm | RSI hits extreme | Earnings & news catalysts |
        """)

        st.subheader("Swing Trading Strategies")

        st.markdown("""
| Strategy | Idea | Entry | Exit | Best For |
|----------|------|-------|------|----------|
| ↩️ **Mean Reversion** | Stretched prices snap back | Price at BB extreme + RSI < 30 or > 70 | Price returns to middle band | Range-bound stocks |
| 📐 **Fibonacci Retracement** | Pullbacks stop at Fib levels | Price at 38.2/50/61.8 % in a trend | 1.618 extension | Trending stocks |
| 💥 **Breakout** | Consolidation → big move | Price breaks support/resistance + volume >2× + ADX >25 | 2× risk distance | Stocks coiling before a move |
        """)

    # --- Section 5 ---------------------------------------------------- #
    with st.expander("5️⃣  Reading a Signal"):
        st.markdown("""
When the dashboard generates a signal, here's what each field means:

| Field | What It Means |
|-------|--------------|
| **Signal** | 🟢 BUY, 🔴 SELL, or 🟡 HOLD |
| **Confidence** | Strength of the signal (60 – 98 %). Higher = more indicators agree |
| **Entry Price** | Price to enter (usually the current price) |
| **Stop Loss** | Exit here if the trade goes against you — **limits your loss** |
| **Target Price** | Exit here to take profit |
| **R:R Ratio** | Risk-to-Reward. 1:2 means you risk $1 to make $2 |
| **Reasoning** | Plain-English explanation |
        """)

    # --- Section 6 ---------------------------------------------------- #
    with st.expander("6️⃣  Risk Management Rules", expanded=True):
        st.markdown("""
These rules protect your capital. **Follow them always.**
        """)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
##### 🛡️ The 2 % Rule
Never risk more than **2 %** of your account on one trade.

> $10,000 account → max risk = $200.
> Stop loss $2 away → max 100 shares.
            """)

        with col2:
            st.markdown("""
##### 🚫 Always Use a Stop Loss
- The dashboard sets stops using ATR
- **Never move your stop further away**
- Only tighten it as the trade moves in your favour
            """)

        with col3:
            st.markdown("""
##### ⚖️ Risk : Reward
- Only take trades where reward ≥ 1.5× risk
- Example: risk $100 → target ≥ $150
- Shown as the R:R ratio on every signal
            """)

    # --- Section 7 ---------------------------------------------------- #
    with st.expander("7️⃣  Common Mistakes to Avoid"):
        st.markdown("""
| Mistake | Why It's Bad | Do This Instead |
|---------|-------------|-----------------|
| No stop loss | One bad trade can wipe out weeks of gains | Always set a stop before entering |
| Overtrading | More trades ≠ more profit | Wait for high-confidence signals (> 70 %) |
| Chasing | Buying after a stock already moved 10 % | Wait for a pullback or the next setup |
| Revenge trading | Trying to "win back" a loss immediately | Walk away — the market will be there tomorrow |
| Ignoring the trend | Buying in a downtrend hoping for a reversal | Trade with the trend |
| Too much size | Risking 10 %+ on one trade | Follow the 2 % rule |
        """)

    # --- Section 8 ---------------------------------------------------- #
    with st.expander("8️⃣  How to Use This Dashboard (Step by Step)"):
        st.markdown("""
1. **Start in the 🌊 Swing Trading tab** — pick the *Mean Reversion* strategy
2. **Enter a stock** you're interested in (or use **SPY** to practice)
3. **Read the signal** — focus on confidence, entry, stop loss, and target
4. **Check the chart** — does the setup make visual sense?
5. **Check 📰 AI News** — any major news that could override the technical signal?
6. **If everything aligns**, record the trade in 💼 My Portfolio
7. **Monitor daily** — respect your stop loss and target
8. **Review** — after the trade closes, check your performance stats
        """)

        st.info(
            "**Suggested starting stocks:** SPY (S&P 500 ETF), QQQ (NASDAQ 100), "
            "AAPL (Apple) — all high-volume and well-behaved."
        )

    # --- Section 9 ---------------------------------------------------- #
    with st.expander("9️⃣  Glossary"):
        st.markdown("""
| Term | Definition |
|------|-----------|
| **ATR** | Average True Range — typical daily price movement |
| **Bollinger Bands** | Bands at ±2 std devs from the 20-day moving average |
| **Breakout** | Price moving above resistance or below support with conviction |
| **Consolidation** | Price trading in a tight range before a big move |
| **MACD** | Momentum indicator from moving average crossovers |
| **Mean Reversion** | Extreme prices tend to return to the average |
| **Pullback** | Temporary dip in an uptrend (or bounce in a downtrend) |
| **RSI** | Relative Strength Index — overbought / oversold gauge |
| **Stop Loss** | Preset exit point to limit losses |
| **VWAP** | Volume Weighted Average Price — intraday fair value |
| **Volume** | Shares traded — confirms strength of a move |
        """)

    # --- Disclaimer --------------------------------------------------- #
    st.markdown("---")
    st.warning(
        "⚠️ **Disclaimer:** This guide and this dashboard are for **educational "
        "purposes only**. They are not financial advice. Trading involves "
        "significant risk — you can lose money. Always do your own research."
    )
