"""
Signal Logic Layer — single source of truth for every strategy's entry conditions.

Both the backtesting Strategy classes and TradingStrategyService._analyze_signals()
import from here, so changing a threshold or rule fixes both at once.

Each module exposes:
  - A ``*Params`` dataclass   — all tunable thresholds in one place
  - A ``*_signal()`` function — pure function: inputs → SignalResult
  - A ``SignalResult``        — re-exported from base for convenience
"""

from .base import SignalResult
from .vwap import VWAPParams, vwap_signal
from .orb import ORBParams, orb_signal
from .momentum import MomentumParams, momentum_signal
from .mean_reversion import MeanReversionParams, mean_reversion_signal
from .fibonacci import FibonacciParams, fibonacci_signal
from .breakout import BreakoutParams, breakout_signal

__all__ = [
    "SignalResult",
    "VWAPParams",        "vwap_signal",
    "ORBParams",         "orb_signal",
    "MomentumParams",    "momentum_signal",
    "MeanReversionParams","mean_reversion_signal",
    "FibonacciParams",   "fibonacci_signal",
    "BreakoutParams",    "breakout_signal",
]
