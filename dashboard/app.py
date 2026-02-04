"""Main Streamlit dashboard application."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Import services
from services.market_data_service import MarketDataService
from services.gemini_service import GeminiService
from services.trading_strategy_service import TradingStrategyService
from services.portfolio_service import PortfolioDB
from services.backtest_service import BacktestService
from config.settings import settings

# Import components
from dashboard.components.market_overview import render_market_overview
from dashboard.components.portfolio_management import render_portfolio_management
from dashboard.components.trading_signals import render_trading_signals
from dashboard.components.news_analysis import render_news_analysis
from dashboard.components.charts import render_detailed_charts
from dashboard.components.watchlist import render_watchlist
from dashboard.components.backtest_tab import render_backtest_tab

# Page configuration
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive {
        color: #00ff00;
    }
    .negative {
        color: #ff0000;
    }
    .stAlert {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services."""
    return {
        "market": MarketDataService(),
        "gemini": GeminiService(),
        "strategy": TradingStrategyService(),
        "portfolio": PortfolioDB(),
        "backtest": BacktestService()
    }

services = get_services()

# Initialize session state
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = settings.DEFAULT_TICKERS.copy()

if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = st.session_state.watchlist[0] if st.session_state.watchlist else "AAPL"

# Auto-refresh
if st.session_state.get('auto_refresh', True):
    st_autorefresh(interval=settings.REFRESH_INTERVAL * 1000, key="datarefresh")

# Sidebar
with st.sidebar:
    st.title("📊 Dashboard Controls")
    
    # Market status
    market_status = services['market'].get_market_status()
    status_emoji = "🟢" if market_status.get('is_open') else "🔴"
    st.info(f"{status_emoji} Market: {market_status.get('market_state', 'UNKNOWN')}")
    
    st.markdown("---")
    
    # Watchlist management
    st.subheader("📋 Watchlist")
    
    # Add new ticker
    new_ticker = st.text_input("Add Ticker:", placeholder="e.g., AAPL").upper()
    if st.button("➕ Add to Watchlist"):
        if new_ticker and new_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_ticker)
            st.success(f"Added {new_ticker}")
            st.rerun()
        elif new_ticker in st.session_state.watchlist:
            st.warning(f"{new_ticker} already in watchlist")
    
    # Display watchlist
    st.markdown("**Current Watchlist:**")
    for ticker in st.session_state.watchlist:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"• {ticker}")
        with col2:
            if st.button("❌", key=f"remove_{ticker}"):
                st.session_state.watchlist.remove(ticker)
                st.rerun()
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    st.session_state.auto_refresh = auto_refresh
    
    if st.button("🔄 Refresh Now"):
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Main content
st.title("📈 Stock Market Dashboard with AI")
st.markdown("**Live market data • AI-powered insights • Swing trading recommendations**")

# Check if Gemini is configured
if not services['gemini'].is_available():
    st.warning("⚠️ Gemini AI not configured. Set GEMINI_API_KEY in .env file for AI features.")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Market Overview",
    "💼 My Portfolio",
    "🧪 Backtest",
    "📰 AI News & Analysis",
    "🎯 Trading Signals",
    "📈 Detailed Charts"
])

# Render each tab using components
with tab1:
    render_market_overview(services, st.session_state.watchlist)

with tab2:
    render_portfolio_management(services)

with tab3:
    render_backtest_tab(services, st.session_state.watchlist)

with tab4:
    render_news_analysis(services, st.session_state.selected_symbol, st.session_state.watchlist)

with tab5:
    render_trading_signals(services, st.session_state.selected_symbol, st.session_state.watchlist)

with tab6:
    render_detailed_charts(services, st.session_state.watchlist)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>⚠️ Disclaimer:</strong> This dashboard is for educational purposes only. Not financial advice.
    Always do your own research before making investment decisions.</p>
    <p>Data provided by Yahoo Finance • AI powered by Google Gemini</p>
</div>
""", unsafe_allow_html=True)
