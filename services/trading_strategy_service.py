"""Trading strategy service for generating buy/sell signals.

Supports:
- 3 Day Trading strategies (VWAP, ORB, Momentum)
- 3 Swing Trading strategies (Mean Reversion, Fibonacci, Breakout)
- Optional news sentiment integration
"""

import logging
import pandas as pd
from typing import Optional, Dict, List
from models.trading_signal import TradingSignal, SignalType, NewsAnalysis
from models.stock_data import StockData
from services.market_data_service import MarketDataService
from services.gemini_service import GeminiService
from services.strategies import DAY_TRADING_STRATEGIES, SWING_TRADING_STRATEGIES
from services.signal_logic import (
    vwap_signal,          VWAPParams,
    orb_signal,           ORBParams,
    momentum_signal,      MomentumParams,
    mean_reversion_signal,MeanReversionParams,
    fibonacci_signal,     FibonacciParams,
    breakout_signal,      BreakoutParams,
)
from utils.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    identify_support_resistance,
    detect_trend,
    calculate_volume_profile,
    calculate_atr,
    calculate_vwap,
    calculate_fibonacci_levels,
)
from config.settings import settings

logger = logging.getLogger(__name__)


class TradingStrategyService:
    """Service for generating trading signals and strategies."""
    
    # Map timeframes to appropriate data periods
    TIMEFRAME_PERIOD_MAP = {
        '1m': '1d',
        '5m': '5d',
        '15m': '5d',
        '30m': '5d',
        '1h': '30d',
        '1d': '1y',
    }

    # Correct timeframe for each strategy — day-trading strategies need
    # intraday bars; swing strategies need daily bars.
    STRATEGY_TIMEFRAME_MAP = {
        'vwap':           '5m',   # VWAP is an intraday concept
        'orb':            '5m',   # Opening Range needs intraday bars
        'momentum':       '5m',   # Gap/momentum needs intraday bars
        'mean_reversion': '1d',   # Bollinger mean reversion on daily
        'fibonacci':      '1d',   # Fibonacci retracement on daily
        'breakout':       '1d',   # Breakout on daily
    }
    
    def __init__(self, market_service=None, gemini_service=None):
        """Initialize trading strategy service.

        Parameters
        ----------
        market_service:
            Shared ``MarketDataService`` instance.  A new one is created when
            *None* (standalone / test usage).
        gemini_service:
            Shared ``GeminiService`` instance.  A new one is created when
            *None* (standalone / test usage).
        """
        self.market_service = market_service or MarketDataService()
        self.gemini_service = gemini_service or GeminiService()
    
    @staticmethod
    def _last_value(series_or_val, key: str = None) -> Optional[float]:
        """Safely extract the last numeric value from a Series or dict entry."""
        try:
            if key is not None:
                series_or_val = series_or_val[key]
            if hasattr(series_or_val, 'empty'):
                return float(series_or_val.iloc[-1]) if not series_or_val.empty else None
            return float(series_or_val) if series_or_val is not None else None
        except (IndexError, KeyError, TypeError, ValueError):
            return None
    
    def calculate_all_indicators(self, symbol: str, timeframe: str = "1d") -> Optional[Dict]:
        """
        Calculate all technical indicators for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            timeframe: Data timeframe ('1m', '5m', '1h', '1d')
        
        Returns:
            Dictionary with all indicators
        """
        try:
            period = self.TIMEFRAME_PERIOD_MAP.get(timeframe, '1y')
            
            hist_data = self.market_service.get_historical_data(
                symbol, period=period, interval=timeframe
            )
            
            if hist_data is None or hist_data.empty:
                return None
            
            close_prices = hist_data['Close']

            rsi = calculate_rsi(close_prices)
            macd_data = calculate_macd(close_prices)
            bollinger = calculate_bollinger_bands(close_prices)
            support, resistance = identify_support_resistance(hist_data)
            trend = detect_trend(close_prices)
            volume_data = calculate_volume_profile(hist_data)
            atr = calculate_atr(hist_data)
            vwap = calculate_vwap(hist_data)
            fibs = calculate_fibonacci_levels(hist_data)

            lv = self._last_value  # shorthand

            return {
                "rsi": lv(rsi),
                "macd": {
                    "macd": lv(macd_data, 'macd'),
                    "signal": lv(macd_data, 'signal'),
                    "histogram": lv(macd_data, 'histogram'),
                },
                "bollinger": {
                    "upper": lv(bollinger, 'upper'),
                    "middle": lv(bollinger, 'middle'),
                    "lower": lv(bollinger, 'lower'),
                },
                "support": float(support) if support else None,
                "resistance": float(resistance) if resistance else None,
                "trend": trend,
                "volume": volume_data,
                "atr": lv(atr),
                "vwap": lv(vwap),
                "fibonacci": fibs,
                "timeframe": timeframe,
            }
            
        except Exception as e:
            logger.error("Error calculating indicators for %s: %s", symbol, e)
            return None
    
    def generate_signal(self, symbol: str, strategy_name: str = "mean_reversion",
                       timeframe: str = None, include_news: bool = True) -> Optional[TradingSignal]:
        """
        Generate trading signal for a symbol using specified strategy.

        Args:
            symbol: Stock ticker symbol
            strategy_name: Strategy identifier (e.g., 'vwap', 'mean_reversion')
            timeframe: Data timeframe override. If None (default), the correct
                       timeframe is derived from strategy_name automatically:
                       day-trading strategies use '5m', swing strategies use '1d'.
            include_news: Whether to include news sentiment analysis

        Returns:
            TradingSignal object or None
        """
        try:
            # Get stock data
            stock_data = self.market_service.get_stock_data(symbol)
            if not stock_data:
                return None

            # Determine strategy type from strategy name
            if strategy_name in DAY_TRADING_STRATEGIES:
                strategy_type = "day"
            elif strategy_name in SWING_TRADING_STRATEGIES:
                strategy_type = "swing"
            else:
                strategy_type = "swing"  # Default

            # Derive the correct timeframe for this strategy unless overridden
            resolved_timeframe = timeframe or self.STRATEGY_TIMEFRAME_MAP.get(
                strategy_name, '1d'
            )

            # Calculate indicators on the strategy-appropriate timeframe
            indicators = self.calculate_all_indicators(symbol, resolved_timeframe)
            if not indicators:
                return None
            
            # Fetch news analysis if enabled
            news_analysis = None
            if include_news and self.gemini_service.is_available():
                try:
                    company_info = self.market_service.get_company_info(symbol)
                    news_analysis = self.gemini_service.analyze_stock_news(
                        symbol, 
                        company_info.get('name', symbol)
                    )
                except Exception as e:
                    logger.warning("News analysis failed for %s: %s", symbol, e)
            
            # Analyze signals based on strategy type
            signal_type, confidence, reasoning = self._analyze_signals(
                stock_data, indicators, news_analysis, strategy_type, strategy_name
            )
            
            # Calculate entry/exit points based on strategy type
            entry_price = stock_data.current_price
            raw_atr = indicators.get('atr')
            # ATR can be None when the data window is too short; fall back to 2% of price
            atr = raw_atr if (raw_atr is not None and raw_atr > 0) else entry_price * 0.02
            
            if strategy_type == "day":
                # Day trading: tighter targets and stops (1-3% moves)
                target_mult = 1.5
                stop_mult = 1.0
            else:
                # Swing trading: wider targets and stops (3-6% moves)
                target_mult = 3.0
                stop_mult = 1.5

            if signal_type == SignalType.BUY:
                target_price = entry_price + (atr * target_mult)
                stop_loss = entry_price - (atr * stop_mult)
            elif signal_type == SignalType.SELL:
                target_price = entry_price - (atr * target_mult)
                stop_loss = entry_price + (atr * stop_mult)
            else:  # HOLD
                target_price = entry_price
                stop_loss = entry_price - (atr * stop_mult)
            
            trading_signal = TradingSignal(
                symbol=symbol,
                signal=signal_type,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                holding_period="Intraday" if strategy_type == "day" else "3-7 days",
                reasoning=reasoning,
                indicators=indicators,
                news_analysis=news_analysis
            )
            
            return trading_signal
            
        except Exception as e:
            logger.error("Error generating signal for %s: %s", symbol, e)
            return None
    
    def _analyze_signals(self, stock_data: StockData, indicators: Dict, 
                         news: Optional[NewsAnalysis] = None, strategy_type: str = "swing",
                         strategy_name: str = "mean_reversion") -> tuple:
        """
        Analyze technical indicators to generate signal.
        
        Args:
            stock_data: Stock data
            indicators: Technical indicators
            news: Optional news analysis
            strategy_type: Type of strategy ("day" or "swing")
            strategy_name: Specific strategy name for detailed analysis
        
        Returns:
            Tuple of (signal_type, confidence, reasoning)
        """
        buy_signals = 0
        sell_signals = 0
        reasons = []

        rsi = indicators.get('rsi')
        macd = indicators.get('macd', {})
        trend = indicators.get('trend')
        volume = indicators.get('volume', {})
        current_price = stock_data.current_price
        
        # 1. Technical Indicators (Core)
        if rsi:
            if rsi < settings.RSI_OVERSOLD:
                buy_signals += 2
                reasons.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > settings.RSI_OVERBOUGHT:
                sell_signals += 2
                reasons.append(f"RSI overbought ({rsi:.1f})")
        
        # MACD Analysis
        macd_line = macd.get('macd')
        signal_line = macd.get('signal')
        if macd_line and signal_line:
            if macd_line > signal_line:
                buy_signals += 1
                reasons.append("MACD bullish crossover")
            else:
                sell_signals += 1
                reasons.append("MACD bearish crossover")
        
        # 2. Strategy-Specific Logic (delegates to shared signal_logic pure functions)
        atr = indicators.get('atr') or current_price * 0.02
        cur_volume = volume.get('current_volume', 0)
        avg_volume = volume.get('avg_volume', 1) or 1

        if strategy_type == "day":
            if strategy_name == "vwap":
                result = vwap_signal(
                    price=current_price,
                    vwap=indicators.get('vwap') or 0.0,
                    volume=cur_volume,
                    avg_volume=avg_volume,
                    atr=atr,
                )
                if result.direction == 'BUY':
                    buy_signals += result.confidence_votes
                    reasons.append(result.reason)
                elif result.direction == 'SELL':
                    sell_signals += result.confidence_votes
                    reasons.append(result.reason)

            elif strategy_name == "orb":
                result = orb_signal(
                    price=current_price,
                    opening_high=indicators.get('resistance') or 0.0,
                    opening_low=indicators.get('support') or 0.0,
                    volume=cur_volume,
                    avg_volume=avg_volume,
                )
                if result.direction == 'BUY':
                    buy_signals += result.confidence_votes
                    reasons.append(result.reason)
                elif result.direction == 'SELL':
                    sell_signals += result.confidence_votes
                    reasons.append(result.reason)

            elif strategy_name == "momentum":
                # Live snapshot: no prev_close available, so use a volume+RSI proxy.
                # Pass prev_close=None → function returns HOLD → apply fallback.
                macd_line = macd.get('macd')
                macd_signal_line = macd.get('signal')
                vol_ratio = volume.get('volume_ratio', 1.0)

                result = momentum_signal(
                    price=current_price,
                    prev_close=None,
                    rsi=rsi or 50.0,
                    macd_line=macd_line or 0.0,
                    macd_signal_line=macd_signal_line or 0.0,
                    volume=cur_volume,
                    avg_volume=avg_volume,
                    atr=atr,
                )
                if result.direction == 'BUY':
                    buy_signals += result.confidence_votes
                    reasons.append(result.reason)
                elif result.direction == 'SELL':
                    sell_signals += result.confidence_votes
                    reasons.append(result.reason)
                else:
                    # Fallback: volume surge + RSI confirms momentum direction
                    if rsi and rsi > 65 and vol_ratio > 1.5:
                        buy_signals += 2
                        reasons.append(
                            f"Bullish momentum: RSI {rsi:.0f}, volume {vol_ratio:.1f}x avg"
                        )
                    elif rsi and rsi < 35 and vol_ratio > 1.5:
                        sell_signals += 2
                        reasons.append(
                            f"Bearish momentum: RSI {rsi:.0f}, volume {vol_ratio:.1f}x avg"
                        )

        else:
            # Swing Trading Strategy Logic
            if strategy_name == "mean_reversion":
                bollinger = indicators.get('bollinger', {})
                result = mean_reversion_signal(
                    price=current_price,
                    bb_upper=bollinger.get('upper') or 0.0,
                    bb_middle=bollinger.get('middle') or 0.0,
                    bb_lower=bollinger.get('lower') or 0.0,
                    rsi=rsi or 50.0,
                    volume=cur_volume,
                    avg_volume=avg_volume,
                )
                if result.direction == 'BUY':
                    buy_signals += result.confidence_votes
                    reasons.append(result.reason)
                elif result.direction == 'SELL':
                    sell_signals += result.confidence_votes
                    reasons.append(result.reason)

            elif strategy_name == "fibonacci":
                fibs = indicators.get('fibonacci', {})
                is_uptrend = trend == "UPTREND"
                result = fibonacci_signal(
                    price=current_price,
                    fib_levels=fibs,
                    is_uptrend=is_uptrend,
                    volume=cur_volume,
                    avg_volume=avg_volume,
                )
                if result.direction == 'BUY':
                    buy_signals += result.confidence_votes
                    reasons.append(result.reason)
                elif result.direction == 'SELL':
                    sell_signals += result.confidence_votes
                    reasons.append(result.reason)

            elif strategy_name == "breakout":
                result = breakout_signal(
                    price=current_price,
                    resistance=indicators.get('resistance') or 0.0,
                    support=indicators.get('support') or 0.0,
                    volume=cur_volume,
                    avg_volume=avg_volume,
                    adx=None,  # ADX not pre-computed in live indicators dict
                )
                if result.direction == 'BUY':
                    buy_signals += result.confidence_votes
                    reasons.append(result.reason)
                elif result.direction == 'SELL':
                    sell_signals += result.confidence_votes
                    reasons.append(result.reason)

            # Longer-term trend context for swing trading
            if trend == "UPTREND":
                buy_signals += 1
                reasons.append("In daily uptrend")
            elif trend == "DOWNTREND":
                sell_signals += 1
                reasons.append("In daily downtrend")

        # 3. News & Noise Logic (Signal Override/Enhancement)
        if news:
            sentiment_score = news.sentiment_score
            relevance = news.relevance
            
            # High relevance news acts as a multiplier
            weight = 1.0
            if relevance > 80:
                weight = 2.0
                if news.headline:
                    reasons.append(f"High impact news")
            
            if sentiment_score > 0.4:
                buy_signals += int(2 * weight)
                reasons.append(f"Positive sentiment (+{sentiment_score:.2f})")
            elif sentiment_score < -0.4:
                sell_signals += int(2 * weight)
                reasons.append(f"Negative sentiment ({sentiment_score:.2f})")
            
            # Noise Filter: If news is extremely negative but price doesn't drop, 
            # might be a "buy the news" opportunity (divergence).
            if sentiment_score < -0.7 and stock_data.change_percent > 0:
                buy_signals += 1
                reasons.append("Sentiment/Price divergence (contrarian)")

        # Determine signal
        total_signals = buy_signals + sell_signals
        if total_signals == 0:
            return SignalType.HOLD, 50.0, "No clear technical signals"
        
        if buy_signals > sell_signals:
            confidence = min(98, 50 + (buy_signals / (total_signals + 1)) * 50)
            return SignalType.BUY, round(confidence, 1), "; ".join(reasons[:3])
        elif sell_signals > buy_signals:
            confidence = min(98, 50 + (sell_signals / (total_signals + 1)) * 50)
            return SignalType.SELL, round(confidence, 1), "; ".join(reasons[:3])
        else:
            return SignalType.HOLD, 50.0, "Conflicting signals"
    
    def scan_multiple_symbols(self, symbols: List[str], strategy_name: str = "mean_reversion",
                             timeframe: str = None, min_confidence: float = 65.0,
                             include_news: bool = True) -> List[TradingSignal]:
        """
        Scan multiple symbols for trading signals.

        Args:
            symbols: List of ticker symbols
            strategy_name: Strategy to apply
            timeframe: Data timeframe override. If None, derived from strategy_name.
            min_confidence: Minimum confidence threshold
            include_news: Whether to include news analysis

        Returns:
            List of trading signals above confidence threshold
        """
        signals = []
        
        for symbol in symbols:
            try:
                signal = self.generate_signal(
                    symbol=symbol,
                    strategy_name=strategy_name,
                    timeframe=timeframe,
                    include_news=include_news
                )
                
                if signal and signal.confidence >= min_confidence:
                    signals.append(signal)
            except Exception as e:
                logger.error("Error scanning %s: %s", symbol, e)
                continue
        
        # Sort by confidence
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return signals
    
    def get_signals_for_multiple_stocks(self, symbols: List[str], strategy_name: str = "mean_reversion",
                                       timeframe: str = None, include_news: bool = True) -> Dict[str, TradingSignal]:
        """
        Generate signals for multiple stocks.

        Convenience wrapper around scan_multiple_symbols that returns
        a dict keyed by symbol with no confidence filter.

        Args:
            symbols: List of ticker symbols
            strategy_name: Strategy to apply
            timeframe: Data timeframe override. If None, derived from strategy_name.
            include_news: Whether to include news analysis

        Returns:
            Dictionary mapping symbols to trading signals
        """
        signals = self.scan_multiple_symbols(
            symbols, strategy_name=strategy_name,
            timeframe=timeframe, min_confidence=0.0,
            include_news=include_news
        )
        return {s.symbol: s for s in signals}
    
    def filter_top_opportunities(self, signals: Dict[str, TradingSignal], limit: int = 5) -> List[TradingSignal]:
        """
        Filter and return top trading opportunities.
        
        Args:
            signals: Dictionary of trading signals
            limit: Maximum number of opportunities to return
        
        Returns:
            List of top trading signals sorted by confidence
        """
        # Filter BUY signals above minimum confidence
        buy_signals = [
            signal for signal in signals.values()
            if signal.signal == SignalType.BUY and signal.confidence >= settings.MIN_CONFIDENCE
        ]
        
        # Sort by confidence
        buy_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return buy_signals[:limit]
