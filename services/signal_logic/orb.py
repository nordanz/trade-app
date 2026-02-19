"""Opening Range Breakout entry logic — shared by OpeningRangeBreakoutStrategy and _analyze_signals()."""

from dataclasses import dataclass
from typing import Optional
from .base import SignalResult


@dataclass
class ORBParams:
    """All tunable thresholds for the ORB strategy."""
    volume_threshold: float  = 1.8   # volume must be N× avg for a valid breakout
    profit_multiplier: float = 2.0   # TP = breakout level + N × opening range size


def orb_signal(
    price: float,
    opening_high: float,
    opening_low: float,
    volume: float,
    avg_volume: float,
    params: ORBParams = None,
) -> SignalResult:
    """
    Opening Range Breakout entry condition.

    BUY  when price breaks *above* ``opening_high`` with volume confirmation.
    SELL when price breaks *below* ``opening_low`` with volume confirmation.

    Parameters
    ----------
    price:        Current close price.
    opening_high: High of the opening-range window (first N bars of the session).
    opening_low:  Low of the opening-range window.
    volume:       Current bar volume.
    avg_volume:   20-bar average volume.
    params:       Override defaults via ``ORBParams``.
    """
    if params is None:
        params = ORBParams()

    if not opening_high or not opening_low:
        return SignalResult('HOLD', 0, "Opening range not yet established")

    opening_range = opening_high - opening_low
    vol_ok = volume > params.volume_threshold * avg_volume

    if not vol_ok:
        return SignalResult(
            'HOLD', 0,
            f"Volume {volume/avg_volume:.1f}x avg — below {params.volume_threshold}x threshold",
        )

    if price > opening_high:
        tp_price = opening_high + params.profit_multiplier * opening_range
        return SignalResult(
            direction='BUY',
            confidence_votes=2,
            reason=(
                f"Broke above intraday opening high (${opening_high:.2f}) "
                f"with {volume/avg_volume:.1f}x volume"
            ),
            sl_price=opening_low,
            tp_price=tp_price,
        )

    if price < opening_low:
        tp_price = opening_low - params.profit_multiplier * opening_range
        return SignalResult(
            direction='SELL',
            confidence_votes=2,
            reason=(
                f"Broke below intraday opening low (${opening_low:.2f}) "
                f"with {volume/avg_volume:.1f}x volume"
            ),
            sl_price=opening_high,
            tp_price=tp_price,
        )

    return SignalResult(
        'HOLD', 0,
        f"Price (${price:.2f}) inside opening range "
        f"[${opening_low:.2f} – ${opening_high:.2f}]",
    )
