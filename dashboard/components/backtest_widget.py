"""
Reusable inline backtest panel – Dash version.

Drop into any page with:

    from dashboard.components.backtest_widget import backtest_panel_layout, register_backtest_callbacks
    # in layout():
    backtest_panel_layout(prefix="dt")   # returns a dbc.Card collapse widget
    # in register_callbacks():
    register_backtest_callbacks(app, services, prefix="dt", is_intraday=True)

IDs used (all prefixed):
    {prefix}-bt-toggle   – collapse toggle button
    {prefix}-bt-collapse – the collapsible card body
    {prefix}-bt-start    – start date
    {prefix}-bt-end      – end date
    {prefix}-bt-cash     – starting cash
    {prefix}-bt-sentiment– include news sentiment switch
    {prefix}-bt-run      – run button
    {prefix}-bt-output   – results div
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc

from utils.helpers import format_price, format_percentage


# ── Public helpers ──────────────────────────────────────────────────────────

def backtest_panel_layout(prefix: str, is_intraday: bool = False) -> html.Div:
    """Return the full collapse widget. Embed anywhere in a page layout."""
    default_days = 30 if is_intraday else 180
    default_start = (date.today() - timedelta(days=default_days)).isoformat()
    default_end   = date.today().isoformat()

    return html.Div([
        html.Hr(),
        dbc.Button(
            "🧪 Backtest This Strategy",
            id=f"{prefix}-bt-toggle",
            color="link",
            style={
                "color": "#4fc3f7",
                "textDecoration": "none",
                "fontWeight": "bold",
                "paddingLeft": 0,
            },
        ),
        dbc.Collapse(
            id=f"{prefix}-bt-collapse",
            is_open=False,
            children=[
                dbc.Card([
                    dbc.CardBody([
                        html.P(
                            "Validate how this strategy performed historically "
                            "before acting on a live signal.",
                            style={"color": "#aaa", "fontSize": "0.85rem",
                                   "marginBottom": "1rem"},
                        ),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Start Date"),
                                dbc.Input(
                                    id=f"{prefix}-bt-start",
                                    type="date",
                                    value=default_start,
                                    style={"backgroundColor": "#161b27",
                                           "color": "#e0e0e0",
                                           "borderColor": "#2a2f3e"},
                                ),
                            ], md=3),
                            dbc.Col([
                                dbc.Label("End Date"),
                                dbc.Input(
                                    id=f"{prefix}-bt-end",
                                    type="date",
                                    value=default_end,
                                    style={"backgroundColor": "#161b27",
                                           "color": "#e0e0e0",
                                           "borderColor": "#2a2f3e"},
                                ),
                            ], md=3),
                            dbc.Col([
                                dbc.Label("Starting Capital ($)"),
                                dbc.Input(
                                    id=f"{prefix}-bt-cash",
                                    type="number",
                                    min=1000, max=1_000_000,
                                    step=1000, value=10000,
                                    style={"backgroundColor": "#161b27",
                                           "color": "#e0e0e0",
                                           "borderColor": "#2a2f3e"},
                                ),
                            ], md=3),
                            dbc.Col([
                                dbc.Label("News Sentiment"),
                                dbc.Switch(
                                    id=f"{prefix}-bt-sentiment",
                                    value=False,
                                    label="Include",
                                ),
                            ], md=3),
                        ], className="g-3 mb-3"),
                        dbc.Button(
                            "▶️ Run Backtest",
                            id=f"{prefix}-bt-run",
                            color="primary",
                            className="w-100 mb-3",
                        ),
                        dbc.Spinner(
                            html.Div(id=f"{prefix}-bt-output"),
                            color="primary",
                        ),
                    ]),
                ], style={"backgroundColor": "#161b27", "border": "1px solid #2a2f3e",
                          "marginTop": "0.5rem"}),
            ],
        ),
    ])


def register_backtest_callbacks(
    app,
    services,
    prefix: str,
    symbol_state_id: str,
    strategy_state_id: str,
    is_intraday: bool = False,
) -> None:
    """Register the toggle + run callbacks for a backtest panel."""

    @app.callback(
        Output(f"{prefix}-bt-collapse", "is_open"),
        Input(f"{prefix}-bt-toggle", "n_clicks"),
        State(f"{prefix}-bt-collapse", "is_open"),
        prevent_initial_call=True,
    )
    def _toggle(_, is_open):
        return not is_open

    @app.callback(
        Output(f"{prefix}-bt-output", "children"),
        Input(f"{prefix}-bt-run", "n_clicks"),
        State(symbol_state_id,          "value"),
        State(strategy_state_id,        "value"),
        State(f"{prefix}-bt-start",     "value"),
        State(f"{prefix}-bt-end",       "value"),
        State(f"{prefix}-bt-cash",      "value"),
        State(f"{prefix}-bt-sentiment", "value"),
        prevent_initial_call=True,
    )
    def _run(_, symbol, strategy, start_date, end_date, cash, use_sentiment):
        symbol = (symbol or "AAPL").strip().upper()
        if not strategy:
            return dbc.Alert("Select a strategy first.", color="warning")

        interval = "5m" if is_intraday else "1d"
        try:
            from datetime import datetime, timedelta
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            end_fetch = end_dt.strftime("%Y-%m-%d")

            hist = services["market"].get_historical_data(
                symbol,
                interval=interval,
                start=start_date,
                end=end_fetch,
            )
        except Exception as e:
            return dbc.Alert(f"Data fetch error: {e}", color="danger")

        if hist is None or hist.empty:
            return dbc.Alert(
                f"No data for {symbol} between {start_date} and {end_date}. "
                "Try a wider date range.",
                color="warning",
            )

        try:
            result = services["backtest"].run_backtest(
                ohlc_data=hist,
                symbol=symbol,
                strategy_name=strategy,
                cash=float(cash or 10000),
                use_sentiment=bool(use_sentiment),
            )
        except Exception as e:
            return dbc.Alert(f"Backtest error: {e}", color="danger")

        status = result.get("status")
        if status == "INSUFFICIENT_DATA":
            return dbc.Alert(
                f"⚠️ Not enough bars: {result.get('error')}. Try a wider date range.",
                color="warning",
            )
        if status != "SUCCESS":
            return dbc.Alert(
                f"Backtest failed — {result.get('error', status)}", color="danger"
            )

        return _render_results(result, symbol, strategy, start_date, end_date)


# ── Private rendering ───────────────────────────────────────────────────────

_STRATEGY_LABELS = {
    "vwap":           "🎯 VWAP",
    "orb":            "🔓 Opening Range Breakout",
    "momentum":       "🚀 Momentum/Gap-and-Go",
    "mean_reversion": "↩️ Mean Reversion (BB)",
    "fibonacci":      "📐 Fibonacci Retracement",
    "breakout":       "💥 Breakout",
}


def _render_results(result, symbol, strategy, start_date, end_date):
    m = result.get("metrics", {})
    trades = result.get("trades", [])
    equity = result.get("equity_curve", [])

    net   = m.get("net_profit", 0)
    ret   = m.get("return_pct", 0)
    bah   = m.get("buy_and_hold_return_pct")
    sharpe   = m.get("sharpe_ratio")
    drawdown = m.get("max_drawdown")

    label = _STRATEGY_LABELS.get(strategy, strategy)

    rows = [
        dbc.Alert(
            f"✅ Backtest complete — {symbol} • {label} • {start_date} → {end_date} "
            f"• {len(result.get('trades', []))} bars",
            color="success",
            style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem"},
        ),
        # Metrics row 1
        dbc.Row([
            dbc.Col(_kv("Net Profit",   format_price(net),
                        "positive" if net >= 0 else "negative"), md=3),
            dbc.Col(_kv("Return",       f"{ret:+.1f}%",
                        "positive" if ret >= 0 else "negative"), md=3),
            dbc.Col(_kv("Win Rate",     f"{m.get('win_rate', 0):.1f}%"),  md=3),
            dbc.Col(_kv("Total Trades", str(m.get("total_trades", 0))),   md=3),
        ], className="g-3 mb-2"),
        # Metrics row 2
        dbc.Row([
            dbc.Col(_kv("Profit Factor",  f"{m.get('profit_factor', 0):.2f}"),          md=3),
            dbc.Col(_kv("Avg Return",     format_percentage(m.get("avg_return", 0))),   md=3),
            dbc.Col(_kv("Sharpe Ratio",   f"{sharpe:.2f}" if sharpe is not None else "—"), md=3),
            dbc.Col(_kv("Max Drawdown",   f"{drawdown:.1f}%" if drawdown is not None else "—"), md=3),
        ], className="g-3 mb-3"),
    ]

    # Buy-and-hold comparison badge
    if bah is not None:
        vs = ret - bah
        rows.append(
            dbc.Alert(
                f"Strategy {'+' if vs >= 0 else ''}{vs:.1f}% vs Buy & Hold ({bah:+.1f}%)",
                color="success" if vs >= 0 else "secondary",
                style={"padding": "0.4rem 0.75rem", "fontSize": "0.82rem",
                       "marginBottom": "0.75rem"},
            )
        )

    # Equity curve
    if equity:
        df  = pd.DataFrame(equity)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["balance"],
            mode="lines", name="Portfolio",
            line=dict(color="#4fc3f7", width=2),
            fill="tozeroy", fillcolor="rgba(79,195,247,0.08)",
            hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
        ))
        fig.update_layout(
            title=f"{symbol} — {label}",
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font_color="#e0e0e0",
            margin=dict(l=0, r=0, t=36, b=0), height=320,
            xaxis=dict(gridcolor="#1e2536"),
            yaxis=dict(gridcolor="#1e2536", tickprefix="$", autorange=True),
            hovermode="x unified",
        )
        rows.append(
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": True,
                        "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
                style={"marginBottom": "1rem"},
            )
        )

    # Trades table
    if trades:
        trade_rows = []
        for t in trades:
            trade_rows.append({
                "Entry":    str(getattr(t, "entry_date", "—")),
                "Exit":     str(getattr(t, "exit_date",  "—")),
                "Entry $":  format_price(getattr(t, "entry_price", 0)),
                "Exit $":   format_price(getattr(t, "exit_price",  0)),
                "Return":   format_percentage(getattr(t, "return_pct", 0)),
                "P/L":      format_price(getattr(t, "profit_loss", 0)),
            })
        from dash import dash_table
        rows.append(
            html.Div([
                html.H6(f"📋 Trade History ({len(trades)} trades)",
                        style={"color": "#e0e0e0", "marginBottom": "0.5rem"}),
                dash_table.DataTable(
                    data=trade_rows,
                    columns=[{"name": c, "id": c} for c in trade_rows[0]],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "backgroundColor": "#161b27", "color": "#e0e0e0",
                        "border": "1px solid #2a2f3e", "padding": "5px 10px",
                        "fontSize": "0.82rem",
                    },
                    style_header={
                        "backgroundColor": "#1e2536", "fontWeight": "bold",
                        "border": "1px solid #2a2f3e",
                    },
                    page_size=15,
                    sort_action="native",
                ),
            ])
        )

    return html.Div(rows)


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
