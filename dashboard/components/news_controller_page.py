"""
News Controller Tab - Manage news sentiment parameters and impact
Allows adjusting news weight, macro event toggles, and sentiment overrides
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List

from services.gemini_service import GeminiService
from services.market_data_service import MarketDataService
from config.settings import settings


def render_news_controller_page(services=None):
    """Render the news controller interface."""
    
    st.header("📰 News Impact Controller")
    st.markdown("""
    Manage news sentiment parameters, macro events, and signal overrides.
    Control how news affects your trading signals.
    """)
    
    # Use shared services or create new ones as fallback
    if services:
        market_service = services['market']
        gemini_service = services['gemini']
    else:
        market_service = MarketDataService()
        gemini_service = GeminiService()
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ Global Settings",
        "📊 News Analysis",
        "🌍 Macro Events",
        "📈 Impact History"
    ])
    
    # ===== TAB 1: Global Settings =====
    with tab1:
        st.subheader("Global News Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**News Integration**")
            enable_news = st.toggle("Enable News Analysis", value=True, key="enable_news")
            
            news_weight = st.slider(
                "News Signal Weight",
                min_value=0,
                max_value=100,
                value=50,
                step=5,
                help="How much news sentiment affects trading signals (0-100%)",
                key="news_controller_weight_slider"
            )
            
            min_relevance = st.slider(
                "Minimum News Relevance",
                min_value=0,
                max_value=100,
                value=30,
                step=5,
                help="Filter out news below this relevance score",
                key="news_controller_relevance_slider"
            )
        
        with col2:
            st.markdown("**Sentiment Thresholds**")
            
            bullish_threshold = st.slider(
                "Bullish Sentiment Threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.4,
                step=0.1,
                help="News sentiment score to trigger BUY signals",
                key="news_controller_bullish_slider"
            )
            
            bearish_threshold = st.slider(
                "Bearish Sentiment Threshold",
                min_value=-1.0,
                max_value=0.0,
                value=-0.4,
                step=0.1,
                help="News sentiment score to trigger SELL signals",
                key="news_controller_bearish_slider"
            )
        
        st.divider()
        st.markdown("**Saved Settings:**")
        settings_summary = {
            "News Enabled": "✅" if enable_news else "❌",
            "Weight": f"{news_weight}%",
            "Min Relevance": f"{min_relevance}%",
            "Bullish Threshold": f"{bullish_threshold:.1f}",
            "Bearish Threshold": f"{bearish_threshold:.1f}"
        }
        
        for key, value in settings_summary.items():
            st.write(f"• {key}: {value}")
    
    # ===== TAB 2: News Analysis =====
    with tab2:
        st.subheader("Real-Time News Analysis")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbol = st.text_input(
                "🎯 Enter Stock Symbol",
                value="AAPL",
                placeholder="AAPL, TSLA, SPY",
                key="news_controller_symbol_input"
            ).upper()
        
        with col2:
            st.write("")
            st.write("")
            analyze_btn = st.button("🔍 Analyze News", type="primary", use_container_width=True, key="news_controller_analyze_btn")
        
        if analyze_btn and symbol:
            with st.spinner(f"📡 Fetching news for {symbol}..."):
                try:
                    if gemini_service.is_available():
                        company_info = market_service.get_company_info(symbol)
                        news_analysis = gemini_service.analyze_stock_news(
                            symbol,
                            company_info.get('name', symbol)
                        )
                        
                        if news_analysis:
                            _display_news_analysis(news_analysis, symbol)
                        else:
                            st.warning("No news analysis available")
                    else:
                        st.error("Gemini service not available. Check API key in .env")
                except Exception as e:
                    st.error(f"Error analyzing news: {str(e)}")
    
    # ===== TAB 3: Macro Events =====
    with tab3:
        st.subheader("Macro Event Management")
        
        st.markdown("**Active Macro Events** - Events affecting the broader market")
        
        # Predefined macro events
        macro_events = {
            "🪙 Central Bank Meeting": {
                "active": st.checkbox("Federal Reserve Decision", value=False, key="macro_event_fed"),
                "impact": "High",
                "date": "TBD",
                "sentiment": "Neutral"
            },
            "💰 Economic Report": {
                "active": st.checkbox("Employment/CPI Report", value=False, key="macro_event_econ"),
                "impact": "High",
                "date": "TBD",
                "sentiment": "TBD"
            },
            "⚔️ Geopolitical Crisis": {
                "active": st.checkbox("War/Sanctions", value=False, key="macro_event_geo"),
                "impact": "Critical",
                "date": "Ongoing",
                "sentiment": "Negative"
            },
            "📊 Earnings Season": {
                "active": st.checkbox("Q4/Earnings Season", value=False, key="macro_event_earnings"),
                "impact": "Medium",
                "date": "Rolling",
                "sentiment": "Variable"
            },
            "🏠 Housing/Real Estate": {
                "active": st.checkbox("Housing Decline/Crisis", value=False, key="macro_event_housing"),
                "impact": "High",
                "date": "TBD",
                "sentiment": "Negative"
            }
        }
        
        # Display active events
        col1, col2, col3, col4 = st.columns(4)
        col_headers = [col1, col2, col3, col4]
        
        header_texts = ["Event", "Impact", "Date", "Sentiment"]
        for col, header in zip(col_headers, header_texts):
            col.write(f"**{header}**")
        
        for event_name, event_data in macro_events.items():
            if event_data['active']:
                col1, col2, col3, col4 = st.columns(4)
                col1.write(f"✅ {event_name}")
                col2.write(event_data['impact'])
                col3.write(event_data['date'])
                col4.write(event_data['sentiment'])
        
        st.divider()
        st.markdown("**Signal Adjustments for Active Events**")
        
        adjustment = st.slider(
            "Volatility Multiplier",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Multiply position size and stops during macro events",
            key="news_controller_volatility_slider"
        )
        
        max_position = st.slider(
            "Max Position Size During Macro Events",
            min_value=1,
            max_value=100,
            value=50,
            step=5,
            help="Percentage of normal position size",
            key="news_controller_max_position_slider"
        )
        
        if adjustment != 1.0 or max_position != 100:
            st.info(f"⚠️ Macro mode active: Volatility multiplier {adjustment}x, Max position {max_position}%")
    
    # ===== TAB 4: Impact History =====
    with tab4:
        st.subheader("News Impact History")
        
        col1, col2 = st.columns(2)
        
        with col1:
            days = st.slider("Days to analyze", 1, 90, 7, key="news_controller_days_slider")
        
        with col2:
            symbol = st.text_input("Symbol (optional)", value="", key="news_controller_history_symbol_input")
        
        # Create sample impact history
        st.markdown("**Recent News Events & Market Impact**")
        
        # Sample data
        impact_data = {
            'Date': ['2026-02-18', '2026-02-17', '2026-02-16', '2026-02-15', '2026-02-14'],
            'Event': [
                'Fed Rate Decision',
                'CPI Report Higher',
                'Tech Earnings Beat',
                'Oil Price Spike',
                'Jobs Report Weak'
            ],
            'Sentiment': ['Neutral', 'Negative', 'Positive', 'Negative', 'Negative'],
            'Impact': ['High', 'High', 'Medium', 'High', 'High'],
            'Market Move': ['+0.5%', '-1.2%', '+1.8%', '-0.8%', '-1.5%'],
            'Stocks Affected': ['Broad', 'Bonds/Equities', 'Tech/Growth', 'Energy/Broad', 'Broad']
        }
        
        df = pd.DataFrame(impact_data)
        
        # Color code sentiment
        def color_sentiment(val):
            if val == 'Positive':
                return 'color: green'
            elif val == 'Negative':
                return 'color: red'
            else:
                return 'color: gray'
        
        def color_move(val):
            try:
                move = float(val.rstrip('%'))
                if move > 0:
                    return 'color: green'
                else:
                    return 'color: red'
            except:
                return ''
        
        st.dataframe(
            df.style
            .applymap(color_sentiment, subset=['Sentiment'])
            .applymap(color_move, subset=['Market Move']),
            use_container_width=True,
            hide_index=True
        )
        
        # Chart: Sentiment vs Market Move
        st.markdown("**Sentiment Impact on Market**")
        
        sentiment_map = {'Positive': 1, 'Neutral': 0, 'Negative': -1}
        move_values = [float(x.rstrip('%')) for x in df['Market Move']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=move_values,
            mode='lines+markers',
            name='Market Move %',
            line=dict(color='blue', width=2),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title="News Sentiment Impact on Daily Returns",
            xaxis_title="Date",
            yaxis_title="Market Move (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


def _display_news_analysis(news_analysis, symbol: str):
    """Display detailed news analysis."""
    
    st.success("### 📰 News Analysis Complete")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sentiment", news_analysis.sentiment.value)
    
    with col2:
        st.metric("Score", f"{news_analysis.sentiment_score:.2f}")
    
    with col3:
        st.metric("Relevance", f"{news_analysis.relevance:.0f}%")
    
    with col4:
        macro_text = "Yes ⚠️" if news_analysis.macro_impact else "No"
        st.metric("Macro Impact", macro_text)
    
    st.divider()
    
    st.markdown("**News Summary**")
    st.info(news_analysis.summary)
    
    if news_analysis.headline:
        st.markdown(f"**Headline:** {news_analysis.headline}")
    
    # Analysis details
    with st.expander("📊 Detailed Analysis"):
        st.markdown(f"**Symbol:** {symbol}")
        st.markdown(f"**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f"**Sentiment Value:** {news_analysis.sentiment_score:.3f}")
        st.markdown(f"**Relevance Score:** {news_analysis.relevance:.1f}%")
        
        if news_analysis.macro_impact:
            st.warning("This news may affect broader market trends beyond individual stocks")
    
    # Recommendations
    st.markdown("**Trading Recommendations**")
    
    if news_analysis.sentiment_score > 0.6:
        st.success("✅ Strongly Bullish - Consider increasing position size for BUY signals")
    elif news_analysis.sentiment_score > 0.3:
        st.info("📈 Mildly Bullish - Confirm with technical signals before entering")
    elif news_analysis.sentiment_score < -0.6:
        st.error("❌ Strongly Bearish - Reduce position size, exercise caution")
    elif news_analysis.sentiment_score < -0.3:
        st.warning("📉 Mildly Bearish - Confirm with technical signals before shorting")
    else:
        st.info("⚪ Neutral - News is not a major factor; rely on technicals")
