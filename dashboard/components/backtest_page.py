"""Backtest page – strategy comparison and deep-dive for power users."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

from services.backtest_service import STRATEGY_MIN_BARS
from services.strategies import ALL_STRATEGIES, DAY_TRADING_STRATEGIES, SWING_TRADING_STRATEGIES
from utils.helpers import format_price, format_percentage

_STRATEGY_LABELS: dict[str, str] = {
    'vwap':           '🎯 VWAP',
    'orb':            '🔓 Opening Range Breakout',
    'momentum':       '🚀 Momentum / Gap-and-Go',
    'mean_reversion': '↩️ Mean Reversion (BB)',
    'fibonacci':      '📐 Fibonacci Retracement',
    'breakout':       '💥 Breakout',
}

_DAY_STRATEGY_KEYS = list(DAY_TRADING_STRATEGIES.keys())
_SWING_STRATEGY_KEYS = list(SWING_TRADING_STRATEGIES.keys())


def render_backtest_page(services, watchlist):
    """Render the full-page Backtest tab."""

    st.header("🧪 Backtest & Strategy Comparison")
    st.info(
        "Run a single strategy deep-dive **or** compare all strategies side-by-side "
        "on the same historical data. For quick in-context backtests, use the "
        "**🧪 Backtest** panel on the Day Trading or Swing Trading pages."
    )

    if 'backtest' not in services:
        st.error("BacktestService is not available.")
        return

    # ── Mode toggle ──────────────────────────────────────────────────────────
    mode = st.radio(
        "Mode",
        ["Single Strategy", "Compare All Strategies"],
        horizontal=True,
        key="bt_page_mode",
    )

    st.divider()

    # ── Shared inputs ────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        symbol = st.selectbox(
            "Stock Symbol",
            options=watchlist if watchlist else ["AAPL"],
            key="bt_page_symbol",
        )
        custom = st.text_input(
            "…or type a symbol",
            placeholder="e.g. NVDA",
            key="bt_page_custom_symbol",
        ).upper()
        if custom:
            symbol = custom

    with col2:
        start_date = st.date_input(
            "Start date",
            value=date.today() - timedelta(days=365),
            max_value=date.today(),
            key="bt_page_start",
        )

    with col3:
        end_date = st.date_input(
            "End date",
            value=date.today(),
            min_value=start_date,
            max_value=date.today(),
            key="bt_page_end",
        )

    col1, col2 = st.columns(2)
    with col1:
        cash = st.number_input(
            "Starting capital ($)",
            min_value=1_000,
            max_value=1_000_000,
            value=10_000,
            step=1_000,
            key="bt_page_cash",
        )
    with col2:
        use_sentiment = st.checkbox(
            "Include news sentiment",
            value=False,
            key="bt_page_sentiment",
            help="Requires NEWS_API_KEY. Sentiment is fetched once and shared across all runs.",
        )

    # ── Single-strategy extra inputs ─────────────────────────────────────────
    if mode == "Single Strategy":
        col1, col2 = st.columns(2)
        with col1:
            strategy_type = st.radio(
                "Strategy type",
                ["Swing Trading", "Day Trading"],
                horizontal=True,
                key="bt_page_strat_type",
            )
        with col2:
            keys = _SWING_STRATEGY_KEYS if strategy_type == "Swing Trading" else _DAY_STRATEGY_KEYS
            strategy_name = st.selectbox(
                "Strategy",
                options=keys,
                format_func=lambda x: _STRATEGY_LABELS.get(x, x),
                key="bt_page_strategy",
            )

        if strategy_type == "Day Trading":
            st.caption(
                "⚠️ Day-trading strategies use **5-minute bars**. "
                "yfinance limits intraday history to ~60 days."
            )

    # ── Run button ───────────────────────────────────────────────────────────
    run = st.button("▶️ Run Backtest", type="primary", use_container_width=True, key="bt_page_run")

    if run:
        # ── Fetch data ───────────────────────────────────────────────────────
        is_intraday = (
            mode == "Single Strategy"
            and strategy_name in _DAY_STRATEGY_KEYS
        )

        # yfinance caps 5-minute data to the last 60 days.  Clamp silently so the
        # fetch always succeeds even if the user picked a wider window.
        _60_days_ago = date.today() - timedelta(days=59)
        fetch_start = max(start_date, _60_days_ago) if is_intraday else start_date

        if is_intraday and fetch_start > start_date:
            st.warning(
                f"⚠️ yfinance limits 5-minute intraday data to **60 days**. "
                f"Start date clamped to **{fetch_start}**."
            )

        # yfinance `end` is exclusive — add one day so the chosen end date is included.
        fetch_end = end_date + timedelta(days=1)

        with st.spinner(f"Fetching {'5-min intraday' if is_intraday else 'daily'} data for {symbol}…"):
            interval = "5m" if is_intraday else "1d"
            hist = services['market'].get_historical_data(
                symbol,
                interval=interval,
                start=fetch_start.strftime("%Y-%m-%d"),
                end=fetch_end.strftime("%Y-%m-%d"),
            )

        if hist is None or hist.empty:
            st.error(
                f"No data returned for **{symbol}** between {fetch_start} and {end_date}. "
                "Try a wider date range or check the ticker symbol."
            )
            st.session_state.pop('bt_page_result', None)
        else:
            st.success(f"Loaded **{len(hist)} bars** for {symbol}  ({interval})")
            # ── Execute and cache result in session_state ─────────────────────
            if mode == "Single Strategy":
                st.session_state['bt_page_result'] = {
                    'mode': 'single',
                    'hist': hist,
                    'symbol': symbol,
                    'strategy_name': strategy_name,
                    'cash': cash,
                    'use_sentiment': use_sentiment,
                }
            else:
                st.session_state['bt_page_result'] = {
                    'mode': 'compare',
                    'hist': hist,
                    'symbol': symbol,
                    'cash': cash,
                    'use_sentiment': use_sentiment,
                }

    # ── Render cached result (survives re-runs without re-fetching) ──────────
    cached = st.session_state.get('bt_page_result')
    if not cached:
        return

    if cached['mode'] == 'single':
        _run_single(services, cached['hist'], cached['symbol'],
                    cached['strategy_name'], cached['cash'], cached['use_sentiment'])
    else:
        _run_comparison(services, cached['hist'], cached['symbol'],
                        cached['cash'], cached['use_sentiment'])


# ---------------------------------------------------------------------------
# Single strategy
# ---------------------------------------------------------------------------

def _run_single(services, hist, symbol, strategy_name, cash, use_sentiment):
    with st.spinner(f"Running {_STRATEGY_LABELS.get(strategy_name, strategy_name)}…"):
        result = services['backtest'].run_backtest(
            ohlc_data=hist,
            symbol=symbol,
            strategy_name=strategy_name,
            cash=float(cash),
            use_sentiment=use_sentiment,
        )

    if result['status'] == 'INSUFFICIENT_DATA':
        min_bars = STRATEGY_MIN_BARS.get(strategy_name, 30)
        st.warning(
            f"⚠️ Not enough bars — **{strategy_name}** needs at least {min_bars} bars, "
            f"got {len(hist)}. Widen the date range."
        )
        return

    if result['status'] != 'SUCCESS':
        st.error(f"Backtest error: {result.get('error', result['status'])}")
        return

    st.success("✅ Backtest complete")

    _render_single_metrics(result['metrics'])
    _render_equity_curve(result['equity_curve'], symbol, strategy_name)
    _render_trades_table(result['trades'])

    if use_sentiment and result.get('sentiment'):
        _render_sentiment_summary(result['sentiment'])


def _render_single_metrics(metrics: dict) -> None:
    st.markdown("### 📊 Performance Metrics")

    net = metrics.get('net_profit', 0)
    ret = metrics.get('return_pct')
    bah = metrics.get('buy_and_hold_return_pct')
    sharpe = metrics.get('sharpe_ratio')
    drawdown = metrics.get('max_drawdown')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Profit", format_price(net),
              delta=f"{ret:.1f}%" if ret is not None else None,
              delta_color="normal" if net >= 0 else "inverse")
    c2.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%",
              f"{metrics.get('total_trades', 0)} trades")
    c3.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
    c4.metric("Avg Return/Trade", format_percentage(metrics.get('avg_return', 0)))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Profit", format_price(metrics.get('gross_profit', 0)))
    c2.metric("Gross Loss", format_price(metrics.get('gross_loss', 0)))
    c3.metric("Best Trade", format_percentage(metrics.get('best_trade', 0)))
    c4.metric("Worst Trade", format_percentage(metrics.get('worst_trade', 0)))

    if any(v is not None for v in (sharpe, drawdown, bah)):
        c1, c2, c3, _ = st.columns(4)
        if sharpe is not None:
            c1.metric("Sharpe Ratio", f"{sharpe:.2f}")
        if drawdown is not None:
            c2.metric("Max Drawdown", f"{drawdown:.1f}%")
        if bah is not None:
            c3.metric("Buy & Hold Return", f"{bah:.1f}%")


# ---------------------------------------------------------------------------
# Comparison mode
# ---------------------------------------------------------------------------

def _run_comparison(services, hist, symbol, cash, use_sentiment):
    # Comparison mode uses daily bars → swing strategies only.
    # Day-trading strategies need intraday bars (Single Strategy mode).
    swing_keys = _SWING_STRATEGY_KEYS

    with st.spinner(f"Running {len(swing_keys)} swing strategies on {symbol}…"):
        compare_result = services['backtest'].compare_strategies(
            ohlc_data=hist,
            symbol=symbol,
            strategy_names=swing_keys,
            cash=float(cash),
            use_sentiment=use_sentiment,
        )

    st.info(
        "ℹ️ Comparison mode uses **daily bars** and runs the 3 swing strategies. "
        "Day-trading strategies require intraday (5-min) data — use Single Strategy mode for those."
    )

    if compare_result['status'] != 'SUCCESS':
        st.error("Comparison failed.")
        return

    summary = compare_result['summary']

    st.success(
        f"✅ {summary['successful_runs']}/{summary['total_strategies']} strategies ran  •  "
        f"Best: **{_STRATEGY_LABELS.get(summary['best_strategy'], summary['best_strategy'])}** "
        f"({format_price(summary['best_net_profit'])} net profit)"
    )

    # ── Ranking table ────────────────────────────────────────────────────────
    st.markdown("### 🏆 Strategy Ranking")

    ranking_rows = []
    for entry in summary['ranking']:
        ranking_rows.append({
            "Rank": f"#{entry['rank']}",
            "Strategy": _STRATEGY_LABELS.get(entry['strategy'], entry['strategy']),
            "Net Profit": format_price(entry['net_profit']),
            "Win Rate": f"{entry['win_rate']:.1f}%",
            "Trades": entry['total_trades'],
            "Sharpe": f"{entry['sharpe_ratio']:.2f}" if entry.get('sharpe_ratio') else "—",
            "Max DD": f"{entry['max_drawdown']:.1f}%" if entry.get('max_drawdown') else "—",
        })

    if ranking_rows:
        df = pd.DataFrame(ranking_rows)

        def _color_net(val: str) -> str:
            try:
                num = float(val.replace("$", "").replace(",", "").replace("+", ""))
                return "color: #2ecc71" if num > 0 else "color: #e74c3c" if num < 0 else ""
            except ValueError:
                return ""

        st.dataframe(
            df.style.applymap(_color_net, subset=["Net Profit"]),
            use_container_width=True,
            hide_index=True,
        )

    # ── Overlay equity curves ────────────────────────────────────────────────
    successful_results = [r for r in compare_result['results'] if r['status'] == 'SUCCESS']
    if successful_results:
        st.markdown("### 📈 Equity Curves (all strategies)")
        fig = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
        for i, r in enumerate(successful_results):
            if not r.get('equity_curve'):
                continue
            ec_df = pd.DataFrame(r['equity_curve'])
            label = _STRATEGY_LABELS.get(r['strategy'], r['strategy'])
            fig.add_trace(go.Scatter(
                x=ec_df['date'], y=ec_df['balance'],
                mode='lines', name=label,
                line=dict(color=colors[i % len(colors)], width=2),
            ))
        fig.update_layout(
            xaxis_title="Date", yaxis_title="Balance ($)",
            hovermode="x unified", height=400,
            margin=dict(t=20, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Per-strategy trade tables (collapsed) ────────────────────────────────
    st.markdown("### 📋 Trade Details by Strategy")
    for r in successful_results:
        label = _STRATEGY_LABELS.get(r['strategy'], r['strategy'])
        with st.expander(f"{label} — {len(r['trades'])} trades"):
            _render_trades_table(r['trades'])


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _render_equity_curve(equity_curve: list, symbol: str, strategy_name: str) -> None:
    if not equity_curve:
        return
    st.markdown("### 📈 Equity Curve")
    df = pd.DataFrame(equity_curve)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['balance'],
        mode='lines', name='Portfolio',
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy', fillcolor='rgba(31,119,180,0.1)',
    ))
    fig.update_layout(
        title=f"{symbol} — {_STRATEGY_LABELS.get(strategy_name, strategy_name)}",
        xaxis_title="Date", yaxis_title="Balance ($)",
        hovermode='x unified', height=350,
        margin=dict(t=40, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_trades_table(trades: list) -> None:
    if not trades:
        st.info("No trades generated.")
        return
    rows = [{
        "Entry": t.entry_date, "Exit": t.exit_date,
        "Entry $": format_price(t.entry_price), "Exit $": format_price(t.exit_price),
        "Return": format_percentage(t.return_pct), "P/L": format_price(t.profit_loss),
    } for t in trades]
    df = pd.DataFrame(rows)

    def _color(val: str) -> str:
        try:
            num = float(val.replace("%", "").replace("+", "").replace("$", "").replace(",", ""))
            return "color: #2ecc71" if num > 0 else "color: #e74c3c" if num < 0 else ""
        except ValueError:
            return ""

    st.dataframe(
        df.style.applymap(_color, subset=["Return", "P/L"]),
        use_container_width=True, hide_index=True,
    )


def _render_sentiment_summary(sentiment: dict) -> None:
    st.markdown("### 📰 News Sentiment")
    score = sentiment.get("sentiment_score", 0)
    emoji = "😊" if score > 0.1 else "😟" if score < -0.1 else "😐"
    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{score:+.2f}", emoji)
    c2.metric("Articles", sentiment.get("article_count", 0))
    c3.metric("Status", sentiment.get("status", "—"))

    st.header("🧪 Backtest RSI + MA Strategy")
    st.info("Backtest a swing trading strategy (RSI + Moving Average) with optional news sentiment filtering.")
    
    # Symbol selection
    col1, col2 = st.columns(2)
    with col1:
        backtest_symbol = st.selectbox(
            "Select Stock to Backtest", 
            watchlist if watchlist else ['AAPL'], 
            key="backtest_symbol"
        )
    with col2:
        backtest_period = st.selectbox(
            "Historical Period", 
            ['1mo', '3mo', '6mo', '1y'], 
            index=2,
            key="backtest_period"
        )
    
    # Strategy parameters
    st.subheader("⚙️ Strategy Parameters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rsi_period = st.number_input("RSI Period", min_value=5, max_value=30, value=14, key="backtest_rsi_period")
    with col2:
        rsi_oversold = st.number_input("RSI Oversold", min_value=10, max_value=40, value=30, key="backtest_rsi_oversold")
    with col3:
        rsi_overbought = st.number_input("RSI Overbought", min_value=60, max_value=90, value=70, key="backtest_rsi_overbought")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ma_short = st.number_input("Short MA Period", min_value=5, max_value=50, value=20, key="backtest_ma_short")
    with col2:
        ma_long = st.number_input("Long MA Period", min_value=50, max_value=200, value=50, key="backtest_ma_long")
    with col3:
        st.metric("Strategy", "RSI + MA Crossover", "Swing Trading")
    
    # Sentiment filter
    st.subheader("📰 Sentiment Filter (Optional)")
    use_sentiment = st.checkbox("Use news sentiment filter", value=True, key="backtest_use_sentiment")
    
    if use_sentiment:
        sentiment_threshold = st.slider(
            "Minimum sentiment score for BUY signals",
            min_value=-1.0,
            max_value=1.0,
            value=-0.3,
            step=0.1,
            help="Only enter BUY trades if news sentiment is above this threshold",
            key="backtest_sentiment_slider"
        )
    else:
        sentiment_threshold = -1.0
    
    # Run backtest
    if st.button("🚀 Run Backtest", key="run_backtest"):
        with st.spinner("Running backtest and fetching data..."):
            try:
                # Check if backtest service is available
                if 'backtest' not in services:
                    st.error("Backtest service not available. Please ensure BacktestService is initialized.")
                    return
                
                # Fetch historical data
                hist_data = services['market'].get_historical_data(
                    backtest_symbol,
                    period=backtest_period,
                    interval='1d'
                )
                
                if hist_data.empty:
                    st.error(f"No data available for {backtest_symbol}")
                else:
                    # Run backtest
                    result = services['backtest'].rsi_ma_backtest(
                        hist_data,
                        backtest_symbol,
                        rsi_period=rsi_period,
                        rsi_oversold=rsi_oversold,
                        rsi_overbought=rsi_overbought,
                        ma_short=ma_short,
                        ma_long=ma_long,
                        use_sentiment=use_sentiment,
                        sentiment_threshold=sentiment_threshold
                    )
                    
                    if result['status'] == 'SUCCESS':
                        st.success("✅ Backtest completed!")
                        
                        # Display sentiment info
                        if use_sentiment and result.get('sentiment'):
                            st.markdown("---")
                            st.subheader("📰 News Sentiment Analysis")
                            sentiment = result['sentiment']
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                sentiment_emoji = "😊" if sentiment['sentiment_score'] > 0 else "😟" if sentiment['sentiment_score'] < 0 else "😐"
                                st.metric("Sentiment Score", sentiment['sentiment_score'], sentiment_emoji)
                            with col2:
                                st.metric("Articles Found", sentiment['article_count'])
                            with col3:
                                st.metric("Status", sentiment['status'])
                            
                            if sentiment.get('articles'):
                                st.write("**Top News Articles:**")
                                for i, article in enumerate(sentiment['articles'][:3], 1):
                                    with st.expander(f"{i}. {article['title'][:60]}..."):
                                        st.write(article.get('description', 'No description'))
                                        st.caption(f"Source: {article.get('source', {}).get('name', 'Unknown')}")
                        
                        # Display metrics
                        st.markdown("---")
                        st.subheader("📊 Backtest Results")
                        
                        metrics = result['metrics']
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Trades", metrics.get('total_trades', 0))
                        with col2:
                            win_rate = metrics.get('win_rate', 0)
                            win_rate_color = "normal" if win_rate > 50 else "inverse"
                            st.metric(
                                "Win Rate",
                                f"{win_rate:.1f}%",
                                delta_color=win_rate_color
                            )
                        with col3:
                            avg_return = metrics.get('avg_return', 0)
                            avg_return_color = "normal" if avg_return > 0 else "inverse"
                            st.metric(
                                "Avg Return",
                                format_percentage(avg_return),
                                delta_color=avg_return_color
                            )
                        with col4:
                            st.metric("Best Trade", format_percentage(metrics.get('best_trade', 0)))
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Worst Trade", format_percentage(metrics.get('worst_trade', 0)))
                        with col2:
                            st.metric("Gross Profit", format_price(metrics.get('gross_profit', 0)))
                        with col3:
                            st.metric("Gross Loss", format_price(metrics.get('gross_loss', 0)))
                        with col4:
                            st.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
                        
                        # Equity curve chart
                        st.markdown("---")
                        st.subheader("📈 Equity Curve")
                        
                        if result.get('equity_curve'):
                            equity_df = pd.DataFrame(result['equity_curve'])
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=equity_df['date'],
                                y=equity_df['balance'],
                                mode='lines',
                                name='Portfolio Value',
                                line=dict(color='#1f77b4', width=2)
                            ))
                            
                            fig.update_layout(
                                title=f"Portfolio Growth - {backtest_symbol}",
                                xaxis_title="Date",
                                yaxis_title="Balance ($)",
                                hovermode='x unified',
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Trades table
                        st.markdown("---")
                        st.subheader("📋 Trade History")
                        
                        if result.get('trades'):
                            trades_data = []
                            for trade in result['trades']:
                                trades_data.append({
                                    "Entry Date": trade.entry_date,
                                    "Exit Date": trade.exit_date,
                                    "Entry Price": format_price(trade.entry_price),
                                    "Exit Price": format_price(trade.exit_price),
                                    "Return": format_percentage(trade.return_pct),
                                    "Sentiment": f"{trade.sentiment_score:+.2f}",
                                    "P/L": format_price(trade.profit_loss)
                                })
                            
                            st.dataframe(pd.DataFrame(trades_data), use_container_width=True, hide_index=True)
                        else:
                            st.info("No trades generated. Try adjusting parameters.")
                    
                    else:
                        st.error(f"Backtest failed: {result.get('status', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
