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

# Page configuration
st.set_page_config(
    page_title="eSignal Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Responsive layout */
    @media (max-width: 640px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }

    /* Reduce default top padding */
    .block-container {
        padding-top: 1.5rem;
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
    .positive { color: #00c853; }
    .negative { color: #d32f2f; }

    .stAlert { margin-top: 10px; }

    /* Active nav button */
    .nav-active > button {
        background-color: #0e4d92 !important;
        color: white !important;
        font-weight: bold !important;
        border-left: 4px solid #4fc3f7 !important;
    }

    /* Nav button hover */
    .stButton > button:hover {
        border-color: #4fc3f7;
    }

    /* Sidebar section labels */
    .sidebar-section {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin: 0.8rem 0 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services."""
    market  = MarketDataService()
    gemini  = GeminiService()
    return {
        "market":    market,
        "gemini":    gemini,
        "strategy":  TradingStrategyService(market_service=market, gemini_service=gemini),
        "portfolio": PortfolioDB(),
        "backtest":  BacktestService(),
    }

services = get_services()

# ── Watchlist: DB is the single source of truth ──────────────────────────────
# Seed the watchlist table with .env defaults only on first-ever install.
services['portfolio'].seed_watchlist_defaults(settings.DEFAULT_TICKERS)

# Load the persisted watchlist into session_state once per browser session.
# On subsequent reruns within the same session the value is already set.
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = services['portfolio'].get_watchlist()
# ─────────────────────────────────────────────────────────────────────────────

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
    st.title("📈 eSignal")

    # Market status
    market_status = services['market'].get_market_status()
    status_emoji = "🟢" if market_status.get('is_open') else "🔴"
    st.caption(f"{status_emoji} Market: **{market_status.get('market_state', 'UNKNOWN')}**")

    st.divider()

    # ── Grouped Navigation ────────────────────────────────────────────────────
    current = st.session_state.current_page

    nav_groups = {
        "MARKET": {
            "Market Overview": "📊 Market Overview",
            "Detailed Charts": "� Charts",
        },
        "TRADING": {
            "Trading Signals": "🎯 Signals",
            "Day Trading":     "⚡ Day Trading",
            "Swing Trading":   "🌊 Swing Trading",
        },
        "RESEARCH": {
            "AI News & Analysis": "🤖 AI News",
            "News Controller":    "🎛️ News Settings",
        },
        "ACCOUNT": {
            "My Portfolio": "💼 Portfolio",
            "Backtest":     "🧪 Backtest",
        },
        "HELP": {
            "Beginner's Guide": "📚 Beginner's Guide",
        },
    }

    for group_label, pages in nav_groups.items():
        st.markdown(f"<p class='sidebar-section'>{group_label}</p>", unsafe_allow_html=True)
        for key, label in pages.items():
            is_active = current == key
            container = st.container()
            if is_active:
                container.markdown("<span class='nav-active'>", unsafe_allow_html=True)
            if container.button(
                f"{'▶ ' if is_active else ''}{label}",
                key=f"nav_{key}",
                use_container_width=True,
            ):
                st.session_state.current_page = key
                st.rerun()
            if is_active:
                container.markdown("</span>", unsafe_allow_html=True)

    st.divider()

    # ── Watchlist ─────────────────────────────────────────────────────────────
    st.markdown("<p class='sidebar-section'>WATCHLIST</p>", unsafe_allow_html=True)

    # Add new ticker
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        new_ticker = st.text_input(
            "Ticker",
            placeholder="e.g. AAPL",
            label_visibility="collapsed",
            key="sidebar_add_ticker_input",
        ).upper()
    with col_btn:
        st.write("")  # vertical alignment nudge
        add_clicked = st.button("＋", key="sidebar_add_ticker_btn", use_container_width=True)

    if add_clicked:
        if new_ticker:
            added = services['portfolio'].add_to_watchlist(new_ticker)
            if added:
                st.session_state.watchlist = services['portfolio'].get_watchlist()
                st.rerun()
            else:
                st.warning(f"{new_ticker} already in watchlist")
        else:
            st.warning("Enter a ticker symbol")

    # Watchlist items
    for ticker in st.session_state.watchlist:
        col1, col2 = st.columns([4, 1])
        with col1:
            is_selected = ticker == st.session_state.selected_symbol
            label = f"**{ticker}**" if is_selected else ticker
            if st.button(label, key=f"select_{ticker}", use_container_width=True):
                st.session_state.selected_symbol = ticker
        with col2:
            if st.button("✕", key=f"remove_{ticker}"):
                services['portfolio'].remove_from_watchlist(ticker)
                st.session_state.watchlist = services['portfolio'].get_watchlist()
                st.rerun()

    st.divider()

    # ── Settings ──────────────────────────────────────────────────────────────
    st.markdown("<p class='sidebar-section'>SETTINGS</p>", unsafe_allow_html=True)
    auto_refresh = st.checkbox(
        "Auto-refresh",
        value=st.session_state.auto_refresh,
        key="sidebar_auto_refresh_checkbox",
    )
    st.session_state.auto_refresh = auto_refresh

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Refresh", key="sidebar_refresh_btn", use_container_width=True):
            st.rerun()
    with col_r2:
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

# ── Top status bar (replaces the heavy title block) ──────────────────────────
page = st.session_state.current_page
_page_title = {
    "Market Overview":    "📊 Market Overview",
    "My Portfolio":       "� My Portfolio",
    "Backtest":           "🧪 Backtest",
    "AI News & Analysis": "🤖 AI News & Analysis",
    "Trading Signals":    "🎯 Trading Signals",
    "Detailed Charts":    "📈 Detailed Charts",
    "Day Trading":        "⚡ Day Trading",
    "Swing Trading":      "🌊 Swing Trading",
    "News Controller":    "🎛️ News Controller",
    "Beginner's Guide":   "📚 Beginner's Guide",
}.get(page, page)

col_title, col_warn = st.columns([3, 2])
with col_title:
    st.markdown(f"## {_page_title}")
with col_warn:
    if not services['gemini'].is_available():
        st.warning("⚠️ Gemini AI not configured — set GEMINI_API_KEY in .env")

st.divider()

if page == "Market Overview":
    render_market_overview(services, st.session_state.watchlist)

elif page == "My Portfolio":
    render_portfolio_management(services)

elif page == "Backtest":
    render_backtest_page(services, st.session_state.watchlist)

elif page == "AI News & Analysis":
    render_news_analysis(services, st.session_state.selected_symbol, st.session_state.watchlist)

elif page == "Trading Signals":
    render_trading_signals(services, st.session_state.watchlist)

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
