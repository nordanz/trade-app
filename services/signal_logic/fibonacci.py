"""Fibonacci Retracement entry logic — shared by FibonacciRetracementStrategy and _analyze_signals()."""

from dataclasses import dataclass
from typing import Dict, Optional
from .base import SignalResult


@dataclass
class FibonacciParams:
    """All tunable thresholds for the Fibonacci Retracement strategy."""
    entry_tolerance: float  = 0.02   # price must be within N% of a Fib level
    volume_threshold: float = 1.2    # volume must be N× avg
    # Key retracement levels to watch for entries
    entry_levels: tuple     = (0.382, 0.5, 0.618)
    stop_level: float       = 0.786  # stop loss at 78.6% retracement
    target_level: float     = 1.618  # take profit at 1.618 extension


def fibonacci_signal(
    price: float,
    fib_levels: Dict[str, float],
    is_uptrend: bool,
    volume: float,
    avg_volume: float,
    params: FibonacciParams = None,
) -> SignalResult:
    """
    Fibonacci Retracement entry condition.

    In an uptrend: BUY when price pulls back to a key Fib retracement level.
    In a downtrend: SELL when price bounces to a key Fib retracement level.

    Parameters
    ----------
    price:       Current close price.
    fib_levels:  Dict mapping level names/floats to prices, e.g.
                 ``{'0.382': 142.5, '0.618': 138.2, '1.618': 162.0, ...}``.
                 Keys may be strings (from indicators module) or floats (from
                 strategy class).
    is_uptrend:  True when the current trend is bullish (price > EMA/SMA).
    volume:      Current bar volume.
    avg_volume:  20-bar average volume.
    params:      Override defaults via ``FibonacciParams``.
    """
    if params is None:
        params = FibonacciParams()

    if not fib_levels:
        return SignalResult('HOLD', 0, "Fibonacci levels unavailable")

    vol_ok = volume > params.volume_threshold * avg_volume
    if not vol_ok:
        return SignalResult(
            'HOLD', 0,
            f"Volume {volume/avg_volume:.1f}x avg — below {params.volume_threshold}x threshold",
        )

    # Normalise keys to floats so we can look up stop and target levels
    normalised: Dict[float, float] = {}
    for k, v in fib_levels.items():
        if v is None:
            continue
        try:
            # Keys from the indicators module are strings like '0_382' or '61.8%';
            # keys from the strategy class are plain floats.
            key_f = float(str(k).replace('_', '.').replace('%', '').strip())
            normalised[key_f] = float(v)
        except (ValueError, TypeError):
            continue

    # Check each entry level in priority order
    for level in params.entry_levels:
        # Try exact float key first, then search through normalised keys
        level_price = normalised.get(level)
        if level_price is None:
            # Fuzzy match: find a normalised key close to target level
            for k, v in normalised.items():
                if abs(k - level) < 0.01:
                    level_price = v
                    break

        if level_price is None:
            continue

        proximity = abs(price - level_price) / level_price
        if proximity < params.entry_tolerance:
            level_pct = f"{level*100:.1f}%"
            if is_uptrend:
                # For a long: SL = deeper retracement (stop_level), TP = extension (target_level)
                long_sl = normalised.get(params.stop_level)
                long_tp = normalised.get(params.target_level)
                # Geometry guard: SL < entry < TP
                if long_sl and long_tp and not (long_sl < price < long_tp):
                    continue
                return SignalResult(
                    direction='BUY',
                    confidence_votes=2,
                    reason=f"Fibonacci {level_pct} support (${level_price:.2f}) in uptrend",
                    sl_price=long_sl,
                    tp_price=long_tp,
                )
            else:
                # For a short: SL = extension above price (target_level), TP = deeper drop (stop_level)
                short_sl = normalised.get(params.target_level)  # above price
                short_tp = normalised.get(params.stop_level)    # below price
                # Geometry guard: TP < entry < SL
                if short_sl and short_tp and not (short_tp < price < short_sl):
                    continue
                return SignalResult(
                    direction='SELL',
                    confidence_votes=2,
                    reason=f"Fibonacci {level_pct} resistance (${level_price:.2f}) in downtrend",
                    sl_price=short_sl,
                    tp_price=short_tp,
                )

    return SignalResult(
        'HOLD', 0,
        f"Price (${price:.2f}) not at any key Fibonacci level "
        f"({'up' if is_uptrend else 'down'}trend)",
    )
