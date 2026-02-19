"""Portfolio Management – Dash component."""

from datetime import datetime
from dash import Input, Output, State, dcc, html, dash_table, ALL
import dash
import dash_bootstrap_components as dbc

from utils.helpers import format_price, format_percentage


def layout(services) -> html.Div:
    return html.Div([
        dcc.Store(id="pm-refresh-signal", data=0),

        dbc.Tabs(id="pm-tabs", active_tab="tab-holdings", children=[

            # ── Holdings ──────────────────────────────────────────────────
            dbc.Tab(label="📋 Holdings", tab_id="tab-holdings", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    _add_position_form(),
                    html.Hr(),
                    dbc.Spinner(html.Div(id="pm-holdings-body"), color="primary"),
                ]),
            ]),

            # ── Watchlist ─────────────────────────────────────────────────
            dbc.Tab(label="👁️ Watchlist", tab_id="tab-watchlist", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    dbc.Spinner(html.Div(id="pm-watchlist-body"), color="primary"),
                ]),
            ]),

            # ── Transaction History ────────────────────────────────────────
            dbc.Tab(label="📜 Transaction History", tab_id="tab-history", children=[
                html.Div(style={"padding": "1rem 0"}, children=[
                    dbc.Spinner(html.Div(id="pm-history-body"), color="primary"),
                ]),
            ]),
        ]),
    ])


def _add_position_form() -> html.Div:
    return dbc.Card([
        dbc.CardHeader(
            dbc.Button(
                "➕ Add New Position",
                id="pm-form-toggle",
                color="link",
                style={"color": "#4fc3f7", "textDecoration": "none", "fontWeight": "bold"},
            )
        ),
        dbc.Collapse(
            id="pm-form-collapse",
            is_open=False,
            children=[
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Ticker Symbol"),
                            dbc.Input(id="pm-add-symbol", placeholder="e.g. AAPL",
                                      style={"backgroundColor": "#161b27", "color": "#e0e0e0",
                                             "borderColor": "#2a2f3e"}),
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Shares"),
                            dbc.Input(id="pm-add-shares", type="number",
                                      min=0.01, step=0.01, value=1.0,
                                      style={"backgroundColor": "#161b27", "color": "#e0e0e0",
                                             "borderColor": "#2a2f3e"}),
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Purchase Price ($)"),
                            dbc.Input(id="pm-add-price", type="number",
                                      min=0.01, step=0.01, value=100.0,
                                      style={"backgroundColor": "#161b27", "color": "#e0e0e0",
                                             "borderColor": "#2a2f3e"}),
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Purchase Date"),
                            dbc.Input(id="pm-add-date", type="date",
                                      value=datetime.today().strftime("%Y-%m-%d"),
                                      style={"backgroundColor": "#161b27", "color": "#e0e0e0",
                                             "borderColor": "#2a2f3e"}),
                        ], md=2),
                        dbc.Col([
                            dbc.Label("Notes"),
                            dbc.Input(id="pm-add-notes", placeholder="optional",
                                      style={"backgroundColor": "#161b27", "color": "#e0e0e0",
                                             "borderColor": "#2a2f3e"}),
                        ], md=3),
                    ], className="g-3 mb-3"),
                    dbc.Button("💾 Add to Portfolio", id="pm-add-btn",
                               color="primary", className="w-100"),
                    html.Div(id="pm-add-feedback", style={"marginTop": "0.5rem"}),
                ]),
            ],
        ),
    ], style={"backgroundColor": "#161b27", "border": "1px solid #2a2f3e",
              "marginBottom": "1rem"})


def register_callbacks(app, services):

    @app.callback(
        Output("pm-form-collapse", "is_open"),
        Input("pm-form-toggle", "n_clicks"),
        State("pm-form-collapse", "is_open"),
        prevent_initial_call=True,
    )
    def _toggle_form(_, is_open):
        return not is_open

    @app.callback(
        Output("pm-add-feedback", "children"),
        Output("pm-refresh-signal", "data"),
        Input("pm-add-btn", "n_clicks"),
        State("pm-add-symbol", "value"),
        State("pm-add-shares", "value"),
        State("pm-add-price",  "value"),
        State("pm-add-date",   "value"),
        State("pm-add-notes",  "value"),
        State("pm-refresh-signal", "data"),
        prevent_initial_call=True,
    )
    def _add_position(_, symbol, shares, price, date_str, notes, rev):
        if not symbol:
            return dbc.Alert("Enter a ticker symbol.", color="warning"), rev
        try:
            services["portfolio"].add_position(
                symbol.strip().upper(),
                float(shares or 1),
                float(price or 0),
                date_str or datetime.today().strftime("%Y-%m-%d"),
                notes or "",
            )
            services["portfolio"].add_to_watchlist(symbol.strip().upper())
        except Exception as e:
            return dbc.Alert(f"Error: {e}", color="danger"), rev
        return (
            dbc.Alert(f"✅ Added {shares} shares of {symbol.upper()} at ${price:.2f}",
                      color="success",
                      style={"padding": "0.4rem 0.75rem", "fontSize": "0.85rem"}),
            (rev or 0) + 1,
        )

    @app.callback(
        Output("pm-holdings-body", "children"),
        Input("pm-refresh-signal", "data"),
        Input("page-refresh-interval", "n_intervals"),
    )
    def _holdings(_, __):
        positions = services["portfolio"].get_all_positions()
        if not positions:
            return dbc.Alert(
                "📭 Your portfolio is empty. Add your first position above!",
                color="info",
            )

        symbols = [p["symbol"] for p in positions]
        try:
            stocks_data    = services["market"].get_multiple_stocks(symbols)
            current_prices = {sym: s.current_price for sym, s in stocks_data.items()}
        except Exception:
            current_prices = {}

        summary = services["portfolio"].get_portfolio_summary(current_prices)

        summary_row = dbc.Row([
            dbc.Col(_kv("Total Invested", format_price(summary["total_cost"])),            md=3),
            dbc.Col(_kv("Current Value",  format_price(summary["total_current_value"])),   md=3),
            dbc.Col(_kv("Total P/L",      format_price(summary["total_profit_loss"]),
                        "positive" if summary["total_profit_loss"] >= 0 else "negative"), md=3),
            dbc.Col(_kv("Positions",      str(summary["position_count"])),                 md=3),
        ], className="g-3 mb-3")

        rows = [
            {
                "Symbol":    pos["symbol"],
                "Shares":    str(pos["shares"]),
                "Avg Price": format_price(pos["avg_buy_price"]),
                "Current":   format_price(pos.get("current_price", 0)),
                "Cost":      format_price(pos["cost_basis"]),
                "Value":     format_price(pos.get("current_value", 0)),
                "P/L":       format_price(pos.get("profit_loss", 0)),
                "P/L %":     format_percentage(pos.get("profit_loss_pct", 0)),
            }
            for pos in summary.get("positions", [])
        ]

        tbl = html.Div()
        if rows:
            tbl = dash_table.DataTable(
                data=rows,
                columns=[{"name": c, "id": c} for c in rows[0]],
                style_table={"overflowX": "auto"},
                style_cell={
                    "backgroundColor": "#161b27", "color": "#e0e0e0",
                    "border": "1px solid #2a2f3e", "padding": "6px 12px",
                    "fontSize": "0.85rem",
                },
                style_header={
                    "backgroundColor": "#1e2536", "fontWeight": "bold",
                    "border": "1px solid #2a2f3e",
                },
                sort_action="native",
            )

        return html.Div([summary_row, tbl])

    @app.callback(
        Output("pm-watchlist-body", "children"),
        Input("pm-refresh-signal", "data"),
    )
    def _watchlist_tab(_):
        wl = services["portfolio"].get_watchlist()
        if not wl:
            return dbc.Alert("Your watchlist is empty. Add stocks via the sidebar.", color="info")
        try:
            stocks_data = services["market"].get_multiple_stocks(wl)
        except Exception:
            stocks_data = {}

        rows = []
        for sym in wl:
            s = stocks_data.get(sym)
            rows.append({
                "Symbol":   sym,
                "Price":    format_price(s.current_price) if s else "—",
                "Change %": f"{s.change_percent:+.2f}%" if s else "—",
                "Volume":   str(s.volume) if s else "—",
            })

        return dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0]],
            style_table={"overflowX": "auto"},
            style_cell={
                "backgroundColor": "#161b27", "color": "#e0e0e0",
                "border": "1px solid #2a2f3e", "padding": "6px 12px",
                "fontSize": "0.85rem",
            },
            style_header={
                "backgroundColor": "#1e2536", "fontWeight": "bold",
                "border": "1px solid #2a2f3e",
            },
            sort_action="native",
        )

    @app.callback(
        Output("pm-history-body", "children"),
        Input("pm-refresh-signal", "data"),
    )
    def _history(_):
        txns = services["portfolio"].get_transactions()
        if not txns:
            return dbc.Alert("No transaction history yet.", color="info")
        return dash_table.DataTable(
            data=txns,
            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in txns[0]],
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
            sort_action="native",
            page_size=20,
        )


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
