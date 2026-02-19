"""
Day Trading Tab - Intraday trading interface with 1-5 minute charts
Strategies: VWAP, Opening Range Breakout, Momentum/Gap-and-Go
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List

from services.market_data_service import MarketDataService
from services.trading_strategy_service import TradingStrategyService
from services.strategies import DAY_TRADING_STRATEGIES
from models.trading_signal import SignalType
from dashboard.components.backtest_widget import render_backtest_panel


def render_day_trading_page(services=None):
    """Render the day trading interface."""
    
    st.header("📈 Day Trading - Intraday Strategies")
    st.markdown("""
    Day trading strategies for intraday positions (minutes to hours).
    All positions are closed by end of day (EOD).
    """)
    st.warning(
        "⚠️ **Data is delayed ~15 minutes** (standard Yahoo Finance feed). "
        "Intraday signals are for **research and screening only** — "
        "do not use them as live execution signals without a real-time data source."
    )
    
    # Use shared services or create new ones as fallback
    if services:
        market_service = services['market']
        strategy_service = services['strategy']
    else:
        market_service = MarketDataService()
        strategy_service = TradingStrategyService()
    
    # Strategy selector
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        selected_strategy = st.selectbox(
            "📊 Select Day Trading Strategy",
            options=list(DAY_TRADING_STRATEGIES.keys()),
            format_func=lambda x: {
                'vwap': '🎯 VWAP Trading',
                'orb': '🔓 Opening Range Breakout',
                'momentum': '🚀 Momentum/Gap-and-Go'
            }.get(x, x),
            key="day_trading_strategy_select"
        )
    
    with col2:
        timeframe = st.selectbox(
            "⏱️ Timeframe",
            options=['1m', '5m', '15m', '30m'],
            index=1,  # Default to 5m
            key="day_trading_timeframe_select"
        )
    
    with col3:
        include_news = st.checkbox("📰 Include News", value=True, key="day_trading_include_news")
    
    # Strategy description
    strategy_descriptions = {
        'vwap': """
        **VWAP Trading Strategy**
        - Entry: Price crosses VWAP with volume confirmation
        - Exit: Mean reversion to VWAP or EOD
        - Best for: Liquid stocks with high intraday volatility
        """,
        'orb': """
        **Opening Range Breakout (ORB)**
        - Entry: Breakout of first 30-min range with volume
        - Exit: Target = 2x opening range, Stop = opposite side
        - Best for: Stocks with morning volatility
        """,
        'momentum': """
        **Momentum/Gap-and-Go Strategy**
        - Entry: Gap >2% + continued momentum (RSI, MACD)
        - Exit: Momentum exhaustion
        - Best for: Stocks with catalysts (earnings, news)
        """
    }
    
    with st.expander("ℹ️ Strategy Details"):
        st.markdown(strategy_descriptions.get(selected_strategy, ""))
    
    # Symbol input
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol = st.text_input(
            "🎯 Stock Symbol",
            value="AAPL",
            placeholder="Enter stock symbol (e.g., AAPL, TSLA, SPY)",
            key="day_trading_symbol_input"
        ).upper()
    
    with col2:
        st.write("")
        st.write("")
        scan_button = st.button("🔍 Generate Signal", type="primary", use_container_width=True)
    
    # Quick symbol buttons
    st.markdown("**Quick Select:**")
    quick_symbols = ['AAPL', 'TSLA', 'SPY', 'QQQ', 'NVDA', 'MSFT', 'AMZN', 'META']
    cols = st.columns(len(quick_symbols))
    for idx, sym in enumerate(quick_symbols):
        if cols[idx].button(sym, use_container_width=True):
            symbol = sym
            scan_button = True
    
    # Generate signal
    if scan_button and symbol:
        with st.spinner(f"🔄 Analyzing {symbol} using {selected_strategy}..."):
            signal = strategy_service.generate_signal(
                symbol=symbol,
                strategy_name=selected_strategy,
                timeframe=timeframe,
                include_news=include_news
            )
            
            if signal:
                _display_signal(signal, selected_strategy)
                _display_intraday_chart(symbol, timeframe, market_service, signal)
                # ── Inline backtest panel ─────────────────────────────────
                st.divider()
                render_backtest_panel(
                    services,
                    symbol=symbol,
                    strategy_name=selected_strategy,
                    key_prefix="day_",
                )
            else:
                st.error(f"❌ Could not generate signal for {symbol}. Please check the symbol and try again.")
    
    # Watchlist scanner
    st.divider()
    st.subheader("📋 Watchlist Scanner")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        watchlist_input = st.text_input(
            "Enter symbols (comma-separated)",
            value="AAPL,TSLA,NVDA,MSFT,GOOGL",
            placeholder="AAPL, TSLA, NVDA, MSFT",
            key="day_trading_watchlist_input"
        )
    
    with col2:
        min_confidence = st.slider("Min Confidence", 50, 90, 65, key="day_trading_min_confidence")
    
    if st.button("🔍 Scan Watchlist", use_container_width=True, key="day_trading_scan_btn"):
        watchlist = [s.strip().upper() for s in watchlist_input.split(',') if s.strip()]
        
        with st.spinner(f"Scanning {len(watchlist)} symbols..."):
            signals = strategy_service.scan_multiple_symbols(
                symbols=watchlist,
                strategy_name=selected_strategy,
                timeframe=timeframe,
                min_confidence=min_confidence
            )
            
            if signals:
                st.success(f"✅ Found {len(signals)} signals above {min_confidence}% confidence")
                _display_watchlist_results(signals)
            else:
                st.warning(f"⚠️ No signals found above {min_confidence}% confidence")


def _display_signal(signal, strategy_name: str):
    """Display the trading signal in a nice format."""
    
    # Signal header with color coding
    if signal.signal == SignalType.BUY:
        st.success("### 🟢 BUY SIGNAL")
        signal_color = "#00ff00"
    elif signal.signal == SignalType.SELL:
        st.error("### 🔴 SELL SIGNAL")
        signal_color = "#ff0000"
    else:
        st.info("### 🟡 HOLD - No Clear Signal")
        signal_color = "#ffaa00"
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Confidence", f"{signal.confidence:.1f}%")
    
    with col2:
        st.metric("Entry Price", f"${signal.entry_price:.2f}")
    
    with col3:
        st.metric("Stop Loss", f"${signal.stop_loss:.2f}")
    
    with col4:
        st.metric("Take Profit", f"${signal.target_price:.2f}")
    
    # Risk/Reward calculation
    if signal.signal in [SignalType.BUY, SignalType.SELL]:
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.target_price - signal.entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Risk per Share", f"${risk:.2f}")
        with col2:
            st.metric("Reward per Share", f"${reward:.2f}")
        with col3:
            st.metric("Risk:Reward Ratio", f"1:{risk_reward:.1f}")
    
    # Reasoning
    st.markdown("**📝 Signal Reasoning:**")
    st.info(signal.reasoning)
    
    # News analysis if available
    if signal.news_analysis:
        with st.expander("📰 News Analysis"):
            st.markdown(f"**Sentiment:** {signal.news_analysis.sentiment.value}")
            st.markdown(f"**Score:** {signal.news_analysis.sentiment_score:.2f}")
            st.markdown(f"**Relevance:** {signal.news_analysis.relevance:.0f}%")
            if signal.news_analysis.macro_impact:
                st.warning("⚠️ Macro impact detected - exercise caution")
            st.markdown(f"**Summary:** {signal.news_analysis.summary}")


def _display_intraday_chart(symbol: str, timeframe: str, market_service, signal):
    """Display intraday chart with signal markers."""
    
    st.subheader(f"📊 {symbol} - {timeframe} Chart")
    
    # Fetch intraday data
    period_map = {
        '1m': '1d',
        '5m': '5d',
        '15m': '5d',
        '30m': '5d'
    }
    
    data = market_service.get_historical_data(
        symbol,
        period=period_map.get(timeframe, '5d'),
        interval=timeframe
    )
    
    if data is None or data.empty:
        st.warning("No chart data available")
        return
    
    # Create candlestick chart
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=symbol
    ))
    
    # Add VWAP if using VWAP strategy
    if 'vwap' in signal.indicators.get('strategy', ''):
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=vwap,
            mode='lines',
            name='VWAP',
            line=dict(color='orange', width=2)
        ))
    
    # Add signal markers
    if signal.signal in [SignalType.BUY, SignalType.SELL]:
        marker_color = 'green' if signal.signal == SignalType.BUY else 'red'
        marker_symbol = 'triangle-up' if signal.signal == SignalType.BUY else 'triangle-down'
        
        fig.add_trace(go.Scatter(
            x=[data.index[-1]],
            y=[signal.entry_price],
            mode='markers',
            name='Entry',
            marker=dict(size=15, color=marker_color, symbol=marker_symbol)
        ))
        
        # Add stop loss and take profit lines
        fig.add_hline(y=signal.stop_loss, line_dash="dash", line_color="red",
                     annotation_text="Stop Loss")
        fig.add_hline(y=signal.target_price, line_dash="dash", line_color="green",
                     annotation_text="Take Profit")
    
    fig.update_layout(
        title=f"{symbol} {timeframe} Chart",
        yaxis_title="Price ($)",
        xaxis_title="Time",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _display_watchlist_results(signals: List):
    """Display watchlist scan results in a table."""
    
    # Create dataframe
    data = []
    for signal in signals:
        data.append({
            'Symbol': signal.symbol,
            'Signal': signal.signal.value,
            'Confidence': f"{signal.confidence:.1f}%",
            'Entry': f"${signal.entry_price:.2f}",
            'Stop': f"${signal.stop_loss:.2f}",
            'Target': f"${signal.target_price:.2f}",
            'Reasoning': signal.reasoning[:50] + "..." if len(signal.reasoning) > 50 else signal.reasoning
        })
    
    df = pd.DataFrame(data)
    
    # Color code signals
    def highlight_signal(val):
        if val == 'BUY':
            return 'background-color: #90EE90'
        elif val == 'SELL':
            return 'background-color: #FFB6C1'
        return ''
    
    st.dataframe(
        df.style.applymap(highlight_signal, subset=['Signal']),
        use_container_width=True,
        hide_index=True
    )
