"""Main Streamlit dashboard application - Menu-based layout for mobile-friendly experience."""

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
from dashboard.components.backtest_page import render_backtest_page
from dashboard.components.day_trading_page import render_day_trading_page
from dashboard.components.swing_trading_page import render_swing_trading_page
from dashboard.components.news_controller_page import render_news_controller_page
from dashboard.components.beginner_guide_page import render_beginner_guide_page

# Page configuration - centered layout for better mobile experience
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile-friendly responsive design
st.markdown("""
<style>
    /* Responsive layout */
    @media (max-width: 640px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    /* Typography */
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    
    /* Cards */
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    /* Colors */
    .positive {
        color: #00ff00;
    }
    
    .negative {
        color: #ff0000;
    }
    
    .stAlert {
        margin-top: 10px;
    }
    
    /* Improve button appearance on mobile */
    .stButton > button {
        width: 100%;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding: 1rem;
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
        "backtest": BacktestService(),
    }

services = get_services()

# Initialize session state
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = settings.DEFAULT_TICKERS.copy()

if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = st.session_state.watchlist[0] if st.session_state.watchlist else "AAPL"

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Market Overview"

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Auto-refresh
if st.session_state.get('auto_refresh', True):
    st_autorefresh(interval=settings.REFRESH_INTERVAL * 1000, key="datarefresh")

# Sidebar navigation and controls
with st.sidebar:
    st.title("� Trading Dashboard")
    
    # Market status
    market_status = services['market'].get_market_status()
    status_emoji = "🟢" if market_status.get('is_open') else "🔴"
    st.info(f"{status_emoji} Market: {market_status.get('market_state', 'UNKNOWN')}")
    
    st.markdown("---")
    
    # Main Navigation Menu
    st.subheader("📍 Navigation")
    
    menu_pages = {
        "Market Overview": "📊 Market Overview",
        "My Portfolio": "💼 My Portfolio",
        "Backtest": "🧪 Backtest",
        "AI News & Analysis": "📰 AI News & Analysis",
        "Trading Signals": "🎯 Trading Signals",
        "Detailed Charts": "📈 Detailed Charts",
        "Day Trading": "📈 Day Trading",
        "Swing Trading": "🌊 Swing Trading",
        "News Controller": "📰 News Controller",
        "Beginner's Guide": "📚 Beginner's Guide"
    }
    
    for key, label in menu_pages.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()
    
    st.markdown("---")
    
    # Watchlist management
    st.subheader("📋 Watchlist")
    
    # Add new ticker
    new_ticker = st.text_input(
        "Add Ticker:",
        placeholder="e.g., AAPL",
        key="sidebar_add_ticker_input"
    ).upper()
    if st.button("➕ Add", key="sidebar_add_ticker_btn", use_container_width=True):
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
            if st.button(f"• {ticker}", key=f"select_{ticker}", use_container_width=True):
                st.session_state.selected_symbol = ticker
        with col2:
            if st.button("❌", key=f"remove_{ticker}"):
                st.session_state.watchlist.remove(ticker)
                st.rerun()
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    auto_refresh = st.checkbox(
        "Auto-refresh",
        value=st.session_state.auto_refresh,
        key="sidebar_auto_refresh_checkbox"
    )
    st.session_state.auto_refresh = auto_refresh
    
    if st.button("🔄 Refresh Now", key="sidebar_refresh_btn", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Main content area
st.title("📈 Stock Market Dashboard with AI")
st.markdown("**Live market data • AI-powered insights • Swing trading recommendations**")

# Check if Gemini is configured
if not services['gemini'].is_available():
    st.warning("⚠️ Gemini AI not configured. Set GEMINI_API_KEY in .env file for AI features.")

st.markdown("---")

# Route to current page
page = st.session_state.current_page

if page == "Market Overview":
    render_market_overview(services, st.session_state.watchlist)

elif page == "My Portfolio":
    render_portfolio_management(services)

elif page == "Backtest":
    render_backtest_page(services, st.session_state.watchlist)

elif page == "AI News & Analysis":
    render_news_analysis(services, st.session_state.selected_symbol, st.session_state.watchlist)

elif page == "Trading Signals":
    render_trading_signals(services, st.session_state.selected_symbol, st.session_state.watchlist)

elif page == "Detailed Charts":
    render_detailed_charts(services, st.session_state.watchlist)

elif page == "Day Trading":
    render_day_trading_page(services)

elif page == "Swing Trading":
    render_swing_trading_page(services)

elif page == "News Controller":
    render_news_controller_page(services)

elif page == "Beginner's Guide":
    render_beginner_guide_page()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>⚠️ Disclaimer:</strong> This dashboard is for educational purposes only. Not financial advice.
    Always do your own research before making investment decisions.</p>
    <p>Data provided by Yahoo Finance • AI powered by Google Gemini</p>
</div>
""", unsafe_allow_html=True)
