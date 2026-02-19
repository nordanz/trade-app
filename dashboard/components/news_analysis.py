"""News Analysis – Dash component."""

from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc

from utils.helpers import get_sentiment_emoji


def layout(services, watchlist=None) -> html.Div:
    return html.Div([
        dcc.Store(id="na-watchlist-store", data=watchlist or []),

        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "🔄 Fetch AI Analysis",
                    id="na-fetch-btn",
                    color="primary",
                    className="w-100",
                    style={"marginBottom": "1rem"},
                ),
            ], md=4),
            dbc.Col([
                html.Div(
                    "Analyzes up to 5 symbols from your watchlist via Gemini AI.",
                    style={"color": "#aaa", "fontSize": "0.85rem",
                           "paddingTop": "0.5rem"},
                ),
            ], md=8),
        ], className="mb-3"),

        dbc.Spinner(
            html.Div(id="na-body"),
            color="primary",
            spinner_style={"width": "3rem", "height": "3rem"},
        ),
    ])


def register_callbacks(app, services):

    @app.callback(
        Output("na-body", "children"),
        Input("na-fetch-btn", "n_clicks"),
        State("na-watchlist-store", "data"),
        prevent_initial_call=True,
    )
    def _fetch(_, watchlist):
        if not watchlist:
            return dbc.Alert(
                "👁️ Add stocks to your watchlist (sidebar) first.",
                color="info",
            )

        if not services["gemini"].is_available():
            return dbc.Alert(
                "⚠️ Gemini AI is not available. Please configure your API key.",
                color="warning",
            )

        symbols = watchlist[:5]
        children = []

        # ── Market summary ─────────────────────────────────────────────
        try:
            stocks_list = []
            for sym in symbols:
                sd = services["market"].get_stock_data(sym)
                if sd:
                    stocks_list.append(sd.to_dict())
            summary_text = services["gemini"].get_market_summary(stocks_list) if stocks_list else None
        except Exception as e:
            summary_text = None

        if summary_text:
            children.append(
                dbc.Card([
                    dbc.CardHeader(html.H5("📋 AI Market Summary",
                                           style={"margin": 0, "color": "#4fc3f7"})),
                    dbc.CardBody(html.P(summary_text,
                                       style={"color": "#e0e0e0", "marginBottom": 0})),
                ], style={"backgroundColor": "#161b27", "border": "1px solid #2a2f3e",
                          "marginBottom": "1.5rem"})
            )

        # ── Per-stock analysis ─────────────────────────────────────────
        children.append(html.H5("📰 Stock News & Sentiment",
                                 style={"color": "#e0e0e0", "marginBottom": "0.75rem"}))

        for sym in symbols:
            card = _stock_analysis_card(sym, services)
            children.append(card)

        return html.Div(children)


def _stock_analysis_card(symbol: str, services) -> dbc.Card:
    try:
        company_info = services["market"].get_company_info(symbol)
        company_name = company_info.get("name", symbol)
        news = services["gemini"].analyze_stock_news(symbol, company_name)
    except Exception as e:
        return dbc.Alert(f"Could not fetch analysis for {symbol}: {e}",
                         color="danger", style={"marginBottom": "0.75rem"})

    if not news:
        return dbc.Alert(f"No analysis available for {symbol}.",
                         color="secondary", style={"marginBottom": "0.75rem"})

    emoji = get_sentiment_emoji(news.sentiment.value)
    sentiment_val = news.sentiment.value.upper()
    badge_color = {
        "BULLISH": "success", "BEARISH": "danger", "NEUTRAL": "secondary",
    }.get(sentiment_val, "secondary")

    return dbc.Card([
        dbc.CardHeader([
            html.Span(f"{emoji} {symbol}",
                      style={"fontWeight": "bold", "color": "#4fc3f7",
                             "fontSize": "1rem"}),
            dbc.Badge(sentiment_val, color=badge_color,
                      style={"marginLeft": "0.75rem", "fontSize": "0.75rem"}),
        ]),
        dbc.CardBody([
            html.H6(news.headline,
                    style={"color": "#e0e0e0", "marginBottom": "0.5rem"}),
            html.P(news.summary,
                   style={"color": "#aaa", "fontSize": "0.85rem",
                          "marginBottom": "0.75rem"}),
            dbc.Row([
                dbc.Col([
                    html.Div("Sentiment Score", className="metric-label"),
                    html.Div(f"{news.sentiment_score:.2f}", className="metric-value"),
                ], md=4),
                dbc.Col([
                    html.Div("Relevance", className="metric-label"),
                    html.Div(f"{news.relevance:.0f}%", className="metric-value"),
                ], md=4),
                dbc.Col([
                    html.Div("Sentiment", className="metric-label"),
                    html.Div(sentiment_val,
                             className=f"metric-value {'positive' if sentiment_val == 'BULLISH' else 'negative' if sentiment_val == 'BEARISH' else ''}"),
                ], md=4),
            ]),
        ]),
    ], style={"backgroundColor": "#161b27", "border": "1px solid #2a2f3e",
              "marginBottom": "0.75rem"})
