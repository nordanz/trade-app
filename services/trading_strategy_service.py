"""Trading strategy service for generating buy/sell signals."""

import pandas as pd
from typing import Optional, Dict, List
from models.trading_signal import TradingSignal, SignalType, NewsAnalysis
from models.stock_data import StockData
from services.market_data_service import MarketDataService
from services.gemini_service import GeminiService
from utils.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    identify_support_resistance,
    detect_trend,
    calculate_volume_profile,
    is_golden_cross,
    is_death_cross,
    calculate_atr,
    calculate_vwap,
    calculate_pivot_points,
    calculate_fibonacci_levels
)
from config.settings import settings


class TradingStrategyService:
    """Service for generating trading signals and strategies."""
    
    def __init__(self):
        """Initialize trading strategy service."""
        self.market_service = MarketDataService()
        self.gemini_service = GeminiService()
    
    def calculate_all_indicators(self, symbol: str) -> Optional[Dict]:
        """
        Calculate all technical indicators for a symbol.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dictionary with all indicators
        """
        try:
            # Get historical data
            hist_data = self.market_service.get_historical_data(
                symbol,
                period=settings.HISTORICAL_PERIOD,
                interval=settings.DATA_INTERVAL
            )
            
            if hist_data.empty:
                return None
            
            close_prices = hist_data['Close']
            
            # Calculate indicators
            rsi = calculate_rsi(close_prices)
            macd_data = calculate_macd(close_prices)
            bollinger = calculate_bollinger_bands(close_prices)
            support, resistance = identify_support_resistance(hist_data)
            trend = detect_trend(close_prices)
            volume_data = calculate_volume_profile(hist_data)
            golden = is_golden_cross(close_prices)
            death = is_death_cross(close_prices)
            atr = calculate_atr(hist_data)
            vwap = calculate_vwap(hist_data)
            pivots = calculate_pivot_points(hist_data)
            fibs = calculate_fibonacci_levels(hist_data)
            
            indicators = {
                "rsi": float(rsi.iloc[-1]) if not rsi.empty else None,
                "macd": {
                    "macd": float(macd_data['macd'].iloc[-1]) if not macd_data['macd'].empty else None,
                    "signal": float(macd_data['signal'].iloc[-1]) if not macd_data['signal'].empty else None,
                    "histogram": float(macd_data['histogram'].iloc[-1]) if not macd_data['histogram'].empty else None
                },
                "bollinger": {
                    "upper": float(bollinger['upper'].iloc[-1]) if not bollinger['upper'].empty else None,
                    "middle": float(bollinger['middle'].iloc[-1]) if not bollinger['middle'].empty else None,
                    "lower": float(bollinger['lower'].iloc[-1]) if not bollinger['lower'].empty else None
                },
                "support": float(support) if support else None,
                "resistance": float(resistance) if resistance else None,
                "trend": trend,
                "volume": volume_data,
                "golden_cross": golden,
                "death_cross": death,
                "atr": float(atr.iloc[-1]) if not atr.empty else None,
                "vwap": float(vwap.iloc[-1]) if not vwap.empty else None,
                "pivots": pivots,
                "fibonacci": fibs
            }
            
            return indicators
            
        except Exception as e:
            print(f"Error calculating indicators for {symbol}: {str(e)}")
            return None
    
    def generate_signal(self, symbol: str, strategy_type: str = "swing") -> Optional[TradingSignal]:
        """
        Generate trading signal for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            strategy_type: Type of strategy ("swing" or "day")
        
        Returns:
            TradingSignal object or None
        """
        try:
            # Get stock data
            stock_data = self.market_service.get_stock_data(symbol)
            if not stock_data:
                return None
            
            # Calculate indicators
            indicators = self.calculate_all_indicators(symbol)
            if not indicators:
                return None
            
            # Fetch news analysis for signal enhancement
            news_analysis = None
            if self.gemini_service.is_available():
                company_info = self.market_service.get_company_info(symbol)
                news_analysis = self.gemini_service.analyze_stock_news(symbol, company_info.get('name', symbol))
            
            # Analyze signals
            signal_type, confidence, reasoning = self._analyze_signals(
                stock_data, indicators, news_analysis, strategy_type
            )
            
            # Calculate entry/exit points
            entry_price = stock_data.current_price
            
            # Use ATR for volatility-based stops if available
            atr = indicators.get('atr', entry_price * 0.02)
            
            if strategy_type == "day":
                # Day trading: tighter targets and stops
                target_mult = 1.5
                stop_mult = 1.0
                holding_period = "Intraday"
            else:
                # Swing trading
                target_mult = 3.0
                stop_mult = 1.5
                holding_period = "3-7 days"

            if signal_type == SignalType.BUY:
                target_price = entry_price + (atr * target_mult)
                stop_loss = entry_price - (atr * stop_mult)
            elif signal_type == SignalType.SELL:
                target_price = entry_price - (atr * target_mult)
                stop_loss = entry_price + (atr * stop_mult)
            else:  # HOLD
                target_price = entry_price
                stop_loss = entry_price - (atr * stop_mult)
            
            # Try to enhance with AI recommendation
            if self.gemini_service.is_available():
                try:
                    ai_rec = self.gemini_service.get_trading_recommendation(
                        symbol,
                        stock_data.to_dict(),
                        indicators
                    )
                    if ai_rec:
                        # Use AI recommendation if confidence is higher
                        ai_confidence = ai_rec.get('confidence', 0)
                        if ai_confidence > confidence:
                            signal_type = SignalType(ai_rec.get('signal', signal_type.value))
                            confidence = ai_confidence
                            reasoning = ai_rec.get('reasoning', reasoning)
                            entry_price = ai_rec.get('entry_price', entry_price)
                            target_price = ai_rec.get('target_price', target_price)
                            stop_loss = ai_rec.get('stop_loss', stop_loss)
                except Exception as e:
                    print(f"AI recommendation failed: {str(e)}")
            
            trading_signal = TradingSignal(
                symbol=symbol,
                signal=signal_type,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss=stop_loss,
                holding_period="3-7 days",
                reasoning=reasoning,
                indicators=indicators
            )
            
            return trading_signal
            
        except Exception as e:
            print(f"Error generating signal for {symbol}: {str(e)}")
            return None
    
    def _analyze_signals(self, stock_data: StockData, indicators: Dict, 
                         news: Optional[NewsAnalysis] = None, strategy_type: str = "swing") -> tuple:
        """
        Analyze technical indicators to generate signal.
        
        Args:
            stock_data: Stock data
            indicators: Technical indicators
            news: Optional news analysis
            strategy_type: Type of strategy to apply
        
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
        
        # 2. Strategy-Specific Logic
        if strategy_type == "day":
            # VWAP Logic for Day Trading
            vwap = indicators.get('vwap')
            if vwap:
                if current_price > vwap:
                    buy_signals += 1
                    reasons.append("Price above VWAP (Bullish)")
                else:
                    sell_signals += 1
                    reasons.append("Price below VWAP (Bearish)")
            
            # Pivot Points
            pivots = indicators.get('pivots', {})
            if current_price < pivots.get('s1', 0):
                buy_signals += 1
                reasons.append("Price near Pivot S1 support")
            elif current_price > pivots.get('r1', 0):
                sell_signals += 1
                reasons.append("Price near Pivot R1 resistance")
        
        else: # Swing Trading
            # Fibonacci Levels
            fibs = indicators.get('fibonacci', {})
            if abs(current_price - fibs.get('level_618', 0)) / current_price < 0.01:
                buy_signals += 2
                reasons.append("Fibonacci 61.8% retracement level")
            
            # Longer term trend
            if trend == "UPTREND":
                buy_signals += 1
                reasons.append("Daily uptrend")
            elif trend == "DOWNTREND":
                sell_signals += 1
                reasons.append("Daily downtrend")

        # 3. News & Noise Logic (Signal Override/Enhancement)
        if news:
            sentiment_score = news.sentiment_score
            relevance = news.relevance
            
            # High relevance news acts as a multiplier
            weight = 1.0
            if relevance > 80:
                weight = 2.0
                reasons.append(f"High impact news: {news.headline}")
            
            if sentiment_score > 0.4:
                buy_signals += int(2 * weight)
                reasons.append(f"Positive sentiment ({sentiment_score:.2f})")
            elif sentiment_score < -0.4:
                sell_signals += int(2 * weight)
                reasons.append(f"Negative sentiment ({sentiment_score:.2f})")
            
            # Noise Filter: If news is extremely negative but price doesn't drop, 
            # might be a "buy the news" opportunity (divergence).
            if sentiment_score < -0.7 and stock_data.change_percent > 0:
                buy_signals += 1
                reasons.append("Sentiment/Price divergence (Noise filter)")

        # Determine signal
        total_signals = buy_signals + sell_signals
        if total_signals == 0:
            return SignalType.HOLD, 50.0, "Neutral technical/news state"
        
        if buy_signals > sell_signals:
            confidence = min(98, 50 + (buy_signals / (total_signals + 1)) * 50)
            return SignalType.BUY, round(confidence, 1), "; ".join(reasons[:3])
        elif sell_signals > buy_signals:
            confidence = min(98, 50 + (sell_signals / (total_signals + 1)) * 50)
            return SignalType.SELL, round(confidence, 1), "; ".join(reasons[:3])
        else:
            return SignalType.HOLD, 50.0, "Conflicting signals"
    
    def get_signals_for_multiple_stocks(self, symbols: List[str], strategy_type: str = "swing") -> Dict[str, TradingSignal]:
        """
        Generate signals for multiple stocks.
        
        Args:
            symbols: List of ticker symbols
            strategy_type: Type of strategy
        
        Returns:
            Dictionary mapping symbols to trading signals
        """
        signals = {}
        for symbol in symbols:
            signal = self.generate_signal(symbol, strategy_type=strategy_type)
            if signal:
                signals[symbol] = signal
        return signals
    
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
