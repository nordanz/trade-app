"""News Analysis component."""

import streamlit as st
from utils.helpers import get_sentiment_emoji


def render_news_analysis(services, selected_symbol, watchlist=None):
    """Render the News & Analysis tab."""
    st.header("🤖 AI-Powered News & Analysis")
    
    if not services['gemini'].is_available():
        st.warning("Gemini AI is not available. Please configure your API key.")
    elif not watchlist:
        st.info("Add stocks to your watchlist to see AI analysis")
    else:
        # Market summary
        st.subheader("📋 Market Summary")
        with st.spinner("Generating AI market summary..."):
            stocks_list = [services['market'].get_stock_data(s).to_dict() 
                          for s in watchlist[:5] 
                          if services['market'].get_stock_data(s)]
            
            if stocks_list:
                summary = services['gemini'].get_market_summary(stocks_list)
                st.info(summary)
        
        st.markdown("---")
        
        # Individual stock analysis
        st.subheader("📰 Stock News & Sentiment")
        
        for symbol in watchlist[:5]:  # Limit to avoid API rate limits
            with st.expander(f"📊 {symbol} Analysis", expanded=False):
                with st.spinner(f"Analyzing {symbol}..."):
                    company_info = services['market'].get_company_info(symbol)
                    company_name = company_info.get('name', symbol)
                    
                    news = services['gemini'].analyze_stock_news(symbol, company_name)
                    
                    if news:
                        sentiment_emoji = get_sentiment_emoji(news.sentiment.value)
                        
                        st.markdown(f"### {sentiment_emoji} {news.headline}")
                        st.write(news.summary)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Sentiment", news.sentiment.value)
                        with col2:
                            st.metric("Score", f"{news.sentiment_score:.2f}")
                        with col3:
                            st.metric("Relevance", f"{news.relevance:.0f}%")
                    else:
                        st.warning(f"Could not fetch analysis for {symbol}")
