"""Detailed Charts – Dash component."""

from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.helpers import format_price


def layout(services, watchlist: list) -> html.Div:
    sym_options = [{"label": s, "value": s} for s in (watchlist or ["AAPL"])]

    return html.Div([
        html.P(
            "Candlestick chart with MA overlays and key technical indicators.",
            style={"color": "#888", "fontSize": "0.85rem", "marginBottom": "1rem"},
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Symbol"),
                dcc.Dropdown(
                    id="charts-symbol",
                    options=sym_options,
                    value=sym_options[0]["value"] if sym_options else "AAPL",
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("Period"),
                dcc.Dropdown(
                    id="charts-period",
                    options=[
                        {"label": "1 Month",  "value": "1mo"},
                        {"label": "3 Months", "value": "3mo"},
                        {"label": "6 Months", "value": "6mo"},
                        {"label": "1 Year",   "value": "1y"},
                    ],
                    value="3mo",
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=2),
        ], className="g-3 mb-3"),

        dbc.Spinner(
            html.Div(id="charts-graph"),
            color="primary",
        ),

        html.Div(id="charts-indicators", style={"marginTop": "1.5rem"}),
    ])


def register_callbacks(app, services):

    @app.callback(
        Output("charts-graph",      "children"),
        Output("charts-indicators", "children"),
        Input("charts-symbol", "value"),
        Input("charts-period", "value"),
    )
    def _update_chart(symbol, period):
        if not symbol:
            return dbc.Alert("Select a symbol.", color="info"), ""

        hist = services["market"].get_historical_data(symbol, period=period)
        if hist is None or hist.empty:
            return dbc.Alert(f"No data for {symbol}.", color="danger"), ""

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.72, 0.28],
        )

        fig.add_trace(
            go.Candlestick(
                x=hist.index,
                open=hist["Open"],
                high=hist["High"],
                low=hist["Low"],
                close=hist["Close"],
                name="Price",
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
            ),
            row=1, col=1,
        )

        ma20 = hist["Close"].rolling(20).mean()
        ma50 = hist["Close"].rolling(50).mean()
        fig.add_trace(
            go.Scatter(x=hist.index, y=ma20, name="MA 20",
                       line=dict(color="#ff9800", width=1.2)),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=hist.index, y=ma50, name="MA 50",
                       line=dict(color="#4fc3f7", width=1.2)),
            row=1, col=1,
        )

        colors = [
            "#26a69a" if c >= o else "#ef5350"
            for c, o in zip(hist["Close"], hist["Open"])
        ]
        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist["Volume"],
                name="Volume",
                marker_color=colors,
                showlegend=False,
            ),
            row=2, col=1,
        )

        fig.update_layout(
            title=f"{symbol} – {period.upper()} Chart",
            paper_bgcolor="#0f1117",
            plot_bgcolor="#0f1117",
            font_color="#e0e0e0",
            margin=dict(l=0, r=0, t=40, b=0),
            height=520,
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", y=1.04),
        )
        fig.update_xaxes(gridcolor="#1e2536")
        fig.update_yaxes(gridcolor="#1e2536")

        chart_div = dcc.Graph(figure=fig, config={"displayModeBar": False})

        try:
            ind = services["strategy"].calculate_all_indicators(symbol)
        except Exception:
            ind = None

        if not ind:
            return chart_div, ""

        rsi    = ind.get("rsi")
        macd_d = ind.get("macd", {})
        trend  = ind.get("trend", "N/A")
        support = ind.get("support")

        rsi_cls   = "positive" if rsi and rsi < 30 else ("negative" if rsi and rsi > 70 else "")
        trend_cls = "positive" if "up"   in (trend or "").lower() else (
                    "negative" if "down" in (trend or "").lower() else "")

        indicators_row = html.Div([
            html.H6("📊 Technical Indicators", style={"marginBottom": "0.75rem"}),
            dbc.Row([
                dbc.Col(_kv("RSI",     f"{rsi:.1f}" if rsi else "N/A", rsi_cls), md=3),
                dbc.Col(_kv("MACD",    f"{macd_d.get('macd', 0):.2f}" if macd_d else "N/A"), md=3),
                dbc.Col(_kv("Trend",   trend or "N/A", trend_cls), md=3),
                dbc.Col(_kv("Support", format_price(support) if support else "N/A"), md=3),
            ], className="g-3"),
        ])

        return chart_div, indicators_row


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
