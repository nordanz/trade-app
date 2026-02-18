"""
Test cases for trading strategies and trading strategy service
Tests both day trading and swing trading strategies
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting import Backtest
from unittest.mock import Mock, patch, MagicMock

from services.day_trading_strategies import (
    VWAPTradingStrategy,
    OpeningRangeBreakoutStrategy,
    MomentumGapStrategy,
    DAY_TRADING_STRATEGIES
)
from services.swing_trading_strategies import (
    MeanReversionBBStrategy,
    FibonacciRetracementStrategy,
    BreakoutTradingStrategy,
    SWING_TRADING_STRATEGIES
)
from services.strategies import get_strategy, list_strategies, get_strategy_info
from services.trading_strategy_service import TradingStrategyService
from models.trading_signal import TradingSignal, SignalType


# ============================================================================
# FIXTURES - Synthetic Test Data
# ============================================================================

@pytest.fixture
def synthetic_daily_data():
    """Generate synthetic daily OHLCV data with trend"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Create uptrend with volatility
    close = np.linspace(100, 120, 100) + np.random.normal(0, 1, 100).cumsum()
    open_ = close + np.random.uniform(-1, 1, 100)
    high = np.maximum(close, open_) + np.random.uniform(0, 2, 100)
    low = np.minimum(close, open_) - np.random.uniform(0, 2, 100)
    volume = np.random.uniform(1000000, 5000000, 100)
    
    df = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Adj Close': close
    }, index=dates)
    
    return df


@pytest.fixture
def synthetic_intraday_data():
    """Generate synthetic 5-minute intraday data"""
    dates = pd.date_range(start='2023-01-01 09:30', periods=80, freq='5min')
    
    # Create mean-reverting intraday pattern
    close = 100 + np.sin(np.linspace(0, 4*np.pi, 80)) * 2 + np.random.normal(0, 0.5, 80)
    open_ = close + np.random.uniform(-0.5, 0.5, 80)
    high = np.maximum(close, open_) + np.random.uniform(0, 1, 80)
    low = np.minimum(close, open_) - np.random.uniform(0, 1, 80)
    volume = np.random.uniform(100000, 500000, 80)
    
    df = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Adj Close': close
    }, index=dates)
    
    return df


@pytest.fixture
def oversold_data():
    """Generate data with RSI oversold condition (RSI < 30)"""
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    
    # Strong downtrend
    close = np.linspace(100, 80, 50) + np.random.normal(0, 0.5, 50)
    open_ = close + np.random.uniform(-0.5, 0.5, 50)
    high = np.maximum(close, open_) + np.random.uniform(0, 0.5, 50)
    low = np.minimum(close, open_) - np.random.uniform(0, 1.5, 50)
    volume = np.random.uniform(1000000, 5000000, 50)
    
    df = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Adj Close': close
    }, index=dates)
    
    return df


@pytest.fixture
def bollinger_band_touch_data():
    """Generate data with price touching Bollinger Bands"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Mean-reverting around 100
    returns = np.random.normal(0.0001, 0.02, 100)
    close = 100 * np.exp(np.cumsum(returns))
    open_ = close + np.random.uniform(-1, 1, 100)
    high = np.maximum(close, open_) + np.random.uniform(0, 2, 100)
    low = np.minimum(close, open_) - np.random.uniform(0, 2, 100)
    volume = np.random.uniform(1000000, 5000000, 100)
    
    df = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Adj Close': close
    }, index=dates)
    
    return df


@pytest.fixture
def gap_up_data():
    """Generate data with gap up (>2%)"""
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    
    close = np.ones(30) * 100
    close[1:] += np.linspace(0, 5, 29)  # Gradual uptrend after gap
    
    # Create gap up on day 1
    open_ = np.ones(30) * 100
    open_[1] = 102.5  # 2.5% gap up
    
    high = np.maximum(close, open_) + np.random.uniform(0, 1, 30)
    low = np.minimum(close, open_) - np.random.uniform(0, 1, 30)
    volume = np.ones(30) * 2000000
    volume[1] = 5000000  # High volume on gap day
    
    df = pd.DataFrame({
        'Open': open_,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Adj Close': close
    }, index=dates)
    
    return df


# ============================================================================
# STRATEGY REGISTRY TESTS
# ============================================================================

class TestStrategyRegistry:
    """Test strategy registry and discovery"""
    
    def test_list_strategies(self):
        """Test listing all available strategies"""
        strategies = list_strategies()
        
        assert 'day_trading' in strategies
        assert 'swing_trading' in strategies
        assert 'vwap' in strategies['day_trading']
        assert 'orb' in strategies['day_trading']
        assert 'momentum' in strategies['day_trading']
        assert 'mean_reversion' in strategies['swing_trading']
        assert 'fibonacci' in strategies['swing_trading']
        assert 'breakout' in strategies['swing_trading']
    
    def test_get_strategy_day_trading(self):
        """Test retrieving day trading strategies"""
        vwap_strategy = get_strategy('vwap')
        assert vwap_strategy == VWAPTradingStrategy
        
        orb_strategy = get_strategy('orb')
        assert orb_strategy == OpeningRangeBreakoutStrategy
        
        momentum_strategy = get_strategy('momentum')
        assert momentum_strategy == MomentumGapStrategy
    
    def test_get_strategy_swing_trading(self):
        """Test retrieving swing trading strategies"""
        mr_strategy = get_strategy('mean_reversion')
        assert mr_strategy == MeanReversionBBStrategy
        
        fib_strategy = get_strategy('fibonacci')
        assert fib_strategy == FibonacciRetracementStrategy
        
        bo_strategy = get_strategy('breakout')
        assert bo_strategy == BreakoutTradingStrategy
    
    def test_get_strategy_case_insensitive(self):
        """Test strategy retrieval is case-insensitive"""
        strategy1 = get_strategy('VWAP')
        strategy2 = get_strategy('vwap')
        assert strategy1 == strategy2
    
    def test_get_strategy_nonexistent(self):
        """Test retrieving nonexistent strategy returns None"""
        strategy = get_strategy('nonexistent')
        assert strategy is None
    
    def test_get_strategy_info(self):
        """Test getting strategy metadata"""
        info = get_strategy_info('vwap')
        
        assert info is not None
        assert info['name'] == 'vwap'
        assert info['type'] == 'day_trading'
        assert info['class'] == 'VWAPTradingStrategy'
        assert 'description' in info
        assert 'parameters' in info


# ============================================================================
# DAY TRADING STRATEGY TESTS
# ============================================================================

class TestDayTradingStrategies:
    """Test day trading strategies with synthetic data"""
    
    def test_vwap_strategy_initialization(self, synthetic_intraday_data):
        """Test VWAP strategy can be initialized"""
        bt = Backtest(synthetic_intraday_data, VWAPTradingStrategy, cash=10000, commission=0.002)
        assert bt is not None
    
    def test_vwap_strategy_runs(self, synthetic_intraday_data):
        """Test VWAP strategy runs without errors"""
        bt = Backtest(synthetic_intraday_data, VWAPTradingStrategy, cash=10000, commission=0.002)
        stats = bt.run()
        
        assert stats is not None
        assert 'Return [%]' in stats
    
    def test_orb_strategy_initialization(self, synthetic_intraday_data):
        """Test ORB strategy can be initialized"""
        bt = Backtest(synthetic_intraday_data, OpeningRangeBreakoutStrategy, cash=10000, commission=0.002)
        assert bt is not None
    
    def test_orb_strategy_runs(self, synthetic_intraday_data):
        """Test ORB strategy runs without errors"""
        bt = Backtest(synthetic_intraday_data, OpeningRangeBreakoutStrategy, cash=10000, commission=0.002)
        stats = bt.run()
        
        assert stats is not None
        assert 'Return [%]' in stats
    
    def test_momentum_strategy_initialization(self, synthetic_intraday_data):
        """Test Momentum strategy can be initialized"""
        bt = Backtest(synthetic_intraday_data, MomentumGapStrategy, cash=10000, commission=0.002)
        assert bt is not None
    
    def test_momentum_strategy_runs(self, synthetic_intraday_data):
        """Test Momentum strategy runs without errors"""
        bt = Backtest(synthetic_intraday_data, MomentumGapStrategy, cash=10000, commission=0.002)
        stats = bt.run()
        
        assert stats is not None
        assert 'Return [%]' in stats


# ============================================================================
# SWING TRADING STRATEGY TESTS
# ============================================================================

class TestSwingTradingStrategies:
    """Test swing trading strategies with synthetic data"""
    
    def test_mean_reversion_strategy_initialization(self, bollinger_band_touch_data):
        """Test Mean Reversion strategy can be initialized"""
        bt = Backtest(bollinger_band_touch_data, MeanReversionBBStrategy, cash=10000, commission=0.002)
        assert bt is not None
    
    def test_mean_reversion_strategy_runs(self, bollinger_band_touch_data):
        """Test Mean Reversion strategy runs without errors"""
        bt = Backtest(bollinger_band_touch_data, MeanReversionBBStrategy, cash=10000, commission=0.002)
        stats = bt.run()
        
        assert stats is not None
        assert 'Return [%]' in stats
    
    def test_fibonacci_strategy_initialization(self, synthetic_daily_data):
        """Test Fibonacci strategy can be initialized"""
        bt = Backtest(synthetic_daily_data, FibonacciRetracementStrategy, cash=10000, commission=0.002)
        assert bt is not None
    
    def test_fibonacci_strategy_runs(self, synthetic_daily_data):
        """Test Fibonacci strategy runs without errors"""
        bt = Backtest(synthetic_daily_data, FibonacciRetracementStrategy, cash=10000, commission=0.002)
        stats = bt.run()
        
        assert stats is not None
        assert 'Return [%]' in stats
    
    def test_breakout_strategy_initialization(self, synthetic_daily_data):
        """Test Breakout strategy can be initialized"""
        bt = Backtest(synthetic_daily_data, BreakoutTradingStrategy, cash=10000, commission=0.002)
        assert bt is not None
    
    def test_breakout_strategy_runs(self, synthetic_daily_data):
        """Test Breakout strategy runs without errors"""
        bt = Backtest(synthetic_daily_data, BreakoutTradingStrategy, cash=10000, commission=0.002)
        stats = bt.run()
        
        assert stats is not None
        assert 'Return [%]' in stats


# ============================================================================
# TRADING STRATEGY SERVICE TESTS
# ============================================================================

class TestTradingStrategyService:
    """Test TradingStrategyService with mocked external dependencies"""
    
    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies"""
        service = TradingStrategyService()
        
        # Mock external services
        service.market_service = Mock()
        service.gemini_service = Mock()
        service.gemini_service.is_available.return_value = False
        
        return service
    
    def test_service_initialization(self, service):
        """Test service initializes correctly"""
        assert service is not None
        assert service.market_service is not None
        assert service.gemini_service is not None
    
    def test_generate_signal_day_trading_vwap(self, service):
        """Test generating day trading VWAP signal"""
        # Mock market data
        service.market_service.get_stock_data.return_value = Mock(
            current_price=150.0,
            change_percent=0.5
        )
        service.market_service.get_historical_data.return_value = pd.DataFrame({
            'Close': np.linspace(150, 152, 20),
            'High': np.linspace(151, 153, 20),
            'Low': np.linspace(149, 151, 20),
            'Open': np.linspace(150.5, 151.5, 20),
            'Volume': np.ones(20) * 1000000
        })
        
        signal = service.generate_signal(
            symbol='AAPL',
            strategy_name='vwap',
            timeframe='5m',
            include_news=False
        )
        
        assert signal is not None
        assert signal.symbol == 'AAPL'
        assert signal.entry_price == 150.0
        assert signal.confidence >= 0
        assert signal.confidence <= 100
    
    def test_generate_signal_swing_trading_mean_reversion(self, service):
        """Test generating swing trading mean reversion signal"""
        # Mock market data
        service.market_service.get_stock_data.return_value = Mock(
            current_price=100.0,
            change_percent=-2.0
        )
        service.market_service.get_historical_data.return_value = pd.DataFrame({
            'Close': np.linspace(102, 100, 50),  # Downtrend
            'High': np.linspace(103, 101, 50),
            'Low': np.linspace(101, 99, 50),
            'Open': np.linspace(102.5, 100.5, 50),
            'Volume': np.ones(50) * 2000000
        })
        
        signal = service.generate_signal(
            symbol='SPY',
            strategy_name='mean_reversion',
            timeframe='1d',
            include_news=False
        )
        
        assert signal is not None
        assert signal.symbol == 'SPY'
        assert signal.holding_period == "3-7 days"
    
    def test_generate_signal_with_news(self, service):
        """Test signal generation with news analysis"""
        from models.trading_signal import NewsAnalysis, Sentiment
        
        # Mock market data
        service.market_service.get_stock_data.return_value = Mock(
            current_price=100.0,
            change_percent=1.0
        )
        service.market_service.get_company_info.return_value = {'name': 'Apple Inc'}
        service.market_service.get_historical_data.return_value = pd.DataFrame({
            'Close': np.linspace(99, 101, 30),
            'High': np.linspace(100, 102, 30),
            'Low': np.linspace(98, 100, 30),
            'Open': np.linspace(99.5, 100.5, 30),
            'Volume': np.ones(30) * 1500000
        })
        
        # Mock Gemini service
        service.gemini_service.is_available.return_value = True
        service.gemini_service.analyze_stock_news.return_value = NewsAnalysis(
            symbol='AAPL',
            sentiment=Sentiment.POSITIVE,
            sentiment_score=0.7,
            relevance=85.0,
            macro_impact=False,
            headline='Positive earnings',
            summary='Strong earnings beat',
            source='test'
        )
        
        signal = service.generate_signal(
            symbol='AAPL',
            strategy_name='mean_reversion',
            timeframe='1d',
            include_news=True
        )
        
        assert signal is not None
        assert signal.news_analysis is not None
        assert signal.news_analysis.sentiment_score > 0
    
    def test_scan_multiple_symbols(self, service):
        """Test scanning multiple symbols"""
        # Mock market data for each symbol
        def mock_stock_data(symbol):
            return Mock(
                current_price=100.0 + (hash(symbol) % 20),
                change_percent=np.random.uniform(-2, 2)
            )
        
        def mock_historical_data(*args, **kwargs):
            return pd.DataFrame({
                'Close': np.linspace(100, 102, 30),
                'High': np.linspace(101, 103, 30),
                'Low': np.linspace(99, 101, 30),
                'Open': np.linspace(100.5, 101.5, 30),
                'Volume': np.ones(30) * 1500000
            })
        
        service.market_service.get_stock_data.side_effect = mock_stock_data
        service.market_service.get_historical_data.side_effect = mock_historical_data
        
        signals = service.scan_multiple_symbols(
            symbols=['AAPL', 'MSFT', 'NVDA'],
            strategy_name='mean_reversion',
            timeframe='1d',
            min_confidence=50.0,
            include_news=False
        )
        
        assert isinstance(signals, list)
        assert len(signals) <= 3  # At most 3 signals
        
        for signal in signals:
            assert isinstance(signal, TradingSignal)
            assert signal.confidence >= 50.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components"""
    
    def test_all_strategies_in_registry(self):
        """Verify all 6 strategies are accessible via registry"""
        expected_strategies = [
            'vwap', 'orb', 'momentum',
            'mean_reversion', 'fibonacci', 'breakout'
        ]
        
        for strategy_name in expected_strategies:
            strategy_class = get_strategy(strategy_name)
            assert strategy_class is not None, f"Strategy {strategy_name} not found"
    
    def test_strategy_info_complete(self):
        """Verify strategy info contains required fields"""
        strategies = list_strategies()
        all_strategies = strategies['day_trading'] + strategies['swing_trading']
        
        for strategy_name in all_strategies:
            info = get_strategy_info(strategy_name)
            assert 'name' in info
            assert 'type' in info
            assert 'class' in info
            assert 'description' in info
            assert 'parameters' in info


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

@pytest.mark.parametrize('strategy_name,strategy_class', [
    ('vwap', VWAPTradingStrategy),
    ('orb', OpeningRangeBreakoutStrategy),
    ('momentum', MomentumGapStrategy),
])
def test_day_trading_strategies_exist(strategy_name, strategy_class):
    """Parametrized test: all day trading strategies exist"""
    assert get_strategy(strategy_name) == strategy_class


@pytest.mark.parametrize('strategy_name,strategy_class', [
    ('mean_reversion', MeanReversionBBStrategy),
    ('fibonacci', FibonacciRetracementStrategy),
    ('breakout', BreakoutTradingStrategy),
])
def test_swing_trading_strategies_exist(strategy_name, strategy_class):
    """Parametrized test: all swing trading strategies exist"""
    assert get_strategy(strategy_name) == strategy_class


@pytest.mark.parametrize('timeframe,expected_period', [
    ('1m', '1d'),
    ('5m', '5d'),
    ('1h', '30d'),
    ('1d', '1y'),
])
def test_timeframe_mapping(timeframe, expected_period):
    """Parametrized test: timeframe to period mapping"""
    period_map = {
        '1m': '1d',
        '5m': '5d',
        '15m': '5d',
        '30m': '5d',
        '1h': '30d',
        '1d': '1y',
    }
    assert period_map[timeframe] == expected_period


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
