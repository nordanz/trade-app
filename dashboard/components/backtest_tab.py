"""Backtest component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.helpers import format_price, format_percentage


def render_backtest_tab(services, watchlist):
    """Render the Backtest tab."""
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
        rsi_period = st.number_input("RSI Period", min_value=5, max_value=30, value=14)
    with col2:
        rsi_oversold = st.number_input("RSI Oversold", min_value=10, max_value=40, value=30)
    with col3:
        rsi_overbought = st.number_input("RSI Overbought", min_value=60, max_value=90, value=70)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ma_short = st.number_input("Short MA Period", min_value=5, max_value=50, value=20)
    with col2:
        ma_long = st.number_input("Long MA Period", min_value=50, max_value=200, value=50)
    with col3:
        st.metric("Strategy", "RSI + MA Crossover", "Swing Trading")
    
    # Sentiment filter
    st.subheader("📰 Sentiment Filter (Optional)")
    use_sentiment = st.checkbox("Use news sentiment filter", value=True)
    
    if use_sentiment:
        sentiment_threshold = st.slider(
            "Minimum sentiment score for BUY signals",
            min_value=-1.0,
            max_value=1.0,
            value=-0.3,
            step=0.1,
            help="Only enter BUY trades if news sentiment is above this threshold"
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
