"""Charts component."""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.helpers import format_price


def render_detailed_charts(services, watchlist):
    """Render the Detailed Charts tab."""
    
    if not watchlist:
        st.info("Add stocks to your watchlist to see charts")
    else:
        selected_symbol = st.selectbox("Select Stock:", watchlist, key="charts_symbol_select")
        
        if selected_symbol:
            with st.spinner(f"Loading chart for {selected_symbol}..."):
                hist_data = services['market'].get_historical_data(selected_symbol, period="3mo")
                
                if not hist_data.empty:
                    # Create candlestick chart
                    fig = make_subplots(
                        rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        subplot_titles=(f'{selected_symbol} Price', 'Volume'),
                        row_width=[0.7, 0.3]
                    )
                    
                    # Candlestick
                    fig.add_trace(
                        go.Candlestick(
                            x=hist_data.index,
                            open=hist_data['Open'],
                            high=hist_data['High'],
                            low=hist_data['Low'],
                            close=hist_data['Close'],
                            name='Price'
                        ),
                        row=1, col=1
                    )
                    
                    # Moving averages
                    ma_20 = hist_data['Close'].rolling(window=20).mean()
                    ma_50 = hist_data['Close'].rolling(window=50).mean()
                    
                    fig.add_trace(
                        go.Scatter(x=hist_data.index, y=ma_20, name='MA20',
                                  line=dict(color='orange', width=1)),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(x=hist_data.index, y=ma_50, name='MA50',
                                  line=dict(color='blue', width=1)),
                        row=1, col=1
                    )
                    
                    # Volume
                    colors = ['red' if close < open else 'green' 
                             for close, open in zip(hist_data['Close'], hist_data['Open'])]
                    
                    fig.add_trace(
                        go.Bar(x=hist_data.index, y=hist_data['Volume'],
                              name='Volume', marker_color=colors),
                        row=2, col=1
                    )
                    
                    # Update layout
                    fig.update_layout(
                        title=f"{selected_symbol} - 3 Month Chart",
                        yaxis_title='Price ($)',
                        xaxis_rangeslider_visible=False,
                        height=700,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Technical indicators for selected stock
                    st.subheader("📊 Technical Indicators")
                    indicators = services['strategy'].calculate_all_indicators(selected_symbol)
                    
                    if indicators:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            rsi = indicators.get('rsi')
                            st.metric("RSI", f"{rsi:.1f}" if rsi else "N/A")
                        
                        with col2:
                            macd_data = indicators.get('macd', {})
                            macd_val = macd_data.get('macd')
                            st.metric("MACD", f"{macd_val:.2f}" if macd_val else "N/A")
                        
                        with col3:
                            trend = indicators.get('trend', 'N/A')
                            st.metric("Trend", trend)
                        
                        with col4:
                            support = indicators.get('support')
                            st.metric("Support", format_price(support) if support else "N/A")
                else:
                    st.error(f"Unable to load chart data for {selected_symbol}")
