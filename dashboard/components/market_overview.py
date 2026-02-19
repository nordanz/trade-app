"""Market Overview – Dash component."""

from dash import Input, Output, dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from utils.helpers import format_price, format_percentage, format_large_number


def layout(services, watchlist: list) -> html.Div:
    return html.Div([
        dcc.Store(id="mo-watchlist-store", data=watchlist),
        dbc.Spinner(html.Div(id="mo-body"), color="primary"),
    ])


def register_callbacks(app, services):

    @app.callback(
        Output("mo-body", "children"),
        Input("mo-watchlist-store", "data"),
        Input("page-refresh-interval", "n_intervals"),
    )
    def _refresh(watchlist, _):
        watchlist = watchlist or []
        if not watchlist:
            return dbc.Alert(
                "👆 Add stocks to your watchlist using the sidebar to get started.",
                color="info",
            )

        try:
            stocks_data = services["market"].get_multiple_stocks(watchlist)
        except Exception as e:
            return dbc.Alert(f"Error fetching market data: {e}", color="danger")

        if not stocks_data:
            return dbc.Alert(
                "Unable to fetch market data. Check your internet connection.",
                color="danger",
            )

        # Summary metrics
        total   = len(stocks_data)
        gainers = sum(1 for s in stocks_data.values() if s.change_percent > 0)
        losers  = sum(1 for s in stocks_data.values() if s.change_percent < 0)
        flat    = total - gainers - losers
        avg_chg = sum(s.change_percent for s in stocks_data.values()) / total

        summary_row = dbc.Row([
            dbc.Col(_kv("Tracked",     str(total)),              md=2),
            dbc.Col(_kv("🟢 Gainers",  str(gainers), "positive"), md=2),
            dbc.Col(_kv("🔴 Losers",   str(losers),  "negative"), md=2),
            dbc.Col(_kv("⬜ Flat",     str(flat)),               md=2),
            dbc.Col(_kv("Avg Change",  f"{avg_chg:+.2f}%",
                        "positive" if avg_chg >= 0 else "negative"), md=2),
        ], className="g-3 mb-3")

        # Summary table
        rows = [
            {
                "Symbol":     sym,
                "Price":      format_price(s.current_price),
                "Change %":   f"{s.change_percent:+.2f}%",
                "Volume":     format_large_number(s.volume) if s.volume else "—",
                "Market Cap": format_large_number(s.market_cap) if s.market_cap else "—",
                "P/E":        f"{s.pe_ratio:.1f}" if s.pe_ratio else "—",
            }
            for sym, s in stocks_data.items()
        ]

        table = dash_table.DataTable(
            data=rows,
            columns=[{"name": c, "id": c} for c in rows[0]],
            sort_action="native",
            style_table={"overflowX": "auto", "marginBottom": "1.5rem"},
            style_cell={
                "backgroundColor": "#161b27",
                "color":           "#e0e0e0",
                "border":          "1px solid #2a2f3e",
                "padding":         "8px 12px",
                "fontSize":        "0.85rem",
            },
            style_header={
                "backgroundColor": "#1e2536",
                "fontWeight":      "bold",
                "border":          "1px solid #2a2f3e",
            },
            style_data_conditional=[
                {"if": {"filter_query": '{Change %} contains "+"'},
                 "color": "#26a69a", "fontWeight": "bold"},
                {"if": {"filter_query": '{Change %} contains "-"'},
                 "color": "#ef5350", "fontWeight": "bold"},
            ],
        )

        # Detail cards
        cards = []
        for sym, stock in stocks_data.items():
            chg_color = "#26a69a" if stock.change_percent >= 0 else "#ef5350"
            cards.append(
                dbc.AccordionItem(
                    title=html.Span([
                        html.Span(f"{'▲' if stock.change_percent >= 0 else '▼'} ",
                                  style={"color": chg_color}),
                        html.Strong(sym),
                        f"  {format_price(stock.current_price)}",
                        html.Span(
                            f"  ({stock.change_percent:+.2f}%)",
                            style={"color": chg_color, "fontSize": "0.9rem"},
                        ),
                    ]),
                    children=[
                        dbc.Row([
                            dbc.Col(_kv("Price",      format_price(stock.current_price),
                                       "positive" if stock.change_percent >= 0 else "negative"), md=3),
                            dbc.Col(_kv("Volume",     format_large_number(stock.volume) if stock.volume else "—"), md=3),
                            dbc.Col(_kv("Market Cap", format_large_number(stock.market_cap) if stock.market_cap else "—"), md=3),
                            dbc.Col(_kv("P/E Ratio",  f"{stock.pe_ratio:.1f}" if stock.pe_ratio else "—"), md=3),
                        ], className="g-3"),
                        html.Div([
                            html.Span(
                                [html.Strong(key.upper() + ": "), format_price(val) + "  "],
                                style={"marginRight": "1rem", "fontSize": "0.82rem", "color": "#888"},
                            )
                            for key, val in (stock.moving_averages or {}).items() if val
                        ], style={"marginTop": "0.5rem"}),
                    ],
                )
            )

        detail_section = html.Div([
            html.H6("Stock Detail", style={"marginBottom": "0.75rem"}),
            dbc.Accordion(cards, start_collapsed=True),
        ])

        return html.Div([summary_row, table, detail_section])


def _kv(label, value, cls=""):
    return html.Div(className="metric-card", children=[
        html.Div(label, className="metric-label"),
        html.Div(value, className=f"metric-value {cls}"),
    ])
