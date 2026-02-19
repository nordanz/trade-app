"""
Swing Trading Tab - Multi-day trading interface with daily charts
Strategies: Mean Reversion, Fibonacci Retracement, Breakout Trading
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List

from services.market_data_service import MarketDataService
from services.trading_strategy_service import TradingStrategyService
from services.strategies import SWING_TRADING_STRATEGIES
from models.trading_signal import SignalType
from dashboard.components.backtest_widget import render_backtest_panel


def render_swing_trading_page(services=None):
    """Render the swing trading interface."""
    
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
            "📊 Select Swing Trading Strategy",
            options=list(SWING_TRADING_STRATEGIES.keys()),
            format_func=lambda x: {
                'mean_reversion': '↩️ Mean Reversion (Bollinger Bands)',
                'fibonacci': '📐 Fibonacci Retracement',
                'breakout': '💥 Breakout Trading'
            }.get(x, x),
            key="swing_trading_strategy_select"
        )
    
    with col2:
        period = st.selectbox(
            "📅 Chart Period",
            options=['1mo', '3mo', '6mo', '1y'],
            index=1,  # Default to 3mo
            key="swing_trading_period_select"
        )
    
    with col3:
        include_news = st.checkbox("📰 News", value=True, key="swing_trading_include_news")
    
    # Strategy description
    strategy_descriptions = {
        'mean_reversion': """
        **Mean Reversion (Bollinger Bands)**
        - Entry: Price at BB extremes + RSI oversold/overbought
        - Exit: Reversion to middle band
        - Best for: Range-bound stocks with clear support/resistance
        """,
        'fibonacci': """
        **Fibonacci Retracement**
        - Entry: Pullback to 38.2%, 50%, or 61.8% Fib level
        - Exit: Extension to 1.618 or trend reversal
        - Best for: Trending stocks with clear swing highs/lows
        """,
        'breakout': """
        **Breakout Trading**
        - Entry: Break above/below support/resistance with volume
        - Exit: 2x risk target or trailing ATR stop
        - Best for: Consolidating stocks before strong moves
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
            key="swing_trading_symbol_input"
        ).upper()
    
    with col2:
        st.write("")
        st.write("")
        scan_button = st.button("🔍 Generate Signal", type="primary", use_container_width=True)
    
    # Quick symbol buttons
    st.markdown("**Quick Select:**")
    quick_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMZN']
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
                timeframe='1d',
                include_news=include_news
            )
            if signal:
                st.session_state['swing_trading_signal'] = signal
                st.session_state['swing_trading_signal_symbol'] = symbol
                st.session_state['swing_trading_signal_strategy'] = selected_strategy
                st.session_state['swing_trading_signal_period'] = period
            else:
                st.session_state.pop('swing_trading_signal', None)
                st.error(f"❌ Could not generate signal for {symbol}. Please check the symbol and try again.")

    # Display persisted signal (survives reruns / auto-refresh)
    if 'swing_trading_signal' in st.session_state:
        cached_signal = st.session_state['swing_trading_signal']
        cached_symbol = st.session_state.get('swing_trading_signal_symbol', symbol)
        cached_strategy = st.session_state.get('swing_trading_signal_strategy', selected_strategy)
        cached_period = st.session_state.get('swing_trading_signal_period', period)
        _display_signal(cached_signal, cached_strategy)
        _display_daily_chart(cached_symbol, cached_period, market_service, cached_signal, cached_strategy)
        # ── Inline backtest panel ─────────────────────────────────
        st.divider()
        render_backtest_panel(
            services,
            symbol=cached_symbol,
            strategy_name=cached_strategy,
            key_prefix="swing_",
        )
    
    # Watchlist scanner
    st.divider()
    st.subheader("📋 Swing Trading Scanner")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        watchlist_input = st.text_input(
            "Enter symbols (comma-separated)",
            value="SPY,QQQ,IWM,DIA,AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA",
            placeholder="SPY, QQQ, AAPL, MSFT",
            key="swing_trading_watchlist_input"
        )
    
    with col2:
        min_confidence = st.slider("Min Confidence", 50, 90, 70, key="swing_trading_min_confidence")
    
    if st.button("🔍 Scan Watchlist", use_container_width=True, key="swing_trading_scan_btn"):
        watchlist = [s.strip().upper() for s in watchlist_input.split(',') if s.strip()]
        
        with st.spinner(f"Scanning {len(watchlist)} symbols..."):
            signals = strategy_service.scan_multiple_symbols(
                symbols=watchlist,
                strategy_name=selected_strategy,
                timeframe='1d',
                min_confidence=min_confidence
            )
            if signals:
                st.session_state['swing_trading_scan_signals'] = signals
                st.session_state['swing_trading_scan_confidence'] = min_confidence
            else:
                st.session_state.pop('swing_trading_scan_signals', None)
                st.warning(f"⚠️ No signals found above {min_confidence}% confidence")

    # Display persisted scan results (survives reruns / auto-refresh)
    if 'swing_trading_scan_signals' in st.session_state:
        cached_signals = st.session_state['swing_trading_scan_signals']
        cached_conf = st.session_state.get('swing_trading_scan_confidence', min_confidence)
        st.success(f"✅ Found {len(cached_signals)} signals above {cached_conf}% confidence")
        _display_watchlist_results(cached_signals)


def _display_signal(signal, strategy_name: str):
    """Display the trading signal in a nice format."""
    
    # Signal header with color coding
    if signal.signal == SignalType.BUY:
        st.success("### 🟢 BUY SIGNAL")
    elif signal.signal == SignalType.SELL:
        st.error("### 🔴 SELL SIGNAL")
    else:
        st.info("### 🟡 HOLD - No Clear Signal")
    
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
        
        risk_pct = (risk / signal.entry_price) * 100
        reward_pct = (reward / signal.entry_price) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Risk", f"${risk:.2f} ({risk_pct:.1f}%)")
        with col2:
            st.metric("Reward", f"${reward:.2f} ({reward_pct:.1f}%)")
        with col3:
            st.metric("R:R Ratio", f"1:{risk_reward:.2f}")
        with col4:
            holding_period = "3-7 days"
            st.metric("Hold Period", holding_period)
    
    # Reasoning
    st.markdown("**📝 Signal Reasoning:**")
    st.info(signal.reasoning)
    
    # News analysis if available
    if signal.news_analysis:
        with st.expander("📰 News Analysis"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Sentiment:** {signal.news_analysis.sentiment.value}")
            with col2:
                st.markdown(f"**Score:** {signal.news_analysis.sentiment_score:.2f}")
            with col3:
                st.markdown(f"**Relevance:** {signal.news_analysis.relevance:.0f}%")
            
            if signal.news_analysis.macro_impact:
                st.warning("⚠️ **Macro Impact Detected** - This news may affect broader market trends")
            
            st.markdown(f"**Summary:**")
            st.markdown(signal.news_analysis.summary)


def _display_daily_chart(symbol: str, period: str, market_service, signal, strategy_name: str):
    """Display daily chart with indicators and signal markers."""
    
    st.subheader(f"📊 {symbol} - Daily Chart ({period})")
    
    # Fetch daily data
    data = market_service.get_historical_data(
        symbol,
        period=period,
        interval='1d'
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
    
    # Add strategy-specific indicators
    if 'mean_reversion' in strategy_name:
        # Bollinger Bands
        close = data['Close']
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        fig.add_trace(go.Scatter(x=data.index, y=bb_upper, mode='lines', 
                                name='BB Upper', line=dict(color='gray', dash='dash')))
        fig.add_trace(go.Scatter(x=data.index, y=bb_middle, mode='lines',
                                name='BB Middle', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=data.index, y=bb_lower, mode='lines',
                                name='BB Lower', line=dict(color='gray', dash='dash')))
    
    elif 'fibonacci' in strategy_name:
        # Fibonacci levels
        recent_high = data['High'].tail(50).max()
        recent_low = data['Low'].tail(50).min()
        diff = recent_high - recent_low
        
        fib_levels = {
            '0%': recent_high,
            '23.6%': recent_high - (diff * 0.236),
            '38.2%': recent_high - (diff * 0.382),
            '50%': recent_high - (diff * 0.5),
            '61.8%': recent_high - (diff * 0.618),
            '100%': recent_low
        }
        
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
        for idx, (level, price) in enumerate(fib_levels.items()):
            fig.add_hline(y=price, line_dash="dot", line_color=colors[idx],
                         annotation_text=f"Fib {level}")
    
    elif 'breakout' in strategy_name:
        # Support and Resistance
        recent_high = data['High'].tail(20).max()
        recent_low = data['Low'].tail(20).min()
        
        fig.add_hline(y=recent_high, line_dash="dash", line_color="red",
                     annotation_text="Resistance")
        fig.add_hline(y=recent_low, line_dash="dash", line_color="green",
                     annotation_text="Support")
    
    # Add moving averages
    sma_20 = data['Close'].rolling(window=20).mean()
    sma_50 = data['Close'].rolling(window=50).mean()
    
    fig.add_trace(go.Scatter(x=data.index, y=sma_20, mode='lines',
                            name='SMA 20', line=dict(color='blue', width=1)))
    fig.add_trace(go.Scatter(x=data.index, y=sma_50, mode='lines',
                            name='SMA 50', line=dict(color='purple', width=1)))
    
    # Add signal markers
    if signal.signal in [SignalType.BUY, SignalType.SELL]:
        marker_color = 'green' if signal.signal == SignalType.BUY else 'red'
        marker_symbol = 'triangle-up' if signal.signal == SignalType.BUY else 'triangle-down'
        
        fig.add_trace(go.Scatter(
            x=[data.index[-1]],
            y=[signal.entry_price],
            mode='markers+text',
            name='Entry',
            marker=dict(size=20, color=marker_color, symbol=marker_symbol),
            text=['ENTRY'],
            textposition='top center'
        ))
        
        # Add stop loss and take profit lines
        fig.add_hline(y=signal.stop_loss, line_dash="dash", line_color="red",
                     annotation_text=f"Stop: ${signal.stop_loss:.2f}", annotation_position="right")
        fig.add_hline(y=signal.target_price, line_dash="dash", line_color="green",
                     annotation_text=f"Target: ${signal.target_price:.2f}", annotation_position="right")
    
    # Volume subplot
    colors = ['red' if close < open else 'green' 
              for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(go.Bar(
        x=data.index,
        y=data['Volume'],
        name='Volume',
        marker_color=colors,
        yaxis='y2',
        opacity=0.3
    ))
    
    fig.update_layout(
        title=f"{symbol} Daily Chart - {strategy_name.replace('_', ' ').title()}",
        yaxis_title="Price ($)",
        yaxis2=dict(title="Volume", overlaying='y', side='right'),
        xaxis_title="Date",
        height=600,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _display_watchlist_results(signals: List):
    """Display watchlist scan results in a table."""
    
    # Create dataframe
    data = []
    for signal in signals:
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.target_price - signal.entry_price)
        rr = reward / risk if risk > 0 else 0
        
        data.append({
            'Symbol': signal.symbol,
            'Signal': signal.signal.value,
            'Confidence': f"{signal.confidence:.1f}%",
            'Entry': f"${signal.entry_price:.2f}",
            'Stop': f"${signal.stop_loss:.2f}",
            'Target': f"${signal.target_price:.2f}",
            'R:R': f"1:{rr:.1f}",
            'Reasoning': signal.reasoning[:60] + "..." if len(signal.reasoning) > 60 else signal.reasoning
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
    
    # Export options
    col1, col2 = st.columns([1, 4])
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export CSV",
            data=csv,
            file_name=f"swing_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
