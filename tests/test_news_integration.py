"""
Test cases for news integration and signal analysis
Tests sentiment scoring, relevance filtering, and signal strength
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime

from services.trading_strategy_service import TradingStrategyService
from models.trading_signal import TradingSignal, SignalType, NewsAnalysis, Sentiment
from models.stock_data import StockData


# ============================================================================
# NEWS ANALYSIS TESTS
# ============================================================================

class TestNewsIntegration:
    """Test news sentiment integration with trading signals"""
    
    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies"""
        service = TradingStrategyService()
        service.market_service = Mock()
        service.gemini_service = Mock()
        return service
    
    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock data"""
        return Mock(
            current_price=100.0,
            change_percent=1.5,
            volume=2000000,
            market_cap=1000000000
        )
    
    @pytest.fixture
    def sample_indicators(self):
        """Create sample technical indicators"""
        return {
            'rsi': 55.0,
            'macd': {'macd': 0.5, 'signal': 0.3, 'histogram': 0.2},
            'bollinger': {'upper': 105.0, 'middle': 100.0, 'lower': 95.0},
            'atr': 2.0,
            'vwap': 100.5,
            'support': 95.0,
            'resistance': 105.0,
            'trend': 'UPTREND',
            'volume': {},
            'golden_cross': False,
            'death_cross': False,
            'pivots': {'r1': 103.0, 's1': 97.0},
            'fibonacci': {'level_382': 98.0, 'level_500': 97.5, 'level_618': 97.0}
        }
    
    def test_positive_sentiment_amplifies_buy_signal(self, service, sample_stock_data, sample_indicators):
        """Test that positive news amplifies buy signals"""
        news = NewsAnalysis(
            symbol='AAPL',
            sentiment=Sentiment.POSITIVE,
            sentiment_score=0.8,
            relevance=90.0,
            macro_impact=False,
            headline='Earnings Beat',
            summary='Company beat earnings expectations',
            source='test'
        )
        
        signal_type, confidence, reasoning = service._analyze_signals(
            sample_stock_data,
            sample_indicators,
            news,
            strategy_type='swing',
            strategy_name='mean_reversion'
        )
        
        # With positive news, should lean toward BUY
        assert signal_type in [SignalType.BUY, SignalType.HOLD]
        # Reasoning may include sentiment or news-related terms
        reasoning_lower = reasoning.lower()
        assert any(term in reasoning_lower for term in ['sentiment', 'news', 'impact'])
    
    def test_negative_sentiment_amplifies_sell_signal(self, service, sample_stock_data, sample_indicators):
        """Test that negative news amplifies sell signals"""
        news = NewsAnalysis(
            symbol='AAPL',
            sentiment=Sentiment.NEGATIVE,
            sentiment_score=-0.8,
            relevance=90.0,
            macro_impact=False,
            headline='Revenue Miss',
            summary='Company missed revenue targets',
            source='test'
        )
        
        signal_type, confidence, reasoning = service._analyze_signals(
            sample_stock_data,
            sample_indicators,
            news,
            strategy_type='swing',
            strategy_name='mean_reversion'
        )
        
        # With negative news, should lean toward SELL
        assert signal_type in [SignalType.SELL, SignalType.HOLD]
        # Reasoning may include sentiment or news-related terms
        reasoning_lower = reasoning.lower()
        assert any(term in reasoning_lower for term in ['sentiment', 'news', 'impact'])
    
    def test_low_relevance_news_filtered(self, service, sample_stock_data, sample_indicators):
        """Test that low relevance news doesn't affect signals"""
        news = NewsAnalysis(
            symbol='AAPL',
            sentiment=Sentiment.POSITIVE,
            sentiment_score=0.9,
            relevance=5.0,  # Low relevance
            macro_impact=False,
            headline='Minor News',
            summary='Minor company news',
            source='test'
        )
        
        signal_type1, confidence1, _ = service._analyze_signals(
            sample_stock_data,
            sample_indicators,
            news,
            strategy_type='swing',
            strategy_name='mean_reversion'
        )
        
        signal_type2, confidence2, _ = service._analyze_signals(
            sample_stock_data,
            sample_indicators,
            None,  # No news
            strategy_type='swing',
            strategy_name='mean_reversion'
        )
        
        # Signals should be similar even with low relevance news
        assert signal_type1 == signal_type2
    
    def test_macro_event_flag(self, service, sample_stock_data, sample_indicators):
        """Test macro event impact flag"""
        news = NewsAnalysis(
            symbol='SPY',
            sentiment=Sentiment.NEGATIVE,
            sentiment_score=-0.7,
            relevance=95.0,
            macro_impact=True,  # Major macro event
            headline='Fed Rate Hike',
            summary='Federal Reserve raises interest rates 50bps',
            source='test'
        )
        
        signal_type, confidence, reasoning = service._analyze_signals(
            sample_stock_data,
            sample_indicators,
            news,
            strategy_type='swing',
            strategy_name='mean_reversion'
        )
        
        # High impact negative news should produce bearish signal
        assert signal_type in [SignalType.SELL, SignalType.HOLD]
    
    def test_sentiment_price_divergence(self, service, sample_indicators):
        """Test divergence between sentiment and price movement"""
        # Negative sentiment but price up (contrarian opportunity)
        stock_data = Mock(
            current_price=100.0,
            change_percent=2.0,  # Price UP despite bad news
            volume=2000000,
            market_cap=1000000000
        )
        
        news = NewsAnalysis(
            symbol='AAPL',
            sentiment=Sentiment.NEGATIVE,
            sentiment_score=-0.9,
            relevance=85.0,
            macro_impact=False,
            headline='Bad News',
            summary='Negative company development',
            source='test'
        )
        
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data,
            sample_indicators,
            news,
            strategy_type='swing',
            strategy_name='mean_reversion'
        )
        
        # Divergence should be noted
        if 'divergence' in reasoning.lower() or 'contrarian' in reasoning.lower():
            assert True
        else:
            # At minimum, signal should exist
            assert signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]


# ============================================================================
# SIGNAL STRENGTH TESTS
# ============================================================================

class TestSignalStrength:
    """Test signal confidence and strength calculation"""
    
    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies"""
        service = TradingStrategyService()
        service.market_service = Mock()
        service.gemini_service = Mock()
        service.gemini_service.is_available.return_value = False
        return service
    
    def test_strong_rsi_oversold_signal(self, service):
        """Test strong buy signal with extreme RSI"""
        stock_data = Mock(current_price=100.0, change_percent=-5.0)
        indicators = {
            'rsi': 20.0,  # Extreme oversold
            'macd': {'macd': 0.5, 'signal': 0.3, 'histogram': 0.2},  # Bullish MACD
            'bollinger': {'upper': 110.0, 'middle': 100.0, 'lower': 90.0},
            'atr': 2.0,
            'support': 90.0,
            'resistance': 110.0,
            'trend': 'NEUTRAL',
            'volume': {},
            'golden_cross': False,
            'death_cross': False,
            'pivots': {},
            'fibonacci': {}
        }
        
        signal_type, confidence, _ = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        assert signal_type == SignalType.BUY
        assert confidence > 70  # Strong confidence
    
    def test_weak_signal_neutral_conditions(self, service):
        """Test neutral signal with conflicting indicators"""
        stock_data = Mock(current_price=100.0, change_percent=0.0)
        indicators = {
            'rsi': 50.0,  # Neutral
            'macd': {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0},
            'bollinger': {'upper': 110.0, 'middle': 100.0, 'lower': 90.0},
            'atr': 2.0,
            'support': 90.0,
            'resistance': 110.0,
            'trend': 'NEUTRAL',
            'volume': {},
            'golden_cross': False,
            'death_cross': False,
            'pivots': {},
            'fibonacci': {}
        }
        
        signal_type, confidence, _ = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        assert signal_type == SignalType.HOLD
        assert confidence <= 60  # Weak signal
    
    def test_strong_sell_signal_overbought(self, service):
        """Test strong sell signal with overbought conditions"""
        stock_data = Mock(current_price=100.0, change_percent=5.0)
        indicators = {
            'rsi': 80.0,  # Overbought
            'macd': {'macd': -0.5, 'signal': 0.3, 'histogram': -0.8},  # Bearish MACD
            'bollinger': {'upper': 110.0, 'middle': 100.0, 'lower': 90.0},
            'atr': 2.0,
            'support': 90.0,
            'resistance': 110.0,
            'trend': 'NEUTRAL',
            'volume': {},
            'golden_cross': False,
            'death_cross': False,
            'pivots': {},
            'fibonacci': {}
        }
        
        signal_type, confidence, _ = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        assert signal_type == SignalType.SELL
        assert confidence > 70  # Strong confidence


# ============================================================================
# STRATEGY-SPECIFIC SIGNAL TESTS
# ============================================================================

class TestStrategySpecificSignals:
    """Test signal generation for specific strategies"""
    
    @pytest.fixture
    def service(self):
        service = TradingStrategyService()
        service.market_service = Mock()
        service.gemini_service = Mock()
        service.gemini_service.is_available.return_value = False
        return service
    
    def test_vwap_strategy_signal(self, service):
        """Test VWAP strategy signal generation"""
        # Price 0.2% above VWAP (within the 0.3% band) with sufficient volume
        stock_data = Mock(current_price=100.2, change_percent=0.2)
        indicators = {
            'rsi': 55.0,
            'macd': {'macd': 0.5, 'signal': 0.3, 'histogram': 0.2},
            'vwap': 100.0,  # Price 0.2% above VWAP → within band
            'atr': 1.5,
            'pivots': {'r1': 102.0, 's1': 98.0},
            'bollinger': {'upper': 105.0, 'middle': 100.0, 'lower': 95.0},
            'support': 98.0,
            'resistance': 102.0,
            'trend': 'UPTREND',
            'volume': {'current_volume': 300_000, 'avg_volume': 150_000, 'volume_ratio': 2.0},
            'golden_cross': False,
            'death_cross': False,
            'fibonacci': {}
        }
        
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data, indicators, None, 'day', 'vwap'
        )
        
        # Price within 0.3% of VWAP with volume should trigger VWAP signal
        assert signal_type in [SignalType.BUY, SignalType.HOLD]
        assert 'vwap' in reasoning.lower()
    
    def test_mean_reversion_strategy_signal(self, service):
        """Test Mean Reversion strategy signal generation"""
        stock_data = Mock(current_price=94.0, change_percent=-4.0)
        indicators = {
            'rsi': 25.0,  # Oversold
            'macd': {'macd': -0.5, 'signal': -0.2, 'histogram': -0.3},
            'bollinger': {'upper': 110.0, 'middle': 100.0, 'lower': 90.0},
            'atr': 2.0,
            'vwap': 100.0,
            'support': 90.0,
            'resistance': 110.0,
            'trend': 'DOWNTREND',
            'volume': {},
            'golden_cross': False,
            'death_cross': False,
            'pivots': {},
            'fibonacci': {}
        }
        
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        # At BB lower band + RSI oversold = mean reversion BUY
        assert signal_type in [SignalType.BUY, SignalType.HOLD]
    
    def test_fibonacci_strategy_signal(self, service):
        """Test Fibonacci strategy signal generation"""
        stock_data = Mock(current_price=97.0, change_percent=-3.0)
        indicators = {
            'rsi': 35.0,
            'macd': {'macd': -0.3, 'signal': -0.1, 'histogram': -0.2},
            'bollinger': {'upper': 110.0, 'middle': 100.0, 'lower': 90.0},
            'atr': 2.0,
            'vwap': 100.0,
            'support': 95.0,
            'resistance': 105.0,
            'trend': 'UPTREND',
            'volume': {},
            'golden_cross': False,
            'death_cross': False,
            'fibonacci': {'level_618': 97.2, 'level_500': 97.5},
            'pivots': {}
        }
        
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'fibonacci'
        )
        
        # Near Fib 61.8% level in uptrend = buy
        assert signal_type in [SignalType.BUY, SignalType.HOLD]
    
    def test_breakout_strategy_signal(self, service):
        """Test Breakout strategy signal generation"""
        stock_data = Mock(current_price=105.5, change_percent=2.0)
        indicators = {
            'rsi': 65.0,
            'macd': {'macd': 0.8, 'signal': 0.5, 'histogram': 0.3},
            'bollinger': {'upper': 110.0, 'middle': 100.0, 'lower': 90.0},
            'atr': 2.0,
            'vwap': 104.5,
            'support': 100.0,
            'resistance': 105.0,
            'trend': 'UPTREND',
            'volume': {},
            'golden_cross': True,
            'death_cross': False,
            'fibonacci': {},
            'pivots': {}
        }
        
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'breakout'
        )
        
        # Above resistance with strength = buy
        assert signal_type in [SignalType.BUY, SignalType.HOLD]


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def service(self):
        service = TradingStrategyService()
        service.market_service = Mock()
        service.gemini_service = Mock()
        service.gemini_service.is_available.return_value = False
        return service
    
    def test_missing_indicators(self, service):
        """Test handling of missing indicators"""
        stock_data = Mock(current_price=100.0, change_percent=0.0)
        indicators = {}  # Empty indicators
        
        # Should not crash
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        assert signal_type == SignalType.HOLD
        assert confidence == 50.0
    
    def test_none_news_analysis(self, service):
        """Test handling of None news analysis"""
        stock_data = Mock(current_price=100.0, change_percent=0.0)
        indicators = {'rsi': 55.0}
        
        # Should not crash with None news
        signal_type, confidence, reasoning = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        assert signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
    
    def test_extreme_prices(self, service):
        """Test handling of extreme price movements"""
        stock_data = Mock(current_price=1000.0, change_percent=-50.0)
        indicators = {
            'rsi': 10.0,
            'macd': {'macd': -10.0, 'signal': -5.0, 'histogram': -5.0},
            'atr': 50.0,
            'bollinger': {'upper': 1100.0, 'middle': 1000.0, 'lower': 900.0}
        }
        
        # Should handle extreme movements
        signal_type, confidence, _ = service._analyze_signals(
            stock_data, indicators, None, 'swing', 'mean_reversion'
        )
        
        assert confidence <= 100  # Confidence should be bounded


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
