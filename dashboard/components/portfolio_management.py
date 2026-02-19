"""Portfolio Management component."""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import format_price, format_percentage


def render_portfolio_management(services):
    """Render the Portfolio Management tab."""

    tab_holdings, tab_watchlist, tab_history = st.tabs(
        ["📋 Holdings", "👁️ Watchlist", "📜 Transaction History"]
    )

    with tab_holdings:
        _render_holdings(services)

    with tab_watchlist:
        _render_watchlist(services)

    with tab_history:
        _render_transaction_history(services)


# ---------------------------------------------------------------------------
# Holdings tab
# ---------------------------------------------------------------------------

def _render_holdings(services):
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
            purchase_date = st.date_input("Purchase Date", value=datetime.now(), key="new_pos_date")
        with col2:
            notes = st.text_input("Notes (optional)", key="new_pos_notes")

        if st.button("💾 Add to Portfolio", key="add_position_btn"):
            if new_symbol:
                try:
                    services['portfolio'].add_position(
                        new_symbol, new_shares, new_price,
                        purchase_date.strftime("%Y-%m-%d"), notes
                    )
                    # Auto-add to watchlist so the ticker appears in the sidebar
                    services['portfolio'].add_to_watchlist(new_symbol)
                    st.session_state.watchlist = services['portfolio'].get_watchlist()
                    st.success(f"✅ Added {new_shares} shares of {new_symbol} at ${new_price:.2f}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a ticker symbol")

    positions = services['portfolio'].get_all_positions()

    if not positions:
        st.info("📭 Your portfolio is empty. Add your first position above!")
        return

    # Fetch current prices
    portfolio_symbols = [p['symbol'] for p in positions]
    with st.spinner("Fetching current prices…"):
        stocks_data = services['market'].get_multiple_stocks(portfolio_symbols)
        current_prices = {sym: s.current_price for sym, s in stocks_data.items()}

    summary = services['portfolio'].get_portfolio_summary(current_prices)

    # Summary metrics
    st.subheader("📊 Portfolio Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Invested", format_price(summary['total_cost']))
    c2.metric("Current Value", format_price(summary['total_current_value']))
    pl_color = "normal" if summary['total_profit_loss'] >= 0 else "inverse"
    c3.metric(
        "Total P/L",
        format_price(summary['total_profit_loss']),
        format_percentage(summary['total_profit_loss_pct']),
        delta_color=pl_color,
    )
    c4.metric("Positions", summary['position_count'])

    st.markdown("---")
    st.subheader("📋 Holdings")

    for pos in summary['positions']:
        sym = pos['symbol']
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 1, 1, 1])
            with c1:
                st.markdown(f"### {sym}")
                badge = "🟢" if pos['profit_loss'] >= 0 else "🔴"
                st.caption(f"{badge} {pos['shares']} shares")
            c2.metric("Avg Price", format_price(pos['avg_buy_price']))
            c3.metric("Current",   format_price(pos['current_price']))
            c4.metric("Cost",      format_price(pos['cost_basis']))
            c5.metric("Value",     format_price(pos['current_value']))
            pl_col = "normal" if pos['profit_loss'] >= 0 else "inverse"
            c6.metric("P/L", format_price(pos['profit_loss']),
                      format_percentage(pos['profit_loss_pct']), delta_color=pl_col)

            # Action row
            c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
            with c1:
                if st.button("📉 Sell", key=f"sell_{sym}"):
                    st.session_state[f"show_sell_{sym}"] = True
            with c2:
                if st.button("📜 History", key=f"history_{sym}"):
                    st.session_state[f"show_history_{sym}"] = not st.session_state.get(f"show_history_{sym}", False)
            with c3:
                in_wl = sym in st.session_state.get('watchlist', [])
                if not in_wl:
                    if st.button("👁️ Watch", key=f"watch_{sym}"):
                        services['portfolio'].add_to_watchlist(sym)
                        st.session_state.watchlist = services['portfolio'].get_watchlist()
                        st.rerun()
                else:
                    st.caption("👁️ Watched")

            # Sell form
            if st.session_state.get(f"show_sell_{sym}", False):
                with st.form(key=f"sell_form_{sym}"):
                    st.write(f"**Sell {sym}**")
                    sell_shares = st.number_input(
                        f"Shares to sell (max {pos['shares']})",
                        min_value=0.01, max_value=pos['shares'],
                        value=pos['shares'], step=0.01,
                    )
                    sell_price = st.number_input(
                        "Sell Price ($)", min_value=0.01,
                        value=pos['current_price'], step=0.01,
                    )
                    sell_notes = st.text_input("Notes (optional)", key=f"sell_notes_{sym}")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.form_submit_button("✅ Confirm Sell"):
                            try:
                                services['portfolio'].sell_position(sym, sell_shares, sell_price, notes=sell_notes)
                                st.success(f"✅ Sold {sell_shares} shares at ${sell_price:.2f}")
                                st.session_state[f"show_sell_{sym}"] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    with sc2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state[f"show_sell_{sym}"] = False
                            st.rerun()

            # Inline transaction history
            if st.session_state.get(f"show_history_{sym}", False):
                txns = services['portfolio'].get_transactions(sym)
                if txns:
                    rows = [{"Date": t['transaction_date'], "Type": t['transaction_type'],
                             "Shares": t['shares'], "Price": format_price(t['price']),
                             "Total": format_price(t['total_value'])} for t in txns]
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

            st.markdown("---")

    # Performance stats
    st.subheader("📈 Signal Performance")
    perf = services['portfolio'].get_performance_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Closed Trades", perf['total_signals'])
    c2.metric("Win Rate", f"{perf['win_rate']:.1f}%")
    c3.metric("Avg Return", format_percentage(perf['avg_return']))
    c4.metric("Best Trade", format_percentage(perf['best_trade']))


# ---------------------------------------------------------------------------
# Watchlist tab
# ---------------------------------------------------------------------------

def _render_watchlist(services):
    st.subheader("👁️ Watchlist")
    st.caption(
        "Your watchlist is **saved to the database** and persists across sessions. "
        "Tickers here also appear in the sidebar and drive the Trading Signals scan."
    )

    # Add from this tab too
    col1, col2 = st.columns([3, 1])
    with col1:
        add_sym = st.text_input(
            "Add ticker to watchlist",
            placeholder="e.g. NVDA",
            key="wl_tab_add_input",
        ).upper()
    with col2:
        st.write("")
        st.write("")
        if st.button("➕ Add", key="wl_tab_add_btn", use_container_width=True):
            if add_sym:
                added = services['portfolio'].add_to_watchlist(add_sym)
                st.session_state.watchlist = services['portfolio'].get_watchlist()
                if added:
                    st.success(f"Added {add_sym}")
                    st.rerun()
                else:
                    st.warning(f"{add_sym} is already in your watchlist")

    watchlist = services['portfolio'].get_watchlist()

    if not watchlist:
        st.info("Your watchlist is empty. Add tickers above or via the sidebar.")
        return

    # Fetch quick quotes for the watchlist
    with st.spinner("Fetching prices…"):
        stocks_data = services['market'].get_multiple_stocks(watchlist)

    rows = []
    for sym in watchlist:
        s = stocks_data.get(sym)
        rows.append({
            "Symbol": sym,
            "Price": format_price(s.current_price) if s else "—",
            "Change %": f"{s.change_percent:+.2f}%" if s else "—",
            "In Portfolio": "✅" if sym in [p['symbol'] for p in services['portfolio'].get_all_positions()] else "—",
        })

    df = pd.DataFrame(rows)

    def _color_change(val: str) -> str:
        try:
            num = float(val.replace("%", "").replace("+", ""))
            return "color: #2ecc71" if num > 0 else "color: #e74c3c" if num < 0 else ""
        except ValueError:
            return ""

    st.dataframe(
        df.style.applymap(_color_change, subset=["Change %"]),
        use_container_width=True,
        hide_index=True,
    )

    # Remove buttons
    st.markdown("**Remove from watchlist:**")
    cols = st.columns(min(len(watchlist), 6))
    for i, sym in enumerate(watchlist):
        with cols[i % 6]:
            if st.button(f"❌ {sym}", key=f"wl_remove_{sym}", use_container_width=True):
                services['portfolio'].remove_from_watchlist(sym)
                st.session_state.watchlist = services['portfolio'].get_watchlist()
                st.rerun()


# ---------------------------------------------------------------------------
# Transaction history tab
# ---------------------------------------------------------------------------

def _render_transaction_history(services):
    st.subheader("📜 Transaction History")

    col1, col2 = st.columns(2)
    with col1:
        all_positions = services['portfolio'].get_all_positions()
        sym_options = ["All"] + [p['symbol'] for p in all_positions]
        filter_sym = st.selectbox("Filter by symbol", sym_options, key="txn_filter_sym")
    with col2:
        limit = st.slider("Show last N transactions", 10, 200, 50, key="txn_limit")

    symbol_filter = None if filter_sym == "All" else filter_sym
    txns = services['portfolio'].get_transactions(symbol=symbol_filter, limit=limit)

    if not txns:
        st.info("No transactions recorded yet.")
        return

    rows = [
        {
            "Date": t['transaction_date'],
            "Symbol": t['symbol'],
            "Type": t['transaction_type'],
            "Shares": t['shares'],
            "Price": format_price(t['price']),
            "Total": format_price(t['total_value']),
            "Notes": t.get('notes') or "",
        }
        for t in txns
    ]
    df = pd.DataFrame(rows)

    def _color_type(val: str) -> str:
        return "color: #2ecc71" if val == "BUY" else "color: #e74c3c" if val == "SELL" else ""

    st.dataframe(
        df.style.applymap(_color_type, subset=["Type"]),
        use_container_width=True,
        hide_index=True,
    )

    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Export CSV",
        data=csv,
        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    
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
