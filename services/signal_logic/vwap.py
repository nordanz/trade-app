"""VWAP strategy entry logic — shared by VWAPTradingStrategy and _analyze_signals()."""

from dataclasses import dataclass
from .base import SignalResult


@dataclass
class VWAPParams:
    """All tunable thresholds for the VWAP strategy (matches VWAPTradingStrategy class attrs)."""
    volume_threshold: float = 1.5   # volume must be N× the 20-bar average
    vwap_distance: float    = 0.003 # max distance from VWAP to qualify as a cross (0.3%)
    sl_multiplier: float    = 2.0   # stop loss = entry ± sl_multiplier × ATR
    tp_multiplier: float    = 1.5   # take profit = entry ± tp_multiplier × ATR


def vwap_signal(
    price: float,
    vwap: float,
    volume: float,
    avg_volume: float,
    atr: float,
    params: VWAPParams = None,
) -> SignalResult:
    """
    VWAP entry condition.

    BUY  when price is within ``vwap_distance`` *above* VWAP with volume confirmation.
    SELL when price is within ``vwap_distance`` *below* VWAP with volume confirmation.

    Parameters
    ----------
    price:       Current close price.
    vwap:        Current VWAP value.
    volume:      Current bar volume.
    avg_volume:  20-bar average volume.
    atr:         Current ATR value (used to compute SL/TP prices).
    params:      Override defaults via ``VWAPParams``.
    """
    if params is None:
        params = VWAPParams()

    if not vwap or vwap <= 0:
        return SignalResult('HOLD', 0, "VWAP unavailable")

    vol_ok = volume > params.volume_threshold * avg_volume
    if not vol_ok:
        return SignalResult(
            'HOLD', 0,
            f"Volume {volume/avg_volume:.1f}x avg — below {params.volume_threshold}x threshold",
        )

    dist = abs(price - vwap) / vwap

    if price > vwap and dist < params.vwap_distance:
        return SignalResult(
            direction='BUY',
            confidence_votes=2,
            reason=(
                f"Price {dist*100:.2f}% above VWAP (${vwap:.2f}) "
                f"with {volume/avg_volume:.1f}x volume"
            ),
            sl_price=price - params.sl_multiplier * atr,
            tp_price=price + params.tp_multiplier * atr,
        )

    if price < vwap and dist < params.vwap_distance:
        return SignalResult(
            direction='SELL',
            confidence_votes=2,
            reason=(
                f"Price {dist*100:.2f}% below VWAP (${vwap:.2f}) "
                f"with {volume/avg_volume:.1f}x volume"
            ),
            sl_price=price + params.sl_multiplier * atr,
            tp_price=price - params.tp_multiplier * atr,
        )

    return SignalResult(
        'HOLD', 0,
        f"Price not within {params.vwap_distance*100:.1f}% of VWAP (dist={dist*100:.2f}%)",
    )
