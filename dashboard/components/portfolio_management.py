"""Portfolio Management component."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import format_price, format_percentage


def render_portfolio_management(services):
    """Render the Portfolio Management tab."""
    st.header("💼 My Portfolio")
    
    # Add new position form
    with st.expander("➕ Add New Position", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_symbol = st.text_input("Ticker Symbol", key="new_pos_symbol").upper()
        with col2:
            new_shares = st.number_input("Number of Shares", min_value=0.01, value=1.0, step=0.01, key="new_pos_shares")
        with col3:
            new_price = st.number_input("Purchase Price ($)", min_value=0.01, value=100.0, step=0.01, key="new_pos_price")
        
        col1, col2 = st.columns(2)
        with col1:
            purchase_date = st.date_input("Purchase Date", value=datetime.now())
        with col2:
            notes = st.text_input("Notes (optional)", key="new_pos_notes")
        
        if st.button("💾 Add to Portfolio"):
            if new_symbol:
                try:
                    services['portfolio'].add_position(
                        new_symbol,
                        new_shares,
                        new_price,
                        purchase_date.strftime("%Y-%m-%d"),
                        notes
                    )
                    st.success(f"✅ Added {new_shares} shares of {new_symbol} at ${new_price}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a ticker symbol")
    
    # Get portfolio positions
    positions = services['portfolio'].get_all_positions()
    
    if not positions:
        st.info("📭 Your portfolio is empty. Add your first position above!")
    else:
        # Fetch current prices for all positions
        portfolio_symbols = [p['symbol'] for p in positions]
        with st.spinner("Fetching current prices..."):
            stocks_data = services['market'].get_multiple_stocks(portfolio_symbols)
            current_prices = {symbol: stock.current_price for symbol, stock in stocks_data.items()}
        
        # Get portfolio summary
        summary = services['portfolio'].get_portfolio_summary(current_prices)
        
        # Display summary metrics
        st.subheader("📊 Portfolio Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Invested", format_price(summary['total_cost']))
        with col2:
            st.metric("Current Value", format_price(summary['total_current_value']))
        with col3:
            profit_loss_color = "normal" if summary['total_profit_loss'] >= 0 else "inverse"
            st.metric(
                "Total P/L",
                format_price(summary['total_profit_loss']),
                format_percentage(summary['total_profit_loss_pct']),
                delta_color=profit_loss_color
            )
        with col4:
            st.metric("Positions", summary['position_count'])
        
        st.markdown("---")
        
        # Display individual positions
        st.subheader("📋 Holdings")
        
        for pos_detail in summary['positions']:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### {pos_detail['symbol']}")
                    change_color = "🟢" if pos_detail['profit_loss'] >= 0 else "🔴"
                    st.caption(f"{change_color} {pos_detail['shares']} shares")
                
                with col2:
                    st.metric("Avg Price", format_price(pos_detail['avg_buy_price']))
                
                with col3:
                    st.metric("Current", format_price(pos_detail['current_price']))
                
                with col4:
                    st.metric("Cost Basis", format_price(pos_detail['cost_basis']))
                
                with col5:
                    st.metric("Value", format_price(pos_detail['current_value']))
                
                with col6:
                    profit_color = "normal" if pos_detail['profit_loss'] >= 0 else "inverse"
                    st.metric(
                        "P/L",
                        format_price(pos_detail['profit_loss']),
                        format_percentage(pos_detail['profit_loss_pct']),
                        delta_color=profit_color
                    )
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button("📉 Sell", key=f"sell_{pos_detail['symbol']}"):
                        st.session_state[f"show_sell_{pos_detail['symbol']}"] = True
                
                with col2:
                    if st.button("📜 History", key=f"history_{pos_detail['symbol']}"):
                        st.session_state[f"show_history_{pos_detail['symbol']}"] = True
                
                # Sell dialog
                if st.session_state.get(f"show_sell_{pos_detail['symbol']}", False):
                    with st.form(key=f"sell_form_{pos_detail['symbol']}"):
                        st.write(f"**Sell {pos_detail['symbol']}**")
                        sell_shares = st.number_input(
                            f"Shares to sell (max: {pos_detail['shares']})",
                            min_value=0.01,
                            max_value=pos_detail['shares'],
                            value=pos_detail['shares'],
                            step=0.01
                        )
                        sell_price = st.number_input(
                            "Sell Price ($)",
                            min_value=0.01,
                            value=pos_detail['current_price'],
                            step=0.01
                        )
                        sell_notes = st.text_input("Notes (optional)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Confirm Sell"):
                                try:
                                    services['portfolio'].sell_position(
                                        pos_detail['symbol'],
                                        sell_shares,
                                        sell_price,
                                        notes=sell_notes
                                    )
                                    st.success(f"✅ Sold {sell_shares} shares at ${sell_price}")
                                    st.session_state[f"show_sell_{pos_detail['symbol']}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"show_sell_{pos_detail['symbol']}"] = False
                                st.rerun()
                
                # Transaction history
                if st.session_state.get(f"show_history_{pos_detail['symbol']}", False):
                    transactions = services['portfolio'].get_transactions(pos_detail['symbol'])
                    if transactions:
                        st.write(f"**Transaction History for {pos_detail['symbol']}**")
                        trans_data = []
                        for t in transactions:
                            trans_data.append({
                                "Date": t['transaction_date'],
                                "Type": t['transaction_type'],
                                "Shares": t['shares'],
                                "Price": format_price(t['price']),
                                "Total": format_price(t['total_value'])
                            })
                        st.dataframe(pd.DataFrame(trans_data), hide_index=True)
                        if st.button("Close", key=f"close_history_{pos_detail['symbol']}"):
                            st.session_state[f"show_history_{pos_detail['symbol']}"] = False
                            st.rerun()
                
                st.markdown("---")
        
        # Performance stats
        st.subheader("📈 Performance Statistics")
        perf_stats = services['portfolio'].get_performance_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Closed Trades", perf_stats['total_signals'])
        with col2:
            st.metric("Win Rate", f"{perf_stats['win_rate']:.1f}%")
        with col3:
            st.metric("Avg Return", format_percentage(perf_stats['avg_return']))
        with col4:
            st.metric("Best Trade", format_percentage(perf_stats['best_trade']))
