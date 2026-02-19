"""eSignal – Plotly Dash dashboard entry point."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, dcc, html

from config.settings import settings
from services.backtest_service import BacktestService
from services.gemini_service import GeminiService
from services.market_data_service import MarketDataService
from services.portfolio_service import PortfolioDB
from services.trading_strategy_service import TradingStrategyService

# ── Page-component imports ────────────────────────────────────────────────────
from dashboard.components.market_overview      import layout as market_overview_layout,   register_callbacks as market_overview_callbacks
from dashboard.components.trading_signals      import layout as trading_signals_layout,   register_callbacks as trading_signals_callbacks
from dashboard.components.day_trading_page     import layout as day_trading_layout,       register_callbacks as day_trading_callbacks
from dashboard.components.swing_trading_page   import layout as swing_trading_layout,     register_callbacks as swing_trading_callbacks
from dashboard.components.portfolio_management import layout as portfolio_layout,         register_callbacks as portfolio_callbacks
from dashboard.components.news_analysis        import layout as news_layout,              register_callbacks as news_callbacks
from dashboard.components.backtest_page        import layout as backtest_layout,          register_callbacks as backtest_callbacks
from dashboard.components.charts               import layout as charts_layout,            register_callbacks as charts_callbacks
from dashboard.components.news_controller_page import layout as nc_layout,               register_callbacks as nc_callbacks
from dashboard.components.beginner_guide_page  import layout as guide_layout,            register_callbacks as guide_callbacks

# ── Services (module-level singletons) ───────────────────────────────────────
_market    = MarketDataService()
_gemini    = GeminiService()
_strategy  = TradingStrategyService(market_service=_market, gemini_service=_gemini)
_portfolio = PortfolioDB()
_backtest  = BacktestService()

SERVICES = {
    "market":    _market,
    "gemini":    _gemini,
    "strategy":  _strategy,
    "portfolio": _portfolio,
    "backtest":  _backtest,
}

# Seed default watchlist tickers on first run
_portfolio.seed_watchlist_defaults(settings.DEFAULT_TICKERS)

# ── Nav structure ─────────────────────────────────────────────────────────────
NAV_GROUPS = {
    "MARKET": {
        "market-overview": ("📊", "Market Overview"),
        "detailed-charts": ("📈", "Charts"),
    },
    "TRADING": {
        "trading-signals": ("🎯", "Signals"),
        "day-trading":     ("⚡", "Day Trading"),
        "swing-trading":   ("🌊", "Swing Trading"),
    },
    "RESEARCH": {
        "ai-news":         ("🤖", "AI News"),
        "news-controller": ("🎛️",  "News Settings"),
    },
    "ACCOUNT": {
        "portfolio":       ("💼", "Portfolio"),
        "backtest":        ("🧪", "Backtest"),
    },
    "HELP": {
        "beginners-guide": ("📚", "Beginner's Guide"),
    },
}

PAGE_TITLES = {
    page_id: label
    for pages in NAV_GROUPS.values()
    for page_id, (_, label) in pages.items()
}

ICON_MAP = {
    page_id: icon
    for pages in NAV_GROUPS.values()
    for page_id, (icon, _) in pages.items()
}

# ── App ───────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="eSignal Dashboard",
)
server = app.server  # expose Flask for gunicorn / production


# ── Sidebar builder ───────────────────────────────────────────────────────────
def _nav_items() -> list:
    items = []
    for group_label, pages in NAV_GROUPS.items():
        items.append(html.P(group_label, className="nav-section-label"))
        for page_id, (icon, label) in pages.items():
            items.append(
                html.Button(
                    f"{icon}  {label}",
                    id={"type": "nav-btn", "page": page_id},
                    className="nav-btn",
                    n_clicks=0,
                )
            )
    return items


def _sidebar() -> html.Div:
    initial_watchlist = _portfolio.get_watchlist()
    initial_symbol    = initial_watchlist[0] if initial_watchlist else "AAPL"

    return html.Div(
        id="sidebar",
        children=[
            html.Div("📈 eSignal", className="brand"),
            html.Div(id="market-status-badge", className="market-status"),
            html.Hr(style={"borderColor": "#2a2f3e", "margin": "0 0 0.5rem 0"}),
            *_nav_items(),
            html.Hr(style={"borderColor": "#2a2f3e", "margin": "1rem 0 0.5rem 0"}),
            html.P("WATCHLIST", className="nav-section-label"),
            dbc.InputGroup(
                [
                    dbc.Input(
                        id="watchlist-add-input",
                        placeholder="e.g. AAPL",
                        size="sm",
                        style={
                            "backgroundColor": "#0f1117",
                            "color": "#e0e0e0",
                            "borderColor": "#2a2f3e",
                        },
                    ),
                    dbc.Button(
                        "＋", id="watchlist-add-btn",
                        color="primary", size="sm", n_clicks=0,
                    ),
                ],
                size="sm",
                style={"padding": "0 0.5rem 0.5rem 0.5rem"},
            ),
            html.Div(id="watchlist-items"),
            # Stores & intervals
            dcc.Interval(id="market-status-interval", interval=30_000, n_intervals=0),
            dcc.Interval(
                id="page-refresh-interval",
                interval=settings.REFRESH_INTERVAL * 1000,
                n_intervals=0,
            ),
            dcc.Store(id="current-page",    data="market-overview", storage_type="session"),
            dcc.Store(id="selected-symbol", data=initial_symbol,    storage_type="session"),
            dcc.Store(id="watchlist-store", data=initial_watchlist, storage_type="session"),
        ],
    )


# ── Root layout ───────────────────────────────────────────────────────────────
app.layout = html.Div(
    [
        _sidebar(),
        html.Div(
            id="page-content",
            children=[
                html.Div(
                    id="topbar",
                    children=[
                        html.H2(id="page-title", children="📊 Market Overview"),
                        html.Div(id="gemini-status-badge"),
                    ],
                ),
                html.Div(id="page-body"),
                html.Div(
                    id="footer",
                    children=[
                        "⚠️ For educational purposes only. Not financial advice. ",
                        "Data: Yahoo Finance • AI: Google Gemini",
                    ],
                ),
            ],
        ),
    ]
)


# ── Router ────────────────────────────────────────────────────────────────────
@app.callback(
    Output("current-page", "data"),
    Input({"type": "nav-btn", "page": dash.ALL}, "n_clicks"),
    State("current-page", "data"),
    prevent_initial_call=True,
)
def _navigate(_n_clicks_list, current_page):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_page
    prop_id = ctx.triggered[0]["prop_id"]
    btn_id  = json.loads(prop_id.rsplit(".", 1)[0])
    return btn_id["page"]


@app.callback(
    Output("page-title", "children"),
    Output("page-body",  "children"),
    Input("current-page",    "data"),
    State("watchlist-store", "data"),
    State("selected-symbol", "data"),
)
def _render_page(page_id, watchlist, selected_symbol):
    watchlist       = watchlist or []
    selected_symbol = selected_symbol or (watchlist[0] if watchlist else "AAPL")
    icon  = ICON_MAP.get(page_id, "")
    title = PAGE_TITLES.get(page_id, page_id)

    page_map = {
        "market-overview": lambda: market_overview_layout(SERVICES, watchlist),
        "trading-signals": lambda: trading_signals_layout(SERVICES, watchlist),
        "day-trading":     lambda: day_trading_layout(SERVICES),
        "swing-trading":   lambda: swing_trading_layout(SERVICES),
        "portfolio":       lambda: portfolio_layout(SERVICES),
        "ai-news":         lambda: news_layout(SERVICES, watchlist),
        "backtest":        lambda: backtest_layout(SERVICES, watchlist),
        "beginners-guide": lambda: guide_layout(),
        "news-controller": lambda: nc_layout(SERVICES),
        "detailed-charts": lambda: charts_layout(SERVICES, watchlist),
    }

    body_fn = page_map.get(page_id)
    body = body_fn() if body_fn else html.P(
        f"Page '{page_id}' not found.", style={"color": "#888"}
    )

    return f"{icon}  {title}", body


# ── Market status ─────────────────────────────────────────────────────────────
@app.callback(
    Output("market-status-badge", "children"),
    Input("market-status-interval", "n_intervals"),
)
def _update_market_status(_):
    status = SERVICES["market"].get_market_status()
    dot    = "🟢" if status.get("is_open") else "🔴"
    state  = status.get("market_state", "UNKNOWN")
    return f"{dot} {state}"


# ── Gemini status ─────────────────────────────────────────────────────────────
@app.callback(
    Output("gemini-status-badge", "children"),
    Input("current-page", "data"),
)
def _gemini_badge(_):
    if not SERVICES["gemini"].is_available():
        return dbc.Alert(
            "⚠️ Gemini AI not configured — set GEMINI_API_KEY in .env",
            color="warning",
            style={"padding": "0.3rem 0.75rem", "fontSize": "0.8rem", "margin": 0},
        )
    return ""


# ── Watchlist: add ────────────────────────────────────────────────────────────
@app.callback(
    Output("watchlist-store",    "data"),
    Output("watchlist-add-input", "value"),
    Input("watchlist-add-btn", "n_clicks"),
    State("watchlist-add-input", "value"),
    prevent_initial_call=True,
)
def _add_to_watchlist(_, ticker):
    if not ticker:
        return SERVICES["portfolio"].get_watchlist(), ""
    SERVICES["portfolio"].add_to_watchlist(ticker.strip().upper())
    return SERVICES["portfolio"].get_watchlist(), ""


# ── Watchlist: render + select + remove ──────────────────────────────────────
@app.callback(
    Output("watchlist-items",   "children"),
    Output("selected-symbol",   "data"),
    Input("watchlist-store",    "data"),
    Input({"type": "wl-select", "ticker": dash.ALL}, "n_clicks"),
    Input({"type": "wl-remove", "ticker": dash.ALL}, "n_clicks"),
    State("selected-symbol",    "data"),
)
def _render_watchlist(watchlist, _sel, _rem, selected):
    ctx      = dash.callback_context
    watchlist = watchlist or []

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"]
        if "wl-remove" in prop_id:
            ticker = json.loads(prop_id.rsplit(".", 1)[0])["ticker"]
            SERVICES["portfolio"].remove_from_watchlist(ticker)
            watchlist = SERVICES["portfolio"].get_watchlist()
            if selected == ticker:
                selected = watchlist[0] if watchlist else "AAPL"
        elif "wl-select" in prop_id:
            selected = json.loads(prop_id.rsplit(".", 1)[0])["ticker"]

    items = []
    for t in watchlist:
        cls = "watchlist-item selected" if t == selected else "watchlist-item"
        items.append(
            html.Div(
                className=cls,
                children=[
                    html.Button(
                        t,
                        id={"type": "wl-select", "ticker": t},
                        n_clicks=0,
                        style={
                            "background": "none", "border": "none",
                            "color": "inherit",   "cursor": "pointer",
                            "fontSize": "0.82rem", "padding": 0,
                        },
                    ),
                    html.Button(
                        "✕",
                        id={"type": "wl-remove", "ticker": t},
                        className="watchlist-remove",
                        n_clicks=0,
                    ),
                ],
            )
        )
    return items, selected


# ── Register page-level callbacks ─────────────────────────────────────────────
market_overview_callbacks(app, SERVICES)
trading_signals_callbacks(app, SERVICES)
day_trading_callbacks(app, SERVICES)
swing_trading_callbacks(app, SERVICES)
portfolio_callbacks(app, SERVICES)
news_callbacks(app, SERVICES)
backtest_callbacks(app, SERVICES)
charts_callbacks(app, SERVICES)
nc_callbacks(app, SERVICES)
guide_callbacks(app, SERVICES)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
