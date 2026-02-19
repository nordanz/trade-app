"""
Reusable inline backtest panel.

Renders a collapsible ``st.expander`` pre-filled with the caller's symbol and
strategy.  Can be dropped into any page with one function call:

    from dashboard.components.backtest_widget import render_backtest_panel
    render_backtest_panel(services, symbol="AAPL", strategy_name="mean_reversion")
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from services.backtest_service import STRATEGY_MIN_BARS, DAY_TRADING_STRATEGY_NAMES
from utils.helpers import format_price, format_percentage

# ---------------------------------------------------------------------------
_STRATEGY_LABELS: dict[str, str] = {
    'vwap':           '🎯 VWAP',
    'orb':            '🔓 Opening Range Breakout',
    'momentum':       '🚀 Momentum/Gap-and-Go',
    'mean_reversion': '↩️ Mean Reversion (BB)',
    'fibonacci':      '📐 Fibonacci Retracement',
    'breakout':       '💥 Breakout',
}


def render_backtest_panel(
    services: dict,
    symbol: str,
    strategy_name: str,
    *,
    key_prefix: str = "",
) -> None:
    """
    Render a collapsible backtest panel pre-filled with *symbol* and
    *strategy_name*.

    Parameters
    ----------
    services:       The shared ``services`` dict from ``app.py``.
    symbol:         Ticker already chosen on the calling page.
    strategy_name:  Strategy key already chosen on the calling page.
    key_prefix:     Unique prefix to avoid Streamlit widget-key collisions when
                    the panel is embedded on more than one page.
    """
    if 'backtest' not in services:
        return

    label = _STRATEGY_LABELS.get(strategy_name, strategy_name)
    is_intraday = strategy_name in DAY_TRADING_STRATEGY_NAMES

    with st.expander(f"🧪 Backtest **{label}** on **{symbol}**", expanded=False):

        st.caption(
            "Validate how this strategy performed historically before acting on a live signal."
        )

        # ── Date range ──────────────────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            default_start = date.today() - timedelta(days=180 if not is_intraday else 30)
            start_date = st.date_input(
                "Start date",
                value=default_start,
                max_value=date.today(),
                key=f"{key_prefix}bt_start_{strategy_name}_{symbol}",
            )
        with col2:
            end_date = st.date_input(
                "End date",
                value=date.today(),
                min_value=start_date,
                max_value=date.today(),
                key=f"{key_prefix}bt_end_{strategy_name}_{symbol}",
            )

        # ── Cash & sentiment ────────────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            cash = st.number_input(
                "Starting capital ($)",
                min_value=1_000,
                max_value=1_000_000,
                value=10_000,
                step=1_000,
                key=f"{key_prefix}bt_cash_{strategy_name}_{symbol}",
            )
        with col2:
            use_sentiment = st.checkbox(
                "Include news sentiment",
                value=False,
                key=f"{key_prefix}bt_sentiment_{strategy_name}_{symbol}",
                help="Fetches recent headlines and scores them. Requires a NEWS_API_KEY.",
            )

        run = st.button(
            "▶️ Run Backtest",
            type="primary",
            use_container_width=True,
            key=f"{key_prefix}bt_run_{strategy_name}_{symbol}",
        )

        if not run:
            return

        # ── Fetch data ───────────────────────────────────────────────────────
        # yfinance `end` is exclusive — add one day so the chosen end is included.
        fetch_end = end_date + timedelta(days=1)

        with st.spinner(f"Fetching data for {symbol}…"):
            interval = "5m" if is_intraday else "1d"
            hist = services['market'].get_historical_data(
                symbol,
                interval=interval,
                start=start_date.strftime("%Y-%m-%d"),
                end=fetch_end.strftime("%Y-%m-%d"),
            )

        if hist is None or hist.empty:
            st.error(
                f"No data returned for **{symbol}** between {start_date} and {end_date}. "
                "Try a wider date range or check the ticker."
            )
            return

        # ── Run backtest ─────────────────────────────────────────────────────
        with st.spinner("Running backtest…"):
            result = services['backtest'].run_backtest(
                ohlc_data=hist,
                symbol=symbol,
                strategy_name=strategy_name,
                cash=float(cash),
                use_sentiment=use_sentiment,
            )

        # ── Display results ──────────────────────────────────────────────────
        status = result.get("status")

        if status == "INSUFFICIENT_DATA":
            st.warning(
                f"⚠️ Not enough bars for **{label}**: {result.get('error')}. "
                f"Try a wider date range (min {min_days} calendar days)."
            )
            return

        if status != "SUCCESS":
            st.error(f"Backtest failed — {result.get('error', status)}")
            return

        st.success(f"✅ Backtest complete  •  {start_date} → {end_date}  •  {len(hist)} bars")

        _render_metrics(result["metrics"])
        _render_equity_curve(result["equity_curve"], symbol, strategy_name)
        _render_trades_table(result["trades"])

        if use_sentiment and result.get("sentiment"):
            _render_sentiment(result["sentiment"])


# ---------------------------------------------------------------------------
# Private rendering helpers
# ---------------------------------------------------------------------------

def _render_metrics(metrics: dict) -> None:
    """Render the key performance metrics row."""
    st.markdown("#### 📊 Performance")

    net = metrics.get("net_profit", 0)
    ret = metrics.get("return_pct")
    bah = metrics.get("buy_and_hold_return_pct")
    sharpe = metrics.get("sharpe_ratio")
    drawdown = metrics.get("max_drawdown")

    # Row 1 – P&L
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Net Profit",
        format_price(net),
        delta=f"{ret:.1f}%" if ret is not None else None,
        delta_color="normal" if net >= 0 else "inverse",
    )
    c2.metric(
        "Win Rate",
        f"{metrics.get('win_rate', 0):.1f}%",
        f"{metrics.get('total_trades', 0)} trades",
    )
    c3.metric(
        "Profit Factor",
        f"{metrics.get('profit_factor', 0):.2f}",
    )
    c4.metric(
        "Avg Return / Trade",
        format_percentage(metrics.get("avg_return", 0)),
    )

    # Row 2 – risk stats (only if populated from backtesting.py)
    if any(v is not None for v in (sharpe, drawdown, bah)):
        c1, c2, c3, c4 = st.columns(4)
        if sharpe is not None:
            c1.metric("Sharpe Ratio", f"{sharpe:.2f}")
        if drawdown is not None:
            c2.metric("Max Drawdown", f"{drawdown:.1f}%")
        if bah is not None:
            c3.metric("Buy & Hold Return", f"{bah:.1f}%")
        c4.metric(
            "Best / Worst Trade",
            f"{format_percentage(metrics.get('best_trade', 0))} / "
            f"{format_percentage(metrics.get('worst_trade', 0))}",
        )


def _render_equity_curve(equity_curve: list, symbol: str, strategy_name: str) -> None:
    """Render the equity curve chart."""
    if not equity_curve:
        st.info("No equity curve data available.")
        return

    st.markdown("#### 📈 Equity Curve")
    df = pd.DataFrame(equity_curve)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["balance"],
            mode="lines",
            name="Portfolio",
            line=dict(color="#1f77b4", width=2),
            fill="tozeroy",
            fillcolor="rgba(31,119,180,0.1)",
        )
    )
    fig.update_layout(
        title=f"{symbol} — {_STRATEGY_LABELS.get(strategy_name, strategy_name)}",
        xaxis_title="Date",
        yaxis_title="Balance ($)",
        hovermode="x unified",
        height=300,
        margin=dict(t=40, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_trades_table(trades: list) -> None:
    """Render a compact trade history table."""
    if not trades:
        st.info("No trades were generated. Try a wider date range or different parameters.")
        return

    st.markdown(f"#### 📋 Trade History ({len(trades)} trades)")

    rows = [
        {
            "Entry": t.entry_date,
            "Exit": t.exit_date,
            "Entry $": format_price(t.entry_price),
            "Exit $": format_price(t.exit_price),
            "Return": format_percentage(t.return_pct),
            "P/L": format_price(t.profit_loss),
        }
        for t in trades
    ]
    df = pd.DataFrame(rows)

    def _color_return(val: str) -> str:
        try:
            num = float(val.replace("%", "").replace("+", ""))
            return "color: #2ecc71" if num > 0 else "color: #e74c3c" if num < 0 else ""
        except ValueError:
            return ""

    st.dataframe(
        df.style.applymap(_color_return, subset=["Return", "P/L"]),
        use_container_width=True,
        hide_index=True,
    )


def _render_sentiment(sentiment: dict) -> None:
    """Render the news sentiment summary."""
    st.markdown("#### 📰 News Sentiment")
    score = sentiment.get("sentiment_score", 0)
    emoji = "😊" if score > 0.1 else "😟" if score < -0.1 else "😐"
    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{score:+.2f}", emoji)
    c2.metric("Articles", sentiment.get("article_count", 0))
    c3.metric("Status", sentiment.get("status", "—"))
