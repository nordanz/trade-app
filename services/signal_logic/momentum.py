"""Momentum / Gap-and-Go entry logic — shared by MomentumGapStrategy and _analyze_signals()."""

from dataclasses import dataclass
from .base import SignalResult


@dataclass
class MomentumParams:
    """All tunable thresholds for the Momentum/Gap-and-Go strategy."""
    gap_threshold: float    = 0.02  # minimum gap size (2 %)
    rsi_long_entry: float   = 60.0  # RSI must be > this for a long
    rsi_short_entry: float  = 40.0  # RSI must be < this for a short
    volume_threshold: float = 1.5   # volume must be N× avg
    sl_multiplier: float    = 3.0   # stop loss = entry ± sl_multiplier × ATR


def momentum_signal(
    price: float,
    prev_close: float,
    rsi: float,
    macd_line: float,
    macd_signal_line: float,
    volume: float,
    avg_volume: float,
    atr: float,
    params: MomentumParams = None,
) -> SignalResult:
    """
    Momentum / Gap-and-Go entry condition.

    BUY  when gap up > threshold, RSI > rsi_long_entry, MACD bullish, volume confirmed.
    SELL when gap down > threshold, RSI < rsi_short_entry, MACD bearish, volume confirmed.

    Parameters
    ----------
    price:             Current close price.
    prev_close:        Previous bar's close (used to compute gap size).
    rsi:               Current RSI value.
    macd_line:         Current MACD line value.
    macd_signal_line:  Current MACD signal line value.
    volume:            Current bar volume.
    avg_volume:        20-bar average volume.
    atr:               Current ATR value (for SL calculation).
    params:            Override defaults via ``MomentumParams``.
    """
    if params is None:
        params = MomentumParams()

    if not prev_close or prev_close <= 0:
        return SignalResult('HOLD', 0, "No previous close available for gap calculation")

    gap = (price - prev_close) / prev_close
    vol_ratio = volume / avg_volume if avg_volume > 0 else 1.0
    vol_ok = vol_ratio >= params.volume_threshold

    if not vol_ok:
        return SignalResult(
            'HOLD', 0,
            f"Volume {vol_ratio:.1f}x avg — below {params.volume_threshold}x threshold",
        )

    macd_bullish = (macd_line is not None and macd_signal_line is not None
                    and macd_line > macd_signal_line)
    macd_bearish = (macd_line is not None and macd_signal_line is not None
                    and macd_line < macd_signal_line)

    if gap > params.gap_threshold and rsi and rsi > params.rsi_long_entry and macd_bullish:
        return SignalResult(
            direction='BUY',
            confidence_votes=2,
            reason=(
                f"Bullish momentum: gap +{gap*100:.1f}%, "
                f"RSI {rsi:.0f}, MACD bullish, volume {vol_ratio:.1f}x avg"
            ),
            sl_price=price - params.sl_multiplier * atr,
            tp_price=None,   # Momentum exits on RSI exhaustion, not fixed TP
        )

    if gap < -params.gap_threshold and rsi and rsi < params.rsi_short_entry and macd_bearish:
        return SignalResult(
            direction='SELL',
            confidence_votes=2,
            reason=(
                f"Bearish momentum: gap {gap*100:.1f}%, "
                f"RSI {rsi:.0f}, MACD bearish, volume {vol_ratio:.1f}x avg"
            ),
            sl_price=price + params.sl_multiplier * atr,
            tp_price=None,
        )

    rsi_str = f"{rsi:.0f}" if rsi is not None else "N/A"
    return SignalResult(
        'HOLD', 0,
        f"No momentum signal (gap={gap*100:.1f}%, RSI={rsi_str})",
    )
