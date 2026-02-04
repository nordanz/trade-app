# News and Noise: Integrating External Parameters into Signals

Professional trading platforms (like Bloomberg Terminal, Reuters Eikon, or institutional HFT systems) treat news not just as "text" but as high-dimensional data points.

## 1. News as a Quantitative Signal
Instead of just reading a headline, big software converts news into numbers:
- **Sentiment Score (-1 to 1):** Using NLP (Natural Language Processing) to determine if the news is bullish or bearish.
- **Relevance Score (0-100):** How much the news actually impacts the specific ticker. A "War" news item has high relevance for Oil/Gold but lower for a small-cap tech stock.
- **Urgency (Latency):** Breaking news triggers immediate execution before retail traders can react.

## 2. Macro-Event Parameters (e.g., "The War Factor")
Large-scale events (War, Pandemics, Sanctions) act as **Contextual Overrides**.
- **The "Risk-Off" Filter:** When a high-impact negative event occurs, software may automatically:
    - Increase "Stop Loss" tightness.
    - Reduce "Position Sizing."
    - Require higher confidence scores (e.g., from 70% to 90%) for BUY signals.
- **Correlation Clusters:** A war in the Middle East is a "Signal" for Energy stocks (BUY) and Airline stocks (SELL) simultaneously.

## 3. Dealing with "Noise"
Noise is price movement that doesn't reflect a change in fundamentals.
- **Volume Filtering:** If a news item causes a price spike on low volume, it's often flagged as "Noise" and ignored.
- **Sentiment Divergence:** If news is 100% positive but price doesn't move, it's a signal that the news was already "priced in" (Selling the News).
- **Source Weighting:** News from a Tier-1 source (Bloomberg/WSJ) is weighted 10x higher than a random tweet or blog post.

## 4. Algorithmic Implementation Logic
Professional systems often use a "Multi-Factor Model":
1.  **Technical Engine:** RSI, MA, MACD give a base signal.
2.  **Sentiment Engine:** Gemini/GPT-4 analyze recent headlines.
3.  **Macro Engine:** Monitors VIX (Volatility Index) and Geopolitical Tags.
4.  **Final Logic:** `If Technical == BUY AND News_Sentiment > 0.5 AND VIX < 25 THEN EXECUTE`.

## 5. How we can implement this in eSignal
We can add a `MacroImpact` parameter to our strategy:
- **Parameter `impact_type`:** `WAR`, `EARNINGS`, `FED_MEETING`.
- **Parameter `direction`:** `-1` (Downside pressure), `+1` (Upside pressure).
- **Logic:** This parameter adjusts the `confidence` score of technical signals. For example, a "War" parameter would penalize all Buy signals by 30% unless they are in the Defense or Energy sectors.
