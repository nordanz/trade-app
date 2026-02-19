"""Backtest – Dash component."""

from datetime import date, timedelta
from dash import Input, Output, State, dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from services.backtest_service import STRATEGY_MIN_BARS
from services.strategies import DAY_TRADING_STRATEGIES, SWING_TRADING_STRATEGIES
from utils.helpers import format_price, format_percentage

_LABELS = {
    "vwap":           "🎯 VWAP",
    "orb":            "🔓 Opening Range Breakout",
    "momentum":       "🚀 Momentum / Gap-and-Go",
    "mean_reversion": "↩️ Mean Reversion (BB)",
    "fibonacci":      "📐 Fibonacci Retracement",
    "breakout":       "💥 Breakout",
}
_DAY_KEYS   = list(DAY_TRADING_STRATEGIES.keys())
_SWING_KEYS = list(SWING_TRADING_STRATEGIES.keys())


def layout(services, watchlist: list) -> html.Div:
    sym_options = [{"label": s, "value": s} for s in (watchlist or ["AAPL"])]

    return html.Div([
        dcc.Store(id="bt-strat-type-store", data="swing"),
        dcc.Store(id="bt-strategy-store",   data=_SWING_KEYS[0] if _SWING_KEYS else ""),

        html.P(
            "Deep-dive a single strategy or compare all side-by-side. "
            "For quick backtests use the panel on Day / Swing Trading pages.",
            style={"color": "#888", "fontSize": "0.85rem", "marginBottom": "1rem"},
        ),

        dbc.RadioItems(
            id="bt-mode",
            options=[
                {"label": "Single Strategy",        "value": "single"},
                {"label": "Compare All Strategies", "value": "compare"},
            ],
            value="single",
            inline=True,
            style={"marginBottom": "1rem"},
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Symbol"),
                dcc.Dropdown(
                    id="bt-symbol",
                    options=sym_options,
                    value=sym_options[0]["value"] if sym_options else "AAPL",
                    clearable=False,
                    style={"color": "#000"},
                ),
                dbc.Input(
                    id="bt-custom-symbol",
                    placeholder="…or type a symbol",
                    className="mt-1",
                    style={
                        "backgroundColor": "#161b27",
                        "color":           "#e0e0e0",
                        "borderColor":     "#2a2f3e",
                        "fontSize":        "0.85rem",
                    },
                ),
            ], md=3),
            dbc.Col([
                dbc.Label("Start Date"),
                dbc.Input(
                    id="bt-start",
                    type="date",
                    value=(date.today() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    style={
                        "backgroundColor": "#161b27",
                        "color":           "#e0e0e0",
                        "borderColor":     "#2a2f3e",
                    },
                ),
                html.Small(id="bt-date-hint",
                           children="Swing: up to 1 year recommended",
                           style={"color": "#888", "fontSize": "0.75rem"}),
            ], md=2),
            dbc.Col([
                dbc.Label("End Date"),
                dbc.Input(
                    id="bt-end",
                    type="date",
                    value=date.today().strftime("%Y-%m-%d"),
                    style={
                        "backgroundColor": "#161b27",
                        "color":           "#e0e0e0",
                        "borderColor":     "#2a2f3e",
                    },
                ),
            ], md=2),
            dbc.Col([
                dbc.Label("Starting Capital ($)"),
                dbc.Input(
                    id="bt-cash",
                    type="number",
                    value=10_000,
                    min=1_000,
                    step=1_000,
                    style={
                        "backgroundColor": "#161b27",
                        "color":           "#e0e0e0",
                        "borderColor":     "#2a2f3e",
                    },
                ),
            ], md=2),
            dbc.Col([
                dbc.Label("News Sentiment"),
                dbc.Switch(
                    id="bt-sentiment",
                    value=False,
                    label="Include (needs NEWS_API_KEY)",
                ),
            ], md=3),
        ], className="g-3 mb-3"),

        html.Div(id="bt-single-inputs"),

        dbc.Button(
            "▶️ Run Backtest",
            id="bt-run-btn",
            color="primary",
            className="mb-3 w-100",
        ),

        dbc.Spinner(html.Div(id="bt-results"), color="primary"),
    ])


def register_callbacks(app, services):

    @app.callback(
        Output("bt-single-inputs", "children"),
        Input("bt-mode", "value"),
    )
    def _single_inputs(mode):
        if mode != "single":
            return ""
        swing_opts = [{"label": _LABELS.get(k, k), "value": k} for k in _SWING_KEYS]
        day_opts   = [{"label": _LABELS.get(k, k), "value": k} for k in _DAY_KEYS]
        return dbc.Row([
            dbc.Col([
                dbc.Label("Strategy Type"),
                dbc.RadioItems(
                    id="bt-strat-type",
                    options=[
                        {"label": "Swing", "value": "swing"},
                        {"label": "Day",   "value": "day"},
                    ],
                    value="swing",
                    inline=True,
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("Strategy"),
                dcc.Dropdown(
                    id="bt-strategy",
                    options=swing_opts,
                    value=_SWING_KEYS[0] if _SWING_KEYS else None,
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=4),
        ], className="g-3 mb-3")

    @app.callback(
        Output("bt-strategy", "options"),
        Output("bt-strategy", "value"),
        Input("bt-strat-type", "value"),
        prevent_initial_call=True,
    )
    def _swap_strategies(strat_type):
        if strat_type == "day":
            opts = [{"label": _LABELS.get(k, k), "value": k} for k in _DAY_KEYS]
            return opts, (_DAY_KEYS[0] if _DAY_KEYS else None)
        opts = [{"label": _LABELS.get(k, k), "value": k} for k in _SWING_KEYS]
        return opts, (_SWING_KEYS[0] if _SWING_KEYS else None)

    @app.callback(
        Output("bt-start", "value"),
        Output("bt-date-hint", "children"),
        Input("bt-strat-type", "value"),
        prevent_initial_call=True,
    )
    def _update_date_range(strat_type):
        # Day trading: last 30 days (intraday data limit)
        # Swing trading: last 365 days
        if strat_type == "day":
            return (
                (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "Day: max ~60 days for 5m data",
            )
        return (
            (date.today() - timedelta(days=365)).strftime("%Y-%m-%d"),
            "Swing: up to 1 year recommended",
        )

    @app.callback(
        Output("bt-strategy-store",   "data"),
        Output("bt-strat-type-store", "data"),
        Input("bt-strategy",   "value"),
        Input("bt-strat-type", "value"),
        prevent_initial_call=True,
    )
    def _sync_stores(strategy, strat_type):
        return strategy, strat_type

    @app.callback(
        Output("bt-results", "children"),
        Input("bt-run-btn", "n_clicks"),
        State("bt-mode",            "value"),
        State("bt-symbol",          "value"),
        State("bt-custom-symbol",   "value"),
        State("bt-start",           "value"),
        State("bt-end",             "value"),
        State("bt-cash",            "value"),
        State("bt-sentiment",       "value"),
        State("bt-strategy-store",  "data"),
        State("bt-strat-type-store","data"),
        prevent_initial_call=True,
    )
    def _run(_, mode, symbol, custom, start_str, end_str, cash, sentiment,
             strategy_store, strat_type_store):
        symbol = (custom.strip().upper() if custom else symbol) or "AAPL"
        # Use stored strategy (set when user picks from dropdown); fall back to default
        strategy_name = strategy_store or (_SWING_KEYS[0] if _SWING_KEYS else "mean_reversion")
        is_intraday   = (strat_type_store == "day")

        start = date.fromisoformat(start_str)
        end   = date.fromisoformat(end_str)
        fetch_end = end + timedelta(days=1)

        interval = "5m" if is_intraday else "1d"
        hist = services["market"].get_historical_data(
            symbol,
            interval=interval,
            start=start.strftime("%Y-%m-%d"),
            end=fetch_end.strftime("%Y-%m-%d"),
        )

        if hist is None or hist.empty:
            return dbc.Alert(
                f"No data returned for {symbol} in the selected date range.",
                color="danger",
            )

        if mode == "single":
            result = services["backtest"].run_backtest(
                ohlc_data=hist,
                symbol=symbol,
                strategy_name=strategy_name,
                cash=float(cash or 10_000),
                use_sentiment=bool(sentiment),
            )
            return _render_single(result, hist, symbol, strategy_name)

        compare = services["backtest"].compare_strategies(
            ohlc_data=hist,
            symbol=symbol,
            cash=float(cash or 10_000),
            use_sentiment=bool(sentiment),
        )
        return _render_compare(compare)


def _render_single(result, hist, symbol, strategy_name):
    status = result.get("status", "")
    if status == "INSUFFICIENT_DATA":
        min_bars = STRATEGY_MIN_BARS.get(strategy_name, 30)
        return dbc.Alert(
            f"Not enough bars — {strategy_name} needs {min_bars}, got {len(hist)}.",
            color="warning",
        )
    if status != "SUCCESS":
        return dbc.Alert(
            f"Backtest error: {result.get('error', status)}",
            color="danger",
        )

    m   = result.get("metrics", {})
    net = m.get("net_profit", 0)

    metrics_row = dbc.Row([
        dbc.Col(_kv("Net Profit",    format_price(net),
                    "positive" if net >= 0 else "negative"), md=3),
        dbc.Col(_kv("Win Rate",
                    f"{m.get('win_rate', 0):.1f}% ({m.get('total_trades', 0)} trades)"), md=3),
        dbc.Col(_kv("Profit Factor", f"{m.get('profit_factor', 0):.2f}"),  md=3),
        dbc.Col(_kv("Max Drawdown",  f"{m.get('max_drawdown', 0):.1f}%"),  md=3),
    ], className="g-3 mb-3")

    equity = result.get("equity_curve", [])
    chart  = html.Div()
    if equity:
        dates  = [e["date"]    for e in equity]
        values = [e["balance"] for e in equity]
        fig = go.Figure(
            go.Scatter(
                x=dates, y=values,
                fill="tozeroy",
                fillcolor="rgba(79,195,247,0.08)",
                line=dict(color="#4fc3f7", width=2),
                hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"{symbol} — {_LABELS.get(strategy_name, strategy_name)} Equity Curve",
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font_color="#e0e0e0",
            margin=dict(l=0, r=0, t=40, b=0),
            height=360,
            xaxis=dict(gridcolor="#1e2536"),
            yaxis=dict(gridcolor="#1e2536", tickprefix="$", autorange=True),
            hovermode="x unified",
        )
        chart = dcc.Graph(
            figure=fig,
            config={"displayModeBar": True, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
        )

    trades = result.get("trades", [])
    trade_tbl = html.Div()
    if trades:
        rows = [
            {
                "Entry Date":  getattr(t, "entry_date",  "—"),
                "Exit Date":   getattr(t, "exit_date",   "—"),
                "Entry $":     format_price(getattr(t, "entry_price", 0)),
                "Exit $":      format_price(getattr(t, "exit_price",  0)),
                "Shares":      f"{getattr(t, 'shares', 0):.2f}",
                "P/L":         format_price(getattr(t, "profit_loss", 0)),
                "Return":      format_percentage(getattr(t, "return_pct", 0)),
            }
            for t in trades
        ]
        trade_tbl = dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0]],
            style_table={"overflowX": "auto"},
            style_cell={
                "backgroundColor": "#161b27",
                "color":           "#e0e0e0",
                "border":          "1px solid #2a2f3e",
                "padding":         "6px 12px",
                "fontSize":        "0.82rem",
            },
            style_header={
                "backgroundColor": "#1e2536",
                "fontWeight":      "bold",
                "border":          "1px solid #2a2f3e",
            },
            page_size=15,
            sort_action="native",
        )

    return html.Div([
        dbc.Alert(
            "✅ Backtest complete",
            color="success",
            style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem"},
        ),
        metrics_row,
        chart,
        html.H6("Trades", style={"marginTop": "1.5rem", "marginBottom": "0.5rem"}),
        trade_tbl,
    ])


def _render_compare(compare):
    if not compare or compare.get("status") != "SUCCESS":
        err = compare.get("error", "Unknown error") if compare else "No results"
        return dbc.Alert(f"Comparison failed: {err}", color="warning")

    summary  = compare.get("summary", {})
    ranking  = summary.get("ranking", [])
    failed   = compare.get("results", [])
    failed   = [r for r in failed if r.get("status") != "SUCCESS"]

    if not ranking:
        return dbc.Alert(
            "No strategies produced results for the selected date range. "
            "Try a wider range or a different symbol.",
            color="warning",
        )

    best = summary.get("best_strategy")
    children = []

    # Summary banner
    children.append(dbc.Alert(
        [
            html.Strong(f"✅ {summary.get('successful_runs', 0)}/{summary.get('total_strategies', 0)} strategies ran successfully.  "),
            f"Best: {_LABELS.get(best, best)}  •  "
            f"Net profit: {format_price(summary.get('best_net_profit', 0))}",
        ],
        color="success",
        style={"padding": "0.5rem 0.75rem", "fontSize": "0.85rem", "marginBottom": "1rem"},
    ))

    # Ranking table
    rows = [
        {
            "Rank":          f"#{r['rank']}",
            "Strategy":      _LABELS.get(r.get("strategy", ""), r.get("strategy", "")),
            "Net Profit":    format_price(r.get("net_profit", 0)),
            "Win Rate":      f"{r.get('win_rate', 0):.1f}%",
            "Trades":        str(r.get("total_trades", 0)),
            "Sharpe":        f"{r.get('sharpe_ratio', 0):.2f}" if r.get("sharpe_ratio") else "—",
            "Max Drawdown":  f"{r.get('max_drawdown', 0):.1f}%" if r.get("max_drawdown") else "—",
        }
        for r in ranking
    ]

    children.append(dash_table.DataTable(
        data=rows,
        columns=[{"name": c, "id": c} for c in rows[0]],
        style_table={"overflowX": "auto"},
        style_cell={
            "backgroundColor": "#161b27",
            "color":           "#e0e0e0",
            "border":          "1px solid #2a2f3e",
            "padding":         "6px 12px",
            "fontSize":        "0.85rem",
        },
        style_header={
            "backgroundColor": "#1e2536",
            "fontWeight":      "bold",
            "border":          "1px solid #2a2f3e",
        },
        sort_action="native",
    ))

    # Failed strategies (if any)
    if failed:
        children.append(html.Div([
            html.H6("⚠️ Failed Strategies",
                    style={"color": "#888", "marginTop": "1rem", "marginBottom": "0.4rem",
                           "fontSize": "0.85rem"}),
            *[
                dbc.Alert(
                    f"{_LABELS.get(r.get('strategy', ''), r.get('strategy', ''))}: "
                    f"{r.get('error', r.get('status', 'unknown error'))}",
                    color="secondary",
                    style={"padding": "0.3rem 0.75rem", "fontSize": "0.8rem",
                           "marginBottom": "0.3rem"},
                )
                for r in failed
            ],
        ]))

    return html.Div(children)


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
