"""Trading Signals – Dash component."""

import dash
from dash import Input, Output, State, dcc, html, dash_table
import dash_bootstrap_components as dbc

from services.strategies import DAY_TRADING_STRATEGIES, SWING_TRADING_STRATEGIES
from utils.helpers import (
    format_price,
    format_percentage,
    get_signal_emoji,
    calculate_risk_reward_ratio,
)

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
        dcc.Store(id="ts-signals-store"),
        dcc.Store(id="ts-watchlist-store", data=watchlist),

        dbc.Row([
            dbc.Col([
                dbc.Label("Strategy Type"),
                dbc.RadioItems(
                    id="ts-strat-type",
                    options=[
                        {"label": "Swing Trading", "value": "swing"},
                        {"label": "Day Trading",   "value": "day"},
                    ],
                    value="swing",
                    inline=True,
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("Strategy"),
                dcc.Dropdown(
                    id="ts-strategy",
                    options=[{"label": _LABELS.get(k, k), "value": k} for k in _SWING_KEYS],
                    value=_SWING_KEYS[0] if _SWING_KEYS else None,
                    clearable=False,
                    style={"color": "#000"},
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("Scope"),
                dbc.Switch(
                    id="ts-portfolio-only",
                    label="Portfolio symbols only",
                    value=False,
                ),
            ], md=4),
        ], className="g-3 mb-3"),

        dbc.Button(
            "🔍 Generate Signals",
            id="ts-run-btn",
            color="primary",
            className="mb-3 w-100",
        ),

        dbc.Spinner(html.Div(id="ts-body"), color="primary"),

        html.Hr(),
        html.H6("📜 Signal History", style={"marginBottom": "0.5rem"}),
        dcc.Dropdown(
            id="ts-history-limit",
            options=[{"label": f"{n} signals", "value": n} for n in [10, 20, 50]],
            value=20,
            clearable=False,
            style={"color": "#000", "width": "200px"},
        ),
        html.Div(id="ts-history", style={"marginTop": "0.75rem"}),
    ])


def register_callbacks(app, services):

    @app.callback(
        Output("ts-strategy", "options"),
        Output("ts-strategy", "value"),
        Input("ts-strat-type", "value"),
    )
    def _swap_strategies(strat_type):
        if strat_type == "day":
            opts = [{"label": _LABELS.get(k, k), "value": k} for k in _DAY_KEYS]
            return opts, (_DAY_KEYS[0] if _DAY_KEYS else None)
        opts = [{"label": _LABELS.get(k, k), "value": k} for k in _SWING_KEYS]
        return opts, (_SWING_KEYS[0] if _SWING_KEYS else None)

    @app.callback(
        Output("ts-body", "children"),
        Input("ts-run-btn", "n_clicks"),
        State("ts-strategy",       "value"),
        State("ts-portfolio-only", "value"),
        State("ts-watchlist-store", "data"),
        prevent_initial_call=True,
    )
    def _generate(_, strategy, portfolio_only, watchlist):
        watchlist = watchlist or []
        if portfolio_only:
            symbols = services["portfolio"].get_portfolio_symbols()
            if not symbols:
                return dbc.Alert("Your portfolio is empty.", color="info")
        else:
            symbols = watchlist
            if not symbols:
                return dbc.Alert("Add stocks to your watchlist first.", color="info")

        try:
            signals = services["strategy"].get_signals_for_multiple_stocks(
                symbols, strategy_name=strategy
            )
        except Exception as e:
            return dbc.Alert(f"Error generating signals: {e}", color="danger")

        if not signals:
            return dbc.Alert("No signals returned.", color="warning")

        portfolio_positions = {
            p["symbol"]: p
            for p in services["portfolio"].get_all_positions()
        }
        top = services["strategy"].filter_top_opportunities(signals)

        top_cards = []
        for sig in top:
            emoji = get_signal_emoji(sig.signal.value)
            in_port = sig.symbol in portfolio_positions
            rr = calculate_risk_reward_ratio(
                sig.entry_price, sig.target_price, sig.stop_loss
            )
            badge = dbc.Badge("💼 In Portfolio", color="info",
                              className="ms-2") if in_port else ""
            color = (
                "success" if sig.signal.value == "BUY"
                else "danger" if sig.signal.value == "SELL"
                else "secondary"
            )
            top_cards.append(dbc.Card([
                dbc.CardHeader(html.Span([
                    html.Strong(f"{emoji} {sig.signal.value} — {sig.symbol}"),
                    badge,
                ])),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(_kv("Entry",      format_price(sig.entry_price)),  md=3),
                        dbc.Col(_kv("Target",     format_price(sig.target_price)), md=3),
                        dbc.Col(_kv("Stop Loss",  format_price(sig.stop_loss)),    md=3),
                        dbc.Col(_kv("Confidence", f"{sig.confidence:.0f}%"),       md=3),
                    ], className="g-3 mb-2"),
                    html.Small([
                        html.Strong("Holding: "), sig.holding_period, "  |  ",
                        html.Strong("R/R: "), f"1:{rr:.2f}",
                    ], style={"color": "#888"}),
                    dbc.Alert(sig.reasoning, color=color,
                              style={"marginTop": "0.5rem", "padding": "0.4rem 0.75rem",
                                     "fontSize": "0.85rem"}),
                ]),
            ], style={"backgroundColor": "#161b27", "border": "1px solid #2a2f3e",
                      "marginBottom": "0.75rem"}))

        # All-signals table
        rows = [
            {
                "Symbol":     ("💼 " if sym in portfolio_positions else "") + sym,
                "Signal":     f"{get_signal_emoji(sig.signal.value)} {sig.signal.value}",
                "Confidence": f"{sig.confidence:.0f}%",
                "Entry":      format_price(sig.entry_price),
                "Target":     format_price(sig.target_price),
                "Stop Loss":  format_price(sig.stop_loss),
                "Holding":    sig.holding_period,
            }
            for sym, sig in signals.items()
        ]

        tbl = dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0]],
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell={
                "backgroundColor": "#161b27", "color": "#e0e0e0",
                "border": "1px solid #2a2f3e", "padding": "6px 12px",
                "fontSize": "0.82rem",
            },
            style_header={
                "backgroundColor": "#1e2536", "fontWeight": "bold",
                "border": "1px solid #2a2f3e",
            },
        )

        return html.Div([
            html.H6("🌟 Top Opportunities", style={"marginBottom": "0.75rem"}),
            *top_cards,
            html.H6("📊 All Signals", style={"margin": "1.5rem 0 0.5rem"}),
            tbl,
        ])

    @app.callback(
        Output("ts-history", "children"),
        Input("ts-history-limit", "value"),
        Input("ts-run-btn", "n_clicks"),
    )
    def _history(limit, _):
        history = services["portfolio"].get_signals(limit=limit or 20)
        if not history:
            return dbc.Alert("No signal history yet. Generate signals to track them here.",
                             color="secondary")
        rows = [
            {
                "Date":       h["signal_date"],
                "Symbol":     h["symbol"],
                "Signal":     f"{get_signal_emoji(h['signal_type'])} {h['signal_type']}",
                "Entry":      format_price(h["entry_price"]),
                "Target":     format_price(h["target_price"]),
                "Confidence": f"{h['confidence']:.0f}%",
                "Status":     h["status"],
                "P/L":        format_percentage(h["profit_loss"]) if h.get("profit_loss") else "—",
            }
            for h in history
        ]
        return dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0]],
            style_table={"overflowX": "auto"},
            style_cell={
                "backgroundColor": "#161b27", "color": "#e0e0e0",
                "border": "1px solid #2a2f3e", "padding": "6px 12px",
                "fontSize": "0.82rem",
            },
            style_header={
                "backgroundColor": "#1e2536", "fontWeight": "bold",
                "border": "1px solid #2a2f3e",
            },
            page_size=20,
        )


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
