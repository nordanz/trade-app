"""Trading Signals component."""

import streamlit as st
import pandas as pd
from utils.helpers import (
    format_price,
    format_percentage,
    get_signal_emoji,
    calculate_risk_reward_ratio
)


def render_trading_signals(services, selected_symbol, watchlist=None):
    """Render the Trading Signals tab."""
    st.header("🎯 Swing Trading Recommendations")
    
    # Add toggle for portfolio-only signals
    show_portfolio_only = st.checkbox("💼 Show signals for my portfolio only", value=False)
    
    # Determine which symbols to analyze
    if show_portfolio_only:
        portfolio_symbols = services['portfolio'].get_portfolio_symbols()
        if not portfolio_symbols:
            st.info("Your portfolio is empty. Add positions in the 'My Portfolio' tab.")
            symbols_to_analyze = []
        else:
            symbols_to_analyze = portfolio_symbols
            st.info(f"Analyzing {len(portfolio_symbols)} stocks from your portfolio")
    else:
        symbols_to_analyze = watchlist if watchlist else []
    
    if not symbols_to_analyze:
        if not show_portfolio_only:
            st.info("Add stocks to your watchlist to see trading signals")
    else:
        with st.spinner("Analyzing stocks and generating signals..."):
            signals = services['strategy'].get_signals_for_multiple_stocks(symbols_to_analyze)
        
        if not signals:
            st.warning("Unable to generate signals. Please try again.")
        else:
            # Get portfolio positions to show what to do
            portfolio_positions = {p['symbol']: p for p in services['portfolio'].get_all_positions()}
            
            # Top opportunities
            st.subheader("🌟 Top Opportunities")
            top_opportunities = services['strategy'].filter_top_opportunities(signals)
            
            if top_opportunities:
                for signal in top_opportunities:
                    signal_emoji = get_signal_emoji(signal.signal.value)
                    
                    # Check if this stock is in portfolio
                    in_portfolio = signal.symbol in portfolio_positions
                    portfolio_badge = " 💼 **IN PORTFOLIO**" if in_portfolio else ""
                    
                    with st.container():
                        st.markdown(f"### {signal_emoji} {signal.signal.value} SIGNAL - {signal.symbol}{portfolio_badge}")
                        
                        # Show portfolio-specific recommendation
                        if in_portfolio:
                            position = portfolio_positions[signal.symbol]
                            shares_owned = position['shares']
                            avg_buy_price = position['avg_buy_price']
                            
                            if signal.signal.value == "SELL":
                                st.info(f"""
                                **💡 Recommendation:** Consider selling your {shares_owned} shares
                                - You bought at: {format_price(avg_buy_price)}
                                - Current price: {format_price(signal.entry_price)}
                                - Target sell: {format_price(signal.target_price)}
                                - Your P/L: {format_percentage((signal.entry_price - avg_buy_price) / avg_buy_price * 100)}
                                """)
                            elif signal.signal.value == "BUY":
                                st.info(f"""
                                **💡 Recommendation:** Consider adding to your position
                                - Current shares: {shares_owned} at avg {format_price(avg_buy_price)}
                                - Suggested entry: {format_price(signal.entry_price)}
                                - This would lower your avg if price < {format_price(avg_buy_price)}
                                """)
                        else:
                            if signal.signal.value == "BUY":
                                st.success(f"**💡 Recommendation:** Consider opening a new position in {signal.symbol}")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Entry", format_price(signal.entry_price))
                        with col2:
                            st.metric("Target", format_price(signal.target_price))
                        with col3:
                            st.metric("Stop Loss", format_price(signal.stop_loss))
                        with col4:
                            st.metric("Confidence", f"{signal.confidence:.0f}%")
                        
                        # Calculate risk/reward
                        rr_ratio = calculate_risk_reward_ratio(
                            signal.entry_price,
                            signal.target_price,
                            signal.stop_loss
                        )
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"**Holding Period:** {signal.holding_period}")
                        with col2:
                            st.caption(f"**Risk/Reward:** 1:{rr_ratio:.2f}")
                        with col3:
                            # Button to save signal to history
                            if st.button("💾 Save Signal", key=f"save_{signal.symbol}"):
                                try:
                                    services['portfolio'].save_signal(
                                        signal.symbol,
                                        signal.signal.value,
                                        signal.confidence,
                                        signal.entry_price,
                                        signal.target_price,
                                        signal.stop_loss,
                                        signal.reasoning
                                    )
                                    st.success("Signal saved to history!")
                                except Exception as e:
                                    st.error(f"Error saving signal: {str(e)}")
                        
                        st.info(f"**Reasoning:** {signal.reasoning}")
                        
                        # Technical indicators
                        with st.expander("📊 Technical Indicators"):
                            ind_col1, ind_col2, ind_col3 = st.columns(3)
                            
                            with ind_col1:
                                rsi = signal.indicators.get('rsi')
                                st.metric("RSI", f"{rsi:.1f}" if rsi else "N/A")
                            
                            with ind_col2:
                                trend = signal.indicators.get('trend', 'N/A')
                                st.metric("Trend", trend)
                            
                            with ind_col3:
                                volume = signal.indicators.get('volume', {})
                                vol_trend = volume.get('volume_trend', 'N/A')
                                st.metric("Volume", vol_trend)
                        
                        st.markdown("---")
            else:
                st.info("No strong buy signals at the moment. Check back later!")
            
            st.markdown("---")
            
            # All signals
            st.subheader("📊 All Signals")
            
            # Create DataFrame for display
            signal_data = []
            for symbol, signal in signals.items():
                in_portfolio = symbol in portfolio_positions
                portfolio_marker = "💼" if in_portfolio else ""
                
                signal_data.append({
                    "Symbol": f"{portfolio_marker} {symbol}",
                    "Signal": f"{get_signal_emoji(signal.signal.value)} {signal.signal.value}",
                    "Confidence": f"{signal.confidence:.0f}%",
                    "Entry": format_price(signal.entry_price),
                    "Target": format_price(signal.target_price),
                    "Stop Loss": format_price(signal.stop_loss)
                })
            
            if signal_data:
                df = pd.DataFrame(signal_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Signal history
            st.markdown("---")
            st.subheader("📜 Signal History")
            
            history_limit = st.slider("Number of signals to show", 5, 50, 20)
            signal_history = services['portfolio'].get_signals(limit=history_limit)
            
            if signal_history:
                history_data = []
                for sig in signal_history:
                    history_data.append({
                        "Date": sig['signal_date'],
                        "Symbol": sig['symbol'],
                        "Signal": f"{get_signal_emoji(sig['signal_type'])} {sig['signal_type']}",
                        "Entry": format_price(sig['entry_price']),
                        "Target": format_price(sig['target_price']),
                        "Confidence": f"{sig['confidence']:.0f}%",
                        "Status": sig['status'],
                        "P/L": format_percentage(sig['profit_loss']) if sig['profit_loss'] else "N/A"
                    })
                st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
            else:
                st.info("No signal history yet. Save signals to track them here!")
