"""Watchlist component."""

import streamlit as st


def render_watchlist(session_state):
    """Render the Watchlist tab."""
    st.header("⭐ Watchlist Management")
    
    st.subheader("Your Watchlist")
    
    if not session_state.watchlist:
        st.info("📭 Your watchlist is empty. Add some stocks below!")
    else:
        # Display current watchlist
        st.write("**Current Stocks:**")
        
        # Remove stocks
        col1, col2 = st.columns(2)
        with col1:
            stock_to_remove = st.selectbox("Remove from watchlist:", session_state.watchlist, key="remove_stock")
        with col2:
            if st.button("🗑️ Remove", key="remove_btn"):
                if stock_to_remove in session_state.watchlist:
                    session_state.watchlist.remove(stock_to_remove)
                    st.success(f"Removed {stock_to_remove}")
                    st.rerun()
        
        # Display as tags/chips
        st.write("**Currently watching:**")
        cols = st.columns(min(5, len(session_state.watchlist)))
        for idx, symbol in enumerate(session_state.watchlist):
            with cols[idx % len(cols)]:
                st.button(f"📍 {symbol}", key=f"stock_{symbol}", disabled=True)
    
    st.markdown("---")
    
    # Add new stock
    st.subheader("➕ Add New Stock")
    new_symbol = st.text_input("Enter stock symbol (e.g., AAPL):", key="new_stock_input").upper()
    
    if st.button("Add to Watchlist", key="add_stock_btn"):
        if new_symbol:
            if new_symbol in session_state.watchlist:
                st.warning(f"{new_symbol} is already in your watchlist")
            else:
                session_state.watchlist.append(new_symbol)
                st.success(f"✅ Added {new_symbol} to watchlist")
                st.rerun()
        else:
            st.warning("Please enter a stock symbol")
