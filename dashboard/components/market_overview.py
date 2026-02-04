"""Market Overview component."""

import streamlit as st
from utils.helpers import format_price, format_percentage, format_large_number


def render_market_overview(services, watchlist):
    """Render the Market Overview tab."""
    st.header("Live Market Data")
    
    if not watchlist:
        st.info("👆 Add stocks to your watchlist using the sidebar")
    else:
        # Fetch data for all stocks
        with st.spinner("Fetching market data..."):
            stocks_data = services['market'].get_multiple_stocks(watchlist)
        
        if not stocks_data:
            st.error("Unable to fetch market data. Please check your internet connection.")
        else:
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_stocks = len(stocks_data)
                st.metric("Stocks Tracked", total_stocks)
            
            with col2:
                gainers = sum(1 for s in stocks_data.values() if s.change_percent > 0)
                st.metric("Gainers", gainers, delta=f"{gainers}/{total_stocks}")
            
            with col3:
                losers = sum(1 for s in stocks_data.values() if s.change_percent < 0)
                st.metric("Losers", losers, delta=f"{losers}/{total_stocks}")
            
            with col4:
                avg_change = sum(s.change_percent for s in stocks_data.values()) / len(stocks_data)
                st.metric("Avg Change", format_percentage(avg_change))
            
            st.markdown("---")
            
            # Display stocks in cards
            for symbol, stock in stocks_data.items():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
                    
                    with col1:
                        st.markdown(f"### {symbol}")
                        change_color = "🟢" if stock.change_percent >= 0 else "🔴"
                        st.markdown(f"{change_color} **{format_price(stock.current_price)}**")
                    
                    with col2:
                        st.metric("Change", format_percentage(stock.change_percent))
                    
                    with col3:
                        st.metric("Volume", format_large_number(stock.volume))
                    
                    with col4:
                        st.metric("Market Cap", format_large_number(stock.market_cap))
                    
                    with col5:
                        st.metric("P/E Ratio", f"{stock.pe_ratio:.2f}" if stock.pe_ratio else "N/A")
                    
                    # Moving averages
                    if stock.moving_averages:
                        ma_cols = st.columns(3)
                        for i, (key, value) in enumerate(stock.moving_averages.items()):
                            if value:
                                ma_cols[i].caption(f"{key.upper()}: {format_price(value)}")
                    
                    st.markdown("---")
