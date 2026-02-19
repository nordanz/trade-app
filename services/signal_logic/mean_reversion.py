"""Mean Reversion (Bollinger Bands) entry logic — shared by MeanReversionBBStrategy and _analyze_signals()."""

from dataclasses import dataclass
from typing import Optional
from .base import SignalResult


@dataclass
class MeanReversionParams:
    """All tunable thresholds for the Mean Reversion strategy."""
    rsi_oversold: float  = 30.0  # RSI must be below this for a long entry
    rsi_overbought: float = 70.0  # RSI must be above this for a short entry
    volume_threshold: float = 1.3  # volume must be N× avg


def mean_reversion_signal(
    price: float,
    bb_upper: float,
    bb_middle: float,
    bb_lower: float,
    rsi: float,
    volume: float,
    avg_volume: float,
    params: MeanReversionParams = None,
) -> SignalResult:
    """
    Mean Reversion (Bollinger Bands) entry condition.

    BUY  when price touches/crosses the lower BB and RSI is oversold.
    SELL when price touches/crosses the upper BB and RSI is overbought.

    Parameters
    ----------
    price:      Current close price.
    bb_upper:   Upper Bollinger Band value.
    bb_middle:  Middle Bollinger Band (SMA 20) value — used as take-profit target.
    bb_lower:   Lower Bollinger Band value.
    rsi:        Current RSI value.
    volume:     Current bar volume.
    avg_volume: 20-bar average volume.
    params:     Override defaults via ``MeanReversionParams``.
    """
    if params is None:
        params = MeanReversionParams()

    if not bb_upper or not bb_lower or not bb_middle:
        return SignalResult('HOLD', 0, "Bollinger Bands unavailable")

    vol_ok = volume > params.volume_threshold * avg_volume

    if not vol_ok:
        return SignalResult(
            'HOLD', 0,
            f"Volume {volume/avg_volume:.1f}x avg — below {params.volume_threshold}x threshold",
        )

    if price <= bb_lower and rsi and rsi < params.rsi_oversold:
        band_width = bb_middle - bb_lower
        sl_price = bb_lower - band_width * 0.5
        return SignalResult(
            direction='BUY',
            confidence_votes=2,
            reason=f"At Bollinger lower band (${bb_lower:.2f}), RSI oversold ({rsi:.1f})",
            sl_price=sl_price,
            tp_price=bb_middle,
        )

    if price >= bb_upper and rsi and rsi > params.rsi_overbought:
        band_width = bb_upper - bb_middle
        sl_price = bb_upper + band_width * 0.5
        return SignalResult(
            direction='SELL',
            confidence_votes=2,
            reason=f"At Bollinger upper band (${bb_upper:.2f}), RSI overbought ({rsi:.1f})",
            sl_price=sl_price,
            tp_price=bb_middle,
        )

    rsi_str = f"{rsi:.1f}" if rsi is not None else "N/A"
    return SignalResult(
        'HOLD', 0,
        f"Price (${price:.2f}) inside Bollinger Bands "
        f"[${bb_lower:.2f} – ${bb_upper:.2f}], RSI={rsi_str}",
    )
