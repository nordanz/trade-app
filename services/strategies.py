"""
Unified Trading Strategies Module - Registry and Imports

This module serves as a central registry for all trading strategies,
importing from separate day trading and swing trading modules.

Strategy Organization:
- day_trading_strategies.py: Intraday strategies (1-5 min candles)
- swing_trading_strategies.py: Multi-day strategies (daily candles)

Usage:
    from services.strategies import get_strategy, ALL_STRATEGIES
    
    strategy_class = get_strategy('vwap')  # Get day trading VWAP strategy
    strategy_class = get_strategy('mean_reversion')  # Get swing strategy
"""

from typing import Type, Dict, Optional
from backtesting import Strategy

# Import all day trading strategies
from services.day_trading_strategies import (
    VWAPTradingStrategy,
    OpeningRangeBreakoutStrategy,
    MomentumGapStrategy,
    DAY_TRADING_STRATEGIES
)

# Import all swing trading strategies
from services.swing_trading_strategies import (
    MeanReversionBBStrategy,
    FibonacciRetracementStrategy,
    BreakoutTradingStrategy,
    SWING_TRADING_STRATEGIES
)


# Combined strategy registry
ALL_STRATEGIES: Dict[str, Type[Strategy]] = {
    **DAY_TRADING_STRATEGIES,
    **SWING_TRADING_STRATEGIES
}


def get_strategy(strategy_name: str) -> Optional[Type[Strategy]]:
    """
    Get strategy class by name.
    
    Args:
        strategy_name: Strategy identifier (e.g., 'vwap', 'mean_reversion')
        
    Returns:
        Strategy class or None if not found
    """
    return ALL_STRATEGIES.get(strategy_name.lower())


def list_strategies() -> Dict[str, list]:
    """
    List all available strategies grouped by type.
    
    Returns:
        Dictionary with 'day_trading' and 'swing_trading' keys
    """
    return {
        'day_trading': list(DAY_TRADING_STRATEGIES.keys()),
        'swing_trading': list(SWING_TRADING_STRATEGIES.keys())
    }


def get_strategy_info(strategy_name: str) -> Optional[Dict]:
    """
    Get detailed information about a strategy.
    
    Args:
        strategy_name: Strategy identifier
        
    Returns:
        Dictionary with strategy metadata
    """
    strategy_class = get_strategy(strategy_name)
    if not strategy_class:
        return None
    
    # Determine strategy type
    strategy_type = 'day_trading' if strategy_name in DAY_TRADING_STRATEGIES else 'swing_trading'
    
    return {
        'name': strategy_name,
        'type': strategy_type,
        'class': strategy_class.__name__,
        'description': strategy_class.__doc__.strip() if strategy_class.__doc__ else '',
        'parameters': {
            k: v for k, v in vars(strategy_class).items() 
            if not k.startswith('_') and not callable(v)
        }
    }


# Export all strategies for convenience
__all__ = [
    # Day trading strategies
    'VWAPTradingStrategy',
    'OpeningRangeBreakoutStrategy',
    'MomentumGapStrategy',
    
    # Swing trading strategies
    'MeanReversionBBStrategy',
    'FibonacciRetracementStrategy',
    'BreakoutTradingStrategy',
    
    # Registries
    'DAY_TRADING_STRATEGIES',
    'SWING_TRADING_STRATEGIES',
    'ALL_STRATEGIES',
    
    # Helper functions
    'get_strategy',
    'list_strategies',
    'get_strategy_info',
]
