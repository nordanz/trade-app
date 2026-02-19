"""Shared return type for all signal logic functions."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SignalResult:
    """
    Output of every ``*_signal()`` pure function.

    Attributes
    ----------
    direction:
        ``'BUY'``, ``'SELL'``, or ``'HOLD'``.
    confidence_votes:
        Weight to add to the buy/sell vote tally in ``_analyze_signals()``.
        Typically 2 for a strong primary signal, 1 for a confirming signal.
    reason:
        Human-readable explanation shown in the UI.
    sl_price:
        Exact stop-loss price calculated by the strategy logic.
        ``None`` means the caller should fall back to its ATR-based default.
    tp_price:
        Exact take-profit / target price.
        ``None`` means the caller should fall back to its ATR-based default.
    """

    direction: str          # 'BUY' | 'SELL' | 'HOLD'
    confidence_votes: int   # vote weight contributed to _analyze_signals tally
    reason: str
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
