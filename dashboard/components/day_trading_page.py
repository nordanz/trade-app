"""Day Trading – Dash component."""

import dash
from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from services.strategies import DAY_TRADING_STRATEGIES
from utils.helpers import format_price, get_signal_emoji, calculate_risk_reward_ratio
from dashboard.components.backtest_widget import (
    backtest_panel_layout,
    register_backtest_callbacks,
)

_STRATEGY_LABELS = {
    "vwap":     "🎯 VWAP Trading",
    "orb":      "🔓 Opening Range Breakout",
    "momentum": "🚀 Momentum / Gap-and-Go",
}
_STRATEGY_DESCRIPTIONS = {
    "vwap":     "Entry: Price crosses VWAP with volume confirmation. Exit: Mean reversion to VWAP or EOD.",
    "orb":      "Entry: Breakout of first 30-min range with volume. Exit: 2× opening range, stop at opposite side.",
    "momentum": "Entry: Gap >2% + continued momentum (RSI, MACD). Exit: Momentum exhaustion.",
}
_QUICK_SYMBOLS = ["AAPL", "TSLA", "SPY", "QQQ", "NVDA", "MSFT", "AMZN", "META"]


def layout(services) -> html.Div:
    strat_opts = [
        {"label": _STRATEGY_LABELS.get(k, k), "value": k}
        for k in DAY_TRADING_STRATEGIES.keys()
    ]

    return html.Div([
        html.P(
            "⚠️ Data is delayed ~15 minutes (Yahoo Finance). "
            "Intraday signals are for research & screening only — not live execution.",
            style={"color": "#888", "fontSize": "0.82rem", "marginBottom": "1rem"},
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Strategy"),
                dcc.Dropdown(
                    id="dt-strategy",
                    options=strat_opts,
                    value=list(DAY_TRADING_STRATEGIES.keys())[0],
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("Timeframe"),
                dcc.Dropdown(
                    id="dt-timeframe",
                    options=[
                        {"label": "1 min",  "value": "1m"},
                        {"label": "5 min",  "value": "5m"},
                        {"label": "15 min", "value": "15m"},
                        {"label": "30 min", "value": "30m"},
                    ],
                    value="5m",
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=2),
            dbc.Col([
                dbc.Label("News Sentiment"),
                dbc.Switch(id="dt-news", value=True, label="Include"),
            ], md=2),
        ], className="g-3 mb-2"),

        html.Div(id="dt-strat-desc",
                 style={"color": "#888", "fontSize": "0.82rem", "marginBottom": "1rem"}),

        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id="dt-symbol",
                    value="AAPL",
                    placeholder="e.g. AAPL",
                    style={
                        "backgroundColor": "#161b27",
                        "color":           "#e0e0e0",
                        "borderColor":     "#2a2f3e",
                    },
                ),
            ], md=4),
            dbc.Col([
                dbc.Button(
                    "🔍 Generate Signal",
                    id="dt-run-btn",
                    color="primary",
                    className="w-100",
                ),
            ], md=2),
        ], className="g-3 mb-2"),

        html.Div([
            html.Small("Quick select: ", style={"color": "#888"}),
            *[
                dbc.Button(
                    sym,
                    id={"type": "dt-quick", "sym": sym},
                    size="sm",
                    color="secondary",
                    outline=True,
                    className="me-1 mb-1",
                    n_clicks=0,
                )
                for sym in _QUICK_SYMBOLS
            ],
        ], style={"marginBottom": "1rem"}),

        dbc.Spinner(html.Div(id="dt-signal-body"), color="primary"),

        html.Hr(),
        html.H6("📋 Watchlist Scanner"),
        dbc.Row([
            dbc.Col([
                dbc.Input(
                    id="dt-scan-input",
                    value="AAPL,TSLA,NVDA,MSFT,GOOGL",
                    placeholder="AAPL, TSLA, NVDA",
                    style={
                        "backgroundColor": "#161b27",
                        "color":           "#e0e0e0",
                        "borderColor":     "#2a2f3e",
                    },
                ),
            ], md=5),
            dbc.Col([
                dbc.Label("Min Confidence (%)"),
                dcc.Slider(
                    id="dt-scan-conf",
                    min=50, max=90, step=5, value=65,
                    marks={50: "50", 65: "65", 80: "80", 90: "90"},
                    tooltip={"placement": "bottom"},
                ),
            ], md=4),
            dbc.Col([
                dbc.Button(
                    "🔍 Scan Watchlist",
                    id="dt-scan-btn",
                    color="secondary",
                    className="w-100",
                ),
            ], md=3),
        ], className="g-3 mb-2"),

        dbc.Spinner(html.Div(id="dt-scan-body"), color="secondary"),

        backtest_panel_layout(prefix="dt", is_intraday=True),
    ])


def register_callbacks(app, services):

    register_backtest_callbacks(
        app, services,
        prefix="dt",
        symbol_state_id="dt-symbol",
        strategy_state_id="dt-strategy",
        is_intraday=True,
    )

    @app.callback(
        Output("dt-strat-desc", "children"),
        Input("dt-strategy", "value"),
    )
    def _desc(strategy):
        return _STRATEGY_DESCRIPTIONS.get(strategy, "")

    @app.callback(
        Output("dt-symbol", "value"),
        Input({"type": "dt-quick", "sym": dash.ALL}, "n_clicks"),
        State("dt-symbol", "value"),
        prevent_initial_call=True,
    )
    def _quick_select(_clicks, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            return current
        import json
        btn_id = json.loads(ctx.triggered[0]["prop_id"].rsplit(".", 1)[0])
        return btn_id["sym"]

    @app.callback(
        Output("dt-signal-body", "children"),
        Input("dt-run-btn", "n_clicks"),
        State("dt-symbol",   "value"),
        State("dt-strategy", "value"),
        State("dt-timeframe","value"),
        State("dt-news",     "value"),
        prevent_initial_call=True,
    )
    def _run_signal(_, symbol, strategy, timeframe, include_news):
        symbol = (symbol or "AAPL").strip().upper()
        try:
            signal = services["strategy"].generate_signal(
                symbol=symbol,
                strategy_name=strategy,
                timeframe=timeframe,
                include_news=bool(include_news),
            )
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger")

        if not signal:
            return dbc.Alert(
                f"Could not generate a signal for {symbol}. Check the symbol and try again.",
                color="warning",
            )

        # Chart
        try:
            hist = services["market"].get_historical_data(symbol, period="1d", interval=timeframe)
        except Exception:
            hist = None

        chart = html.Div()
        if hist is not None and not hist.empty:
            fig = go.Figure(
                go.Candlestick(
                    x=hist.index,
                    open=hist["Open"], high=hist["High"],
                    low=hist["Low"],   close=hist["Close"],
                    name=symbol,
                    increasing_line_color="#26a69a",
                    decreasing_line_color="#ef5350",
                )
            )
            if signal.entry_price:
                fig.add_hline(y=signal.entry_price, line_color="#4fc3f7",
                              line_dash="dash", annotation_text="Entry")
            if signal.stop_loss:
                fig.add_hline(y=signal.stop_loss, line_color="#ef5350",
                              line_dash="dot", annotation_text="Stop")
            if signal.target_price:
                fig.add_hline(y=signal.target_price, line_color="#26a69a",
                              line_dash="dot", annotation_text="Target")
            fig.update_layout(
                paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font_color="#e0e0e0",
                margin=dict(l=0, r=0, t=30, b=0), height=300,
                xaxis_rangeslider_visible=False,
            )
            fig.update_xaxes(gridcolor="#1e2536")
            fig.update_yaxes(gridcolor="#1e2536")
            chart = dcc.Graph(figure=fig, config={"displayModeBar": False})

        emoji  = get_signal_emoji(signal.signal.value)
        color  = ("success" if signal.signal.value == "BUY"
                  else "danger" if signal.signal.value == "SELL"
                  else "secondary")
        rr     = calculate_risk_reward_ratio(
            signal.entry_price, signal.target_price, signal.stop_loss
        )

        return html.Div([
            dbc.Alert(f"{emoji} {signal.signal.value} — {symbol}", color=color,
                      style={"fontWeight": "bold"}),
            dbc.Row([
                dbc.Col(_kv("Entry",      format_price(signal.entry_price)),  md=3),
                dbc.Col(_kv("Target",     format_price(signal.target_price)), md=3),
                dbc.Col(_kv("Stop Loss",  format_price(signal.stop_loss)),    md=3),
                dbc.Col(_kv("Confidence", f"{signal.confidence:.0f}%"),       md=3),
            ], className="g-3 mb-2"),
            html.Small(f"Holding: {signal.holding_period}  |  R/R: 1:{rr:.2f}",
                       style={"color": "#888"}),
            dbc.Alert(signal.reasoning, color=color,
                      style={"marginTop": "0.5rem", "padding": "0.4rem 0.75rem",
                             "fontSize": "0.85rem"}),
            html.Div(style={"marginTop": "0.75rem"}, children=[chart]),
        ])

    @app.callback(
        Output("dt-scan-body", "children"),
        Input("dt-scan-btn",  "n_clicks"),
        State("dt-scan-input","value"),
        State("dt-strategy",  "value"),
        State("dt-timeframe", "value"),
        State("dt-scan-conf", "value"),
        prevent_initial_call=True,
    )
    def _scan(_, watchlist_str, strategy, timeframe, min_conf):
        symbols = [s.strip().upper() for s in (watchlist_str or "").split(",") if s.strip()]
        if not symbols:
            return dbc.Alert("Enter at least one symbol.", color="info")
        try:
            signals = services["strategy"].scan_multiple_symbols(
                symbols=symbols,
                strategy_name=strategy,
                timeframe=timeframe,
                min_confidence=min_conf,
            )
        except Exception as e:
            return dbc.Alert(f"Scan error: {e}", color="danger")

        if not signals:
            return dbc.Alert(
                f"No signals found above {min_conf}% confidence.", color="info"
            )

        cards = []
        for sig in signals:
            emoji = get_signal_emoji(sig.signal.value)
            color = ("success" if sig.signal.value == "BUY"
                     else "danger" if sig.signal.value == "SELL"
                     else "secondary")
            cards.append(dbc.Alert(
                [
                    html.Strong(f"{emoji} {sig.signal.value} — {sig.symbol}"),
                    f"  |  {format_price(sig.entry_price)}  |  {sig.confidence:.0f}% confidence",
                ],
                color=color,
                style={"padding": "0.4rem 0.75rem", "marginBottom": "0.4rem"},
            ))

        return html.Div([
            dbc.Alert(
                f"✅ Found {len(signals)} signal(s) above {min_conf}% confidence",
                color="success",
                style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem"},
            ),
            *cards,
        ])


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
