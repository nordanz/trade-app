"""News Analysis component."""

import streamlit as st
from utils.helpers import get_sentiment_emoji


def render_news_analysis(services, selected_symbol, watchlist=None):
    """Render the News & Analysis tab."""

    if not services['gemini'].is_available():
        st.warning("Gemini AI is not available. Please configure your API key.")
        return
    if not watchlist:
        st.info("Add stocks to your watchlist to see AI analysis")
        return

    symbols = watchlist[:5]
    _cache_key = ','.join(symbols)
    _stale = st.session_state.get('news_cache_key') != _cache_key

    if st.button("🔄 Fetch AI Analysis", type="primary", use_container_width=True, key="news_fetch_btn") or _stale:
        results = {}

        # Market summary
        with st.spinner("Generating AI market summary…"):
            stocks_list = [services['market'].get_stock_data(s).to_dict()
                           for s in symbols
                           if services['market'].get_stock_data(s)]
            results['summary'] = services['gemini'].get_market_summary(stocks_list) if stocks_list else None

        # Per-stock analysis
        per_stock = {}
        for symbol in symbols:
            with st.spinner(f"Analyzing {symbol}…"):
                company_info = services['market'].get_company_info(symbol)
                company_name = company_info.get('name', symbol)
                per_stock[symbol] = services['gemini'].analyze_stock_news(symbol, company_name)
        results['per_stock'] = per_stock

        st.session_state['news_results'] = results
        st.session_state['news_cache_key'] = _cache_key

    results = st.session_state.get('news_results')
    if not results:
        st.info("Click **Fetch AI Analysis** to load market insights.")
        return

    # Market summary
    st.subheader("📋 Market Summary")
    if results.get('summary'):
        st.info(results['summary'])

    st.markdown("---")

    # Individual stock analysis
    st.subheader("📰 Stock News & Sentiment")
    for symbol, news in results.get('per_stock', {}).items():
        with st.expander(f"📊 {symbol} Analysis", expanded=False):
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
