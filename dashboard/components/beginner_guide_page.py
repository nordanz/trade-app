"""Beginner's Guide – Dash component (static, no callbacks needed)."""

from dash import html
import dash_bootstrap_components as dbc


def layout() -> html.Div:
    return html.Div([
        html.P(
            "New to trading? Start here. This guide covers everything you need to "
            "understand the strategies and signals in this dashboard.",
            style={"color": "#b0b8c4", "marginBottom": "1.5rem"},
        ),

        dbc.Accordion(start_collapsed=False, children=[

            # 1 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="1️⃣  What Is Stock Trading?", children=[
                dbc.Table(
                    [
                        html.Thead(html.Tr([
                            html.Th("Style"), html.Th("Holding Period"),
                            html.Th("Typical Gain"), html.Th("Risk Level"),
                        ])),
                        html.Tbody([
                            html.Tr([html.Td("Day Trading"),
                                     html.Td("Minutes to hours (closed by EOD)"),
                                     html.Td("0.5 – 3 %"), html.Td("Higher")]),
                            html.Tr([html.Td("Swing Trading"),
                                     html.Td("Days to weeks"),
                                     html.Td("3 – 10 %"), html.Td("Moderate")]),
                        ]),
                    ],
                    bordered=True, hover=True, size="sm",
                ),
                dbc.Alert(
                    "Starting out? Begin with swing trading — it's slower, less stressful, "
                    "and gives you time to learn.",
                    color="info",
                    style={"marginTop": "0.75rem"},
                ),
            ]),

            # 2 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="2️⃣  Key Concepts", children=[
                dbc.Row([
                    dbc.Col([
                        html.Strong("Price Action"),
                        dbc.Table(
                            [
                                html.Thead(html.Tr([html.Th("Term"), html.Th("Meaning")])),
                                html.Tbody([
                                    html.Tr([html.Td("Open"),    html.Td("Price when the market opens")]),
                                    html.Tr([html.Td("Close"),   html.Td("Price when the market closes")]),
                                    html.Tr([html.Td("High/Low"),html.Td("Highest / lowest price during session")]),
                                    html.Tr([html.Td("Volume"),  html.Td("Shares traded — high volume = more conviction")]),
                                ]),
                            ],
                            bordered=True, size="sm",
                        ),
                    ], md=6),
                    dbc.Col([
                        html.Strong("Trends"),
                        html.Ul(
                            [
                                html.Li("📈 Uptrend — higher highs and higher lows"),
                                html.Li("📉 Downtrend — lower highs and lower lows"),
                                html.Li("↔️ Sideways — bouncing between support and resistance"),
                            ],
                            style={"color": "#b0b8c4", "marginTop": "0.5rem"},
                        ),
                        html.Strong("Support & Resistance",
                                    style={"display": "block", "marginTop": "1rem"}),
                        html.Ul(
                            [
                                html.Li("Support — a price floor where buyers step in"),
                                html.Li("Resistance — a price ceiling where sellers step in"),
                                html.Li("A breakout happens when price pushes through resistance with high volume"),
                            ],
                            style={"color": "#b0b8c4"},
                        ),
                        dbc.Alert("Trade with the trend, not against it.",
                                  color="secondary",
                                  style={"marginTop": "0.5rem", "fontSize": "0.85rem"}),
                    ], md=6),
                ], className="g-3"),
            ]),

            # 3 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="3️⃣  Technical Indicators Explained", children=[
                dbc.Row([
                    dbc.Col([
                        _indicator_card("RSI (Relative Strength Index)", [
                            "Scale: 0 – 100",
                            "Below 30 → oversold (potential BUY)",
                            "Above 70 → overbought (potential SELL)",
                        ]),
                        _indicator_card("MACD", [
                            "Shows momentum & trend direction",
                            "Crosses above signal line → bullish",
                            "Crosses below signal line → bearish",
                        ]),
                        _indicator_card("ATR (Average True Range)", [
                            "How much a stock typically moves per day",
                            "Used to size stop-loss and take-profit",
                        ]),
                    ], md=6),
                    dbc.Col([
                        _indicator_card("Bollinger Bands", [
                            "Three bands around price (upper, middle, lower)",
                            "Price near lower band → potentially oversold",
                            "Price near upper band → potentially overbought",
                            "Bands widen with high volatility",
                        ]),
                        _indicator_card("VWAP", [
                            "Volume Weighted Average Price",
                            "The 'fair price' for the day",
                            "Price above VWAP → buyers in control",
                            "Price below VWAP → sellers in control",
                        ]),
                        _indicator_card("Fibonacci Levels", [
                            "Key pullback levels: 38.2%, 50%, 61.8%",
                            "In a trend, price often bounces at these levels",
                        ]),
                    ], md=6),
                ], className="g-3"),
            ]),

            # 4 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="4️⃣  The 6 Strategies in This Dashboard", children=[
                html.Strong("Day Trading Strategies"),
                dbc.Table(
                    [
                        html.Thead(html.Tr([
                            html.Th("Strategy"), html.Th("Idea"),
                            html.Th("Entry"),    html.Th("Best For"),
                        ])),
                        html.Tbody([
                            html.Tr([html.Td("🎯 VWAP"),
                                     html.Td("Trade around fair value"),
                                     html.Td("Price crosses VWAP + high volume"),
                                     html.Td("Large-cap liquid stocks")]),
                            html.Tr([html.Td("🔓 Opening Range Breakout"),
                                     html.Td("First 30 min sets the range"),
                                     html.Td("Price breaks above/below that range"),
                                     html.Td("Morning volatility plays")]),
                            html.Tr([html.Td("🚀 Momentum / Gap-and-Go"),
                                     html.Td("Gaps tend to continue"),
                                     html.Td("Gap >2% + RSI & MACD confirm"),
                                     html.Td("Earnings & news catalysts")]),
                        ]),
                    ],
                    bordered=True, hover=True, size="sm", className="mt-2",
                ),
                html.Strong("Swing Trading Strategies",
                            style={"display": "block", "marginTop": "1rem"}),
                dbc.Table(
                    [
                        html.Thead(html.Tr([
                            html.Th("Strategy"), html.Th("Idea"),
                            html.Th("Entry"),    html.Th("Best For"),
                        ])),
                        html.Tbody([
                            html.Tr([html.Td("↩️ Mean Reversion"),
                                     html.Td("Stretched prices snap back"),
                                     html.Td("Price at BB extreme + RSI extreme"),
                                     html.Td("Range-bound stocks")]),
                            html.Tr([html.Td("📐 Fibonacci Retracement"),
                                     html.Td("Pullbacks stop at Fib levels"),
                                     html.Td("Price at 38.2/50/61.8% in a trend"),
                                     html.Td("Trending stocks")]),
                            html.Tr([html.Td("💥 Breakout"),
                                     html.Td("Consolidation → big move"),
                                     html.Td("Price breaks resistance + volume >2× + ADX >25"),
                                     html.Td("Stocks coiling before a move")]),
                        ]),
                    ],
                    bordered=True, hover=True, size="sm", className="mt-2",
                ),
            ]),

            # 5 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="5️⃣  Reading a Signal", children=[
                dbc.Table(
                    [
                        html.Thead(html.Tr([html.Th("Field"), html.Th("What It Means")])),
                        html.Tbody([
                            html.Tr([html.Td("Signal"),       html.Td("🟢 BUY, 🔴 SELL, or 🟡 HOLD")]),
                            html.Tr([html.Td("Confidence"),   html.Td("Strength 60–98 %. Higher = more indicators agree")]),
                            html.Tr([html.Td("Entry Price"),  html.Td("Price to enter (usually current price)")]),
                            html.Tr([html.Td("Stop Loss"),    html.Td("Exit here if trade goes against you — limits your loss")]),
                            html.Tr([html.Td("Target Price"), html.Td("Exit here to take profit")]),
                            html.Tr([html.Td("R:R Ratio"),    html.Td("Risk-to-Reward. 1:2 means risk $1 to make $2")]),
                            html.Tr([html.Td("Reasoning"),    html.Td("Plain-English explanation")]),
                        ]),
                    ],
                    bordered=True, hover=True, size="sm",
                ),
            ]),

            # 6 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="6️⃣  Risk Management Rules", children=[
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H6("🛡️ The 2 % Rule"),
                        html.P("Never risk more than 2 % of your account on one trade."),
                        html.P("$10,000 account → max risk = $200.",
                               style={"color": "#888"}),
                    ]), style={"backgroundColor": "#1e2536",
                               "border": "1px solid #2a2f3e"}), md=4),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H6("🚫 Always Use a Stop Loss"),
                        html.P("The dashboard sets stops using ATR."),
                        html.P("Never move your stop further away.",
                               style={"color": "#888"}),
                    ]), style={"backgroundColor": "#1e2536",
                               "border": "1px solid #2a2f3e"}), md=4),
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H6("⚖️ Risk : Reward"),
                        html.P("Only take trades where reward ≥ 1.5× risk."),
                        html.P("Example: risk $100 → target ≥ $150.",
                               style={"color": "#888"}),
                    ]), style={"backgroundColor": "#1e2536",
                               "border": "1px solid #2a2f3e"}), md=4),
                ], className="g-3"),
            ]),

            # 7 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="7️⃣  Common Mistakes to Avoid", children=[
                dbc.Table(
                    [
                        html.Thead(html.Tr([
                            html.Th("Mistake"), html.Th("Why It's Bad"),
                            html.Th("Do This Instead"),
                        ])),
                        html.Tbody([
                            html.Tr([html.Td("No stop loss"),
                                     html.Td("One bad trade can wipe weeks of gains"),
                                     html.Td("Always set a stop before entering")]),
                            html.Tr([html.Td("Overtrading"),
                                     html.Td("More trades ≠ more profit"),
                                     html.Td("Wait for high-confidence signals (>70%)")]),
                            html.Tr([html.Td("Chasing"),
                                     html.Td("Buying after stock already moved 10 %"),
                                     html.Td("Wait for a pullback or next setup")]),
                            html.Tr([html.Td("Revenge trading"),
                                     html.Td("Trying to win back a loss immediately"),
                                     html.Td("Walk away — market will be there tomorrow")]),
                            html.Tr([html.Td("Too much size"),
                                     html.Td("Risking 10 %+ on one trade"),
                                     html.Td("Follow the 2 % rule")]),
                        ]),
                    ],
                    bordered=True, hover=True, size="sm",
                ),
            ]),

            # 8 ─────────────────────────────────────────────────────────────
            dbc.AccordionItem(title="8️⃣  How to Use This Dashboard", children=[
                html.Ol(
                    [
                        html.Li("Start in the 🌊 Swing Trading tab — pick Mean Reversion strategy"),
                        html.Li("Enter a stock you're interested in (or use SPY to practice)"),
                        html.Li("Read the signal — focus on confidence, entry, stop loss, and target"),
                        html.Li("Check the chart — does the setup make visual sense?"),
                        html.Li("Check 📰 AI News — any major news that could override the technical signal?"),
                        html.Li("If everything aligns, record the trade in 💼 Portfolio"),
                        html.Li("Monitor daily — respect your stop loss and target"),
                        html.Li("Review — after the trade closes, check your performance stats"),
                    ],
                    style={"color": "#b0b8c4", "lineHeight": "2"},
                ),
                dbc.Alert(
                    "Suggested starting stocks: SPY (S&P 500 ETF), QQQ (NASDAQ 100), "
                    "AAPL (Apple) — all high-volume and well-behaved.",
                    color="info",
                    style={"marginTop": "1rem"},
                ),
            ]),

            # 9 – Glossary ───────────────────────────────────────────────────
            dbc.AccordionItem(title="9️⃣  Glossary", children=[
                dbc.Table(
                    [
                        html.Thead(html.Tr([html.Th("Term"), html.Th("Definition")])),
                        html.Tbody([
                            html.Tr([html.Td("ATR"),            html.Td("Average True Range — typical daily price movement")]),
                            html.Tr([html.Td("Bollinger Bands"),html.Td("Bands at ±2 std devs from the 20-day moving average")]),
                            html.Tr([html.Td("Breakout"),       html.Td("Price moving above resistance or below support with conviction")]),
                            html.Tr([html.Td("Consolidation"),  html.Td("Price trading in tight range before a big move")]),
                            html.Tr([html.Td("MACD"),           html.Td("Momentum indicator from moving average crossovers")]),
                            html.Tr([html.Td("Mean Reversion"), html.Td("Extreme prices tend to return to the average")]),
                            html.Tr([html.Td("Pullback"),       html.Td("Temporary dip in an uptrend (or bounce in downtrend)")]),
                            html.Tr([html.Td("RSI"),            html.Td("Relative Strength Index — overbought/oversold gauge")]),
                            html.Tr([html.Td("Stop Loss"),      html.Td("Preset exit point to limit losses")]),
                            html.Tr([html.Td("VWAP"),           html.Td("Volume Weighted Average Price — intraday fair value")]),
                            html.Tr([html.Td("Volume"),         html.Td("Shares traded — confirms strength of a move")]),
                        ]),
                    ],
                    bordered=True, hover=True, size="sm",
                ),
            ]),
        ]),

        html.Hr(),
        dbc.Alert(
            "⚠️ Disclaimer: This guide and dashboard are for educational purposes only. "
            "They are not financial advice. Trading involves significant risk — you can lose "
            "money. Always do your own research.",
            color="warning",
            style={"marginTop": "1rem", "fontSize": "0.85rem"},
        ),
    ])


def register_callbacks(app, services):
    """No callbacks — purely static content."""
    pass


# ── helpers ───────────────────────────────────────────────────────────────────

def _indicator_card(title: str, bullets: list) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Strong(title, style={"fontSize": "0.9rem"}),
            html.Ul(
                [html.Li(b, style={"color": "#b0b8c4"}) for b in bullets],
                style={"marginTop": "0.5rem", "paddingLeft": "1.2rem"},
            ),
        ]),
        style={
            "backgroundColor": "#1e2536",
            "border":          "1px solid #2a2f3e",
            "marginBottom":    "0.75rem",
        },
    )
