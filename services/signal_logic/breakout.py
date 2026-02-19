"""Breakout entry logic — shared by BreakoutTradingStrategy and _analyze_signals()."""

from dataclasses import dataclass
from .base import SignalResult


@dataclass
class BreakoutParams:
    """All tunable thresholds for the Breakout strategy."""
    breakout_threshold: float = 0.02   # price must be N% beyond S/R to confirm breakout
    volume_threshold: float   = 2.0    # volume must be N× avg (strong breakout)
    adx_threshold: float      = 25.0   # ADX must exceed this for trend strength
    profit_multiplier: float  = 2.0    # TP = entry + N × risk


def breakout_signal(
    price: float,
    resistance: float,
    support: float,
    volume: float,
    avg_volume: float,
    adx: float,
    params: BreakoutParams = None,
) -> SignalResult:
    """
    Breakout entry condition.

    BUY  when price breaks N% above ``resistance`` with volume and ADX confirmation.
    SELL when price breaks N% below ``support`` with volume and ADX confirmation.

    Parameters
    ----------
    price:       Current close price.
    resistance:  Resistance level (20-bar high).
    support:     Support level (20-bar low).
    volume:      Current bar volume.
    avg_volume:  20-bar average volume.
    adx:         Current ADX value (trend strength).  Pass 0 or None to skip
                 the ADX check (the live service may not have ADX pre-computed).
    params:      Override defaults via ``BreakoutParams``.
    """
    if params is None:
        params = BreakoutParams()

    vol_ok   = volume > params.volume_threshold * avg_volume
    # When adx is unavailable (None / 0) we skip the check rather than blocking all signals
    adx_ok   = (adx is None or adx == 0) or (adx > params.adx_threshold)

    if not vol_ok:
        return SignalResult(
            'HOLD', 0,
            f"Volume {volume/avg_volume:.1f}x avg — below {params.volume_threshold}x threshold",
        )

    if not adx_ok:
        return SignalResult(
            'HOLD', 0,
            f"ADX {adx:.1f} below {params.adx_threshold} — trend not strong enough",
        )

    if resistance and price > resistance * (1 + params.breakout_threshold):
        risk     = price - resistance
        tp_price = price + params.profit_multiplier * risk
        return SignalResult(
            direction='BUY',
            confidence_votes=2,
            reason=(
                f"Breakout {(price/resistance - 1)*100:.1f}% above resistance "
                f"(${resistance:.2f}) with {volume/avg_volume:.1f}x volume"
            ),
            sl_price=resistance,
            tp_price=tp_price,
        )

    if support and price < support * (1 - params.breakout_threshold):
        risk     = support - price
        tp_price = price - params.profit_multiplier * risk
        return SignalResult(
            direction='SELL',
            confidence_votes=2,
            reason=(
                f"Breakdown {(1 - price/support)*100:.1f}% below support "
                f"(${support:.2f}) with {volume/avg_volume:.1f}x volume"
            ),
            sl_price=support,
            tp_price=tp_price,
        )

    return SignalResult(
        'HOLD', 0,
        f"Price (${price:.2f}) inside S/R range [${support:.2f} – ${resistance:.2f}]"
        if support and resistance else "Support/Resistance unavailable",
    )
