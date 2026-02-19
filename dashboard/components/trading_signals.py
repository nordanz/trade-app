"""Trading Signals component."""

import streamlit as st
import pandas as pd
from services.strategies import DAY_TRADING_STRATEGIES, SWING_TRADING_STRATEGIES
from utils.helpers import (
    format_price,
    format_percentage,
    get_signal_emoji,
    calculate_risk_reward_ratio,
)

_STRATEGY_LABELS: dict[str, str] = {
    # Day trading
    'vwap':           '🎯 VWAP',
    'orb':            '🔓 Opening Range Breakout',
    'momentum':       '🚀 Momentum / Gap-and-Go',
    # Swing trading
    'mean_reversion': '↩️ Mean Reversion (BB)',
    'fibonacci':      '📐 Fibonacci Retracement',
    'breakout':       '💥 Breakout',
}

_DAY_STRATEGY_KEYS = list(DAY_TRADING_STRATEGIES.keys())
_SWING_STRATEGY_KEYS = list(SWING_TRADING_STRATEGIES.keys())


def render_trading_signals(services, watchlist=None):
    """Render the Trading Signals tab."""
    st.header("🎯 Trading Signals")

    # ── Strategy selector ────────────────────────────────────────────────────
    col_type, col_strat = st.columns(2)
    with col_type:
        strategy_type = st.radio(
            "Strategy type",
            ["Swing Trading", "Day Trading"],
            horizontal=True,
            key="ts_strategy_type",
        )
    with col_strat:
        keys = _SWING_STRATEGY_KEYS if strategy_type == "Swing Trading" else _DAY_STRATEGY_KEYS
        selected_strategy = st.selectbox(
            "Strategy",
            options=keys,
            format_func=lambda k: _STRATEGY_LABELS.get(k, k),
            key="ts_strategy_name",
        )

    if strategy_type == "Day Trading":
        st.warning(
            "⚠️ **Data is delayed ~15 minutes** (standard Yahoo Finance feed). "
            "Intraday signals are for **research and screening only** — "
            "do not use them as live execution signals without a real-time data source."
        )

    st.divider()

    # ── Symbol scope ─────────────────────────────────────────────────────────
    show_portfolio_only = st.checkbox(
        "💼 Show signals for my portfolio only",
        value=False,
        key="ts_portfolio_only",
    )

    if show_portfolio_only:
        portfolio_symbols = services['portfolio'].get_portfolio_symbols()
        if not portfolio_symbols:
            st.info("Your portfolio is empty. Add positions in the 'My Portfolio' tab.")
            return
        symbols_to_analyze = portfolio_symbols
        st.info(f"Analyzing {len(portfolio_symbols)} stock(s) from your portfolio.")
    else:
        symbols_to_analyze = watchlist if watchlist else []
        if not symbols_to_analyze:
            st.info("Add stocks to your watchlist to see trading signals.")
            return

    # ── Generate signals ─────────────────────────────────────────────────────
    with st.spinner(f"Analyzing {len(symbols_to_analyze)} symbol(s) with "
                    f"{_STRATEGY_LABELS.get(selected_strategy, selected_strategy)}…"):
        signals = services['strategy'].get_signals_for_multiple_stocks(
            symbols_to_analyze,
            strategy_name=selected_strategy,
        )

    if not signals:
        st.warning("Unable to generate signals. Please try again.")
        return

    portfolio_positions = {p['symbol']: p for p in services['portfolio'].get_all_positions()}

    # ── Top opportunities ────────────────────────────────────────────────────
    st.subheader("🌟 Top Opportunities")
    top_opportunities = services['strategy'].filter_top_opportunities(signals)

    if top_opportunities:
        for signal in top_opportunities:
            signal_emoji = get_signal_emoji(signal.signal.value)
            in_portfolio = signal.symbol in portfolio_positions
            portfolio_badge = "  💼 **IN PORTFOLIO**" if in_portfolio else ""

            with st.container():
                st.markdown(
                    f"### {signal_emoji} {signal.signal.value} — {signal.symbol}{portfolio_badge}"
                )

                # Portfolio-aware recommendation
                if in_portfolio:
                    position = portfolio_positions[signal.symbol]
                    shares_owned = position['shares']
                    avg_buy_price = position['avg_buy_price']
                    pl_pct = (signal.entry_price - avg_buy_price) / avg_buy_price * 100

                    if signal.signal.value == "SELL":
                        st.info(
                            f"**💡 Recommendation:** Consider selling your {shares_owned} shares  \n"
                            f"- Bought at: {format_price(avg_buy_price)}  \n"
                            f"- Current price: {format_price(signal.entry_price)}  \n"
                            f"- Target sell: {format_price(signal.target_price)}  \n"
                            f"- Unrealised P/L: {format_percentage(pl_pct)}"
                        )
                    elif signal.signal.value == "BUY":
                        st.info(
                            f"**💡 Recommendation:** Consider adding to your position  \n"
                            f"- Current: {shares_owned} shares @ avg {format_price(avg_buy_price)}  \n"
                            f"- Suggested entry: {format_price(signal.entry_price)}  \n"
                            f"- {'Would lower' if signal.entry_price < avg_buy_price else 'Would raise'} "
                            f"your average cost"
                        )
                else:
                    if signal.signal.value == "BUY":
                        st.success(
                            f"**💡 Recommendation:** Consider opening a new position in {signal.symbol}"
                        )

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Entry", format_price(signal.entry_price))
                c2.metric("Target", format_price(signal.target_price))
                c3.metric("Stop Loss", format_price(signal.stop_loss))
                c4.metric("Confidence", f"{signal.confidence:.0f}%")

                rr_ratio = calculate_risk_reward_ratio(
                    signal.entry_price, signal.target_price, signal.stop_loss
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"**Holding Period:** {signal.holding_period}")
                with col2:
                    st.caption(f"**Risk/Reward:** 1:{rr_ratio:.2f}")
                with col3:
                    if st.button("💾 Save Signal", key=f"save_{signal.symbol}_{selected_strategy}"):
                        try:
                            services['portfolio'].save_signal(
                                signal.symbol,
                                signal.signal.value,
                                signal.confidence,
                                signal.entry_price,
                                signal.target_price,
                                signal.stop_loss,
                                signal.reasoning,
                            )
                            st.success("Signal saved to history!")
                        except Exception as e:
                            st.error(f"Error saving signal: {e}")

                st.info(f"**Reasoning:** {signal.reasoning}")

                with st.expander("📊 Technical Indicators"):
                    ind1, ind2, ind3 = st.columns(3)
                    rsi_val = signal.indicators.get('rsi')
                    ind1.metric("RSI", f"{rsi_val:.1f}" if rsi_val else "N/A")
                    ind2.metric("Trend", signal.indicators.get('trend', 'N/A'))
                    vol = signal.indicators.get('volume', {})
                    ind3.metric("Volume", vol.get('volume_trend', 'N/A'))

                st.markdown("---")
    else:
        st.info("No strong buy signals at the moment for this strategy. Check back later!")

    st.divider()

    # ── All signals table ────────────────────────────────────────────────────
    st.subheader("📊 All Signals")

    signal_rows = []
    for sym, sig in signals.items():
        signal_rows.append({
            "Symbol": ("💼 " if sym in portfolio_positions else "") + sym,
            "Signal": f"{get_signal_emoji(sig.signal.value)} {sig.signal.value}",
            "Confidence": f"{sig.confidence:.0f}%",
            "Entry": format_price(sig.entry_price),
            "Target": format_price(sig.target_price),
            "Stop Loss": format_price(sig.stop_loss),
            "Holding": sig.holding_period,
        })

    if signal_rows:
        st.dataframe(pd.DataFrame(signal_rows), use_container_width=True, hide_index=True)

    # ── Signal history ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("📜 Signal History")

    history_limit = st.slider(
        "Number of signals to show", 5, 50, 20, key="ts_history_limit"
    )
    signal_history = services['portfolio'].get_signals(limit=history_limit)

    if signal_history:
        history_rows = []
        for sig in signal_history:
            history_rows.append({
                "Date": sig['signal_date'],
                "Symbol": sig['symbol'],
                "Signal": f"{get_signal_emoji(sig['signal_type'])} {sig['signal_type']}",
                "Entry": format_price(sig['entry_price']),
                "Target": format_price(sig['target_price']),
                "Confidence": f"{sig['confidence']:.0f}%",
                "Status": sig['status'],
                "P/L": format_percentage(sig['profit_loss']) if sig['profit_loss'] else "N/A",
            })
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No signal history yet. Save signals to track them here!")
