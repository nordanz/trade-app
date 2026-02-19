"""News Controller – Dash component."""

from datetime import datetime
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from dash import dcc


_IMPACT_DATA = [
    {"Date": "2026-02-18", "Event": "Fed Rate Decision",  "Sentiment": "Neutral",  "Impact": "High",   "Market Move": "+0.5%", "Stocks Affected": "Broad"},
    {"Date": "2026-02-17", "Event": "CPI Report Higher",  "Sentiment": "Negative", "Impact": "High",   "Market Move": "-1.2%", "Stocks Affected": "Bonds/Equities"},
    {"Date": "2026-02-16", "Event": "Tech Earnings Beat", "Sentiment": "Positive", "Impact": "Medium", "Market Move": "+1.8%", "Stocks Affected": "Tech/Growth"},
    {"Date": "2026-02-15", "Event": "Oil Price Spike",    "Sentiment": "Negative", "Impact": "High",   "Market Move": "-0.8%", "Stocks Affected": "Energy/Broad"},
    {"Date": "2026-02-14", "Event": "Jobs Report Weak",   "Sentiment": "Negative", "Impact": "High",   "Market Move": "-1.5%", "Stocks Affected": "Broad"},
]


def layout(services) -> html.Div:
    return html.Div([
        dbc.Tabs(id="nc-tabs", active_tab="tab-settings", children=[

            # ── Tab 1: Global Settings ─────────────────────────────────────
            dbc.Tab(label="⚙️ Global Settings", tab_id="tab-settings", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    dbc.Row([
                        dbc.Col([
                            html.Strong("News Integration"),
                            dbc.Switch(
                                id="nc-enable-news",
                                value=True,
                                label="Enable News Analysis",
                                className="mt-2",
                            ),
                            dbc.Label("News Signal Weight", className="mt-3"),
                            dcc.Slider(
                                id="nc-weight",
                                min=0, max=100, step=5, value=50,
                                marks={0: "0%", 50: "50%", 100: "100%"},
                                tooltip={"placement": "bottom"},
                            ),
                            dbc.Label("Minimum News Relevance", className="mt-3"),
                            dcc.Slider(
                                id="nc-relevance",
                                min=0, max=100, step=5, value=30,
                                marks={0: "0%", 50: "50%", 100: "100%"},
                                tooltip={"placement": "bottom"},
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Strong("Sentiment Thresholds"),
                            dbc.Label("Bullish Threshold", className="mt-3"),
                            dcc.Slider(
                                id="nc-bullish-thr",
                                min=0.0, max=1.0, step=0.1, value=0.4,
                                marks={0: "0", 0.5: "0.5", 1: "1"},
                                tooltip={"placement": "bottom"},
                            ),
                            dbc.Label("Bearish Threshold", className="mt-3"),
                            dcc.Slider(
                                id="nc-bearish-thr",
                                min=-1.0, max=0.0, step=0.1, value=-0.4,
                                marks={-1: "-1", -0.5: "-0.5", 0: "0"},
                                tooltip={"placement": "bottom"},
                            ),
                        ], md=6),
                    ], className="g-3"),
                    html.Hr(),
                    html.Div(id="nc-settings-summary"),
                ]),
            ]),

            # ── Tab 2: News Analysis ───────────────────────────────────────
            dbc.Tab(label="📊 News Analysis", tab_id="tab-analysis", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(
                                id="nc-symbol",
                                value="AAPL",
                                placeholder="AAPL, TSLA, SPY",
                                style={
                                    "backgroundColor": "#161b27",
                                    "color":           "#e0e0e0",
                                    "borderColor":     "#2a2f3e",
                                },
                            ),
                        ], md=4),
                        dbc.Col([
                            dbc.Button(
                                "🔍 Analyze News",
                                id="nc-analyze-btn",
                                color="primary",
                                className="w-100",
                            ),
                        ], md=2),
                    ], className="g-3 mb-3"),
                    dbc.Spinner(html.Div(id="nc-analysis-output"), color="primary"),
                ]),
            ]),

            # ── Tab 3: Macro Events ────────────────────────────────────────
            dbc.Tab(label="🌍 Macro Events", tab_id="tab-macro", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    html.Strong("Active Macro Events"),
                    html.P(
                        "Toggle events currently affecting the broader market.",
                        style={"color": "#888", "fontSize": "0.85rem"},
                    ),
                    dbc.Row([
                        dbc.Col(dbc.Switch(id="macro-fed",      label="🪙 Federal Reserve Decision",  value=False), md=6),
                        dbc.Col(dbc.Switch(id="macro-cpi",      label="💰 Employment / CPI Report",   value=False), md=6),
                        dbc.Col(dbc.Switch(id="macro-geo",      label="⚔️ War / Geopolitical Crisis", value=False), md=6),
                        dbc.Col(dbc.Switch(id="macro-earnings", label="📊 Earnings Season",           value=False), md=6),
                        dbc.Col(dbc.Switch(id="macro-housing",  label="🏠 Housing / Real Estate",     value=False), md=6),
                    ], className="g-3"),
                    html.Hr(),
                    html.Strong("Signal Adjustments"),
                    dbc.Label("Volatility Multiplier", className="mt-2"),
                    dcc.Slider(
                        id="macro-vol-mult",
                        min=0.5, max=2.0, step=0.1, value=1.0,
                        marks={0.5: "0.5×", 1.0: "1×", 1.5: "1.5×", 2.0: "2×"},
                        tooltip={"placement": "bottom"},
                    ),
                    dbc.Label("Max Position Size (%)", className="mt-3"),
                    dcc.Slider(
                        id="macro-max-pos",
                        min=10, max=100, step=5, value=100,
                        marks={10: "10%", 50: "50%", 100: "100%"},
                        tooltip={"placement": "bottom"},
                    ),
                    html.Div(id="macro-status", className="mt-3"),
                ]),
            ]),

            # ── Tab 4: Impact History ──────────────────────────────────────
            dbc.Tab(label="📈 Impact History", tab_id="tab-history", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    html.Strong("Recent News Events & Market Impact"),
                    dbc.Table(
                        [
                            html.Thead(html.Tr([
                                html.Th(c)
                                for c in ["Date", "Event", "Sentiment", "Impact",
                                          "Market Move", "Stocks Affected"]
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td(row["Date"]),
                                    html.Td(row["Event"]),
                                    html.Td(
                                        row["Sentiment"],
                                        style={"color":
                                               "#26a69a" if row["Sentiment"] == "Positive"
                                               else "#ef5350" if row["Sentiment"] == "Negative"
                                               else "#888"},
                                    ),
                                    html.Td(row["Impact"]),
                                    html.Td(
                                        row["Market Move"],
                                        style={"color":
                                               "#26a69a" if row["Market Move"].startswith("+")
                                               else "#ef5350"},
                                    ),
                                    html.Td(row["Stocks Affected"]),
                                ])
                                for row in _IMPACT_DATA
                            ]),
                        ],
                        bordered=True, hover=True,
                        style={"fontSize": "0.85rem", "marginTop": "1rem"},
                    ),
                ]),
            ]),
        ]),
    ])


def register_callbacks(app, services):

    @app.callback(
        Output("nc-settings-summary", "children"),
        Input("nc-enable-news", "value"),
        Input("nc-weight",      "value"),
        Input("nc-relevance",   "value"),
        Input("nc-bullish-thr", "value"),
        Input("nc-bearish-thr", "value"),
    )
    def _settings_summary(enabled, weight, relevance, bullish, bearish):
        items = [
            ("News Enabled",      "✅" if enabled else "❌"),
            ("Weight",            f"{weight}%"),
            ("Min Relevance",     f"{relevance}%"),
            ("Bullish Threshold", f"{bullish:.1f}"),
            ("Bearish Threshold", f"{bearish:.1f}"),
        ]
        return html.Ul(
            [html.Li(f"{k}: {v}") for k, v in items],
            style={"color": "#b0b8c4", "fontSize": "0.85rem"},
        )

    @app.callback(
        Output("nc-analysis-output", "children"),
        Input("nc-analyze-btn",  "n_clicks"),
        State("nc-symbol",       "value"),
        prevent_initial_call=True,
    )
    def _analyze(_, symbol):
        symbol = (symbol or "AAPL").strip().upper()
        gemini = services.get("gemini")
        market = services.get("market")

        if not gemini or not gemini.is_available():
            return dbc.Alert(
                "Gemini service unavailable. Check your GEMINI_API_KEY in .env.",
                color="danger",
            )

        try:
            info     = market.get_company_info(symbol) if market else {}
            analysis = gemini.analyze_stock_news(symbol, info.get("name", symbol))
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger")

        if not analysis:
            return dbc.Alert(
                f"No news analysis returned for {symbol}.", color="warning"
            )

        score = analysis.sentiment_score
        if score > 0.6:
            rec_color, rec_text = "success",   "✅ Strongly Bullish — consider increasing position size for BUY signals"
        elif score > 0.3:
            rec_color, rec_text = "info",      "📈 Mildly Bullish — confirm with technical signals before entering"
        elif score < -0.6:
            rec_color, rec_text = "danger",    "❌ Strongly Bearish — reduce position size, exercise caution"
        elif score < -0.3:
            rec_color, rec_text = "warning",   "📉 Mildly Bearish — confirm with technical signals before shorting"
        else:
            rec_color, rec_text = "secondary", "⚪ Neutral — rely on technicals"

        return html.Div([
            dbc.Alert(
                f"✅ Analysis complete for {symbol}",
                color="success",
                style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem"},
            ),
            dbc.Row([
                dbc.Col(_kv("Sentiment",    analysis.sentiment.value), md=3),
                dbc.Col(_kv("Score",        f"{score:.2f}",
                            "positive" if score > 0 else "negative"), md=3),
                dbc.Col(_kv("Relevance",    f"{analysis.relevance:.0f}%"), md=3),
                dbc.Col(_kv("Macro Impact", "Yes ⚠️" if analysis.macro_impact else "No"), md=3),
            ], className="g-3 mb-3"),
            dbc.Card(
                dbc.CardBody([
                    html.Strong("Summary"),
                    html.P(
                        analysis.summary,
                        style={"marginTop": "0.5rem", "color": "#b0b8c4"},
                    ),
                    (html.Div(
                        f"Headline: {analysis.headline}",
                        style={"fontSize": "0.85rem", "color": "#888"},
                    ) if analysis.headline else ""),
                    html.Hr(),
                    dbc.Alert(
                        rec_text,
                        color=rec_color,
                        style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem",
                               "marginBottom": 0},
                    ),
                ]),
                style={"backgroundColor": "#161b27", "border": "1px solid #2a2f3e"},
            ),
            html.P(
                f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style={"color": "#555", "fontSize": "0.75rem", "marginTop": "0.5rem"},
            ),
        ])

    @app.callback(
        Output("macro-status", "children"),
        Input("macro-fed",      "value"),
        Input("macro-cpi",      "value"),
        Input("macro-geo",      "value"),
        Input("macro-earnings", "value"),
        Input("macro-housing",  "value"),
        Input("macro-vol-mult", "value"),
        Input("macro-max-pos",  "value"),
    )
    def _macro_status(fed, cpi, geo, earnings, housing, mult, max_pos):
        active = any([fed, cpi, geo, earnings, housing])
        if active or mult != 1.0 or max_pos != 100:
            return dbc.Alert(
                f"⚠️ Macro mode active: Volatility {mult}×, Max position {max_pos}%",
                color="warning",
                style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem"},
            )
        return ""


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
