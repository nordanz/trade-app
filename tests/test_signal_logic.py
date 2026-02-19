"""
Unit tests for services/signal_logic pure functions.

These tests exercise the shared entry-condition logic that is used by both
the backtesting Strategy classes and TradingStrategyService._analyze_signals().
No mocking required — all inputs are plain Python scalars.
"""

import pytest
from services.signal_logic import (
    vwap_signal,           VWAPParams,
    orb_signal,            ORBParams,
    momentum_signal,       MomentumParams,
    mean_reversion_signal, MeanReversionParams,
    fibonacci_signal,      FibonacciParams,
    breakout_signal,       BreakoutParams,
    SignalResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_buy(result: SignalResult) -> bool:
    return result.direction == "BUY"

def _is_sell(result: SignalResult) -> bool:
    return result.direction == "SELL"

def _is_hold(result: SignalResult) -> bool:
    return result.direction == "HOLD"


# ---------------------------------------------------------------------------
# SignalResult dataclass
# ---------------------------------------------------------------------------

class TestSignalResult:
    def test_defaults(self):
        r = SignalResult(direction="BUY", confidence_votes=2, reason="test")
        assert r.sl_price is None
        assert r.tp_price is None

    def test_full_construction(self):
        r = SignalResult(direction="SELL", confidence_votes=3, reason="x",
                         sl_price=110.0, tp_price=90.0)
        assert r.sl_price == 110.0
        assert r.tp_price == 90.0


# ---------------------------------------------------------------------------
# VWAP Signal
# ---------------------------------------------------------------------------

class TestVWAPSignal:
    """price within 0.3 % of VWAP + volume > 1.5× avg → BUY or SELL"""

    # price=100.0 is 0.1 % ABOVE vwap=99.9  → BUY
    BUY_BASE = dict(price=100.0, vwap=99.9, volume=200_000, avg_volume=100_000, atr=2.0)
    # price=99.9 is 0.1 % BELOW vwap=100.0 → SELL
    SELL_BASE = dict(price=99.9, vwap=100.0, volume=200_000, avg_volume=100_000, atr=2.0)

    def test_buy_just_above_vwap_with_volume(self):
        r = vwap_signal(**self.BUY_BASE)
        assert _is_buy(r)
        assert r.confidence_votes >= 1
        assert r.sl_price is not None
        assert r.tp_price is not None

    def test_sell_just_below_vwap_with_volume(self):
        r = vwap_signal(**self.SELL_BASE)
        assert _is_sell(r)

    def test_hold_insufficient_volume(self):
        # volume == avg_volume → ratio 1.0, below 1.5 threshold
        r = vwap_signal(price=100.0, vwap=99.9, volume=100_000, avg_volume=100_000, atr=2.0)
        assert _is_hold(r)

    def test_hold_price_too_far_above_vwap(self):
        # price is 2 % above vwap — outside the 0.3 % band
        r = vwap_signal(price=102.0, vwap=100.0, volume=200_000, avg_volume=100_000, atr=2.0)
        assert _is_hold(r)

    def test_hold_zero_vwap(self):
        r = vwap_signal(price=100.0, vwap=0.0, volume=200_000, avg_volume=100_000, atr=2.0)
        assert _is_hold(r)

    def test_custom_params_stricter_volume(self):
        params = VWAPParams(volume_threshold=3.0)
        # volume=2× avg — below new threshold of 3×
        r = vwap_signal(price=100.0, vwap=99.9, volume=200_000, avg_volume=100_000,
                        atr=2.0, params=params)
        assert _is_hold(r)

    def test_sl_below_entry_on_buy(self):
        r = vwap_signal(**self.BUY_BASE)
        assert r.sl_price < r.tp_price  # SL below entry, TP above

    def test_tp_below_sl_on_sell(self):
        r = vwap_signal(**self.SELL_BASE)
        assert r.tp_price < r.sl_price  # TP below entry, SL above


# ---------------------------------------------------------------------------
# Opening Range Breakout (ORB) Signal
# ---------------------------------------------------------------------------

class TestORBSignal:
    """price > opening_high + volume → BUY; price < opening_low + volume → SELL"""

    def test_buy_above_opening_high(self):
        r = orb_signal(price=105.0, opening_high=100.0, opening_low=95.0,
                       volume=380_000, avg_volume=200_000)
        assert _is_buy(r)
        assert r.sl_price == pytest.approx(95.0)  # SL = opening_low
        assert r.tp_price > 105.0

    def test_sell_below_opening_low(self):
        r = orb_signal(price=93.0, opening_high=100.0, opening_low=95.0,
                       volume=380_000, avg_volume=200_000)
        assert _is_sell(r)
        assert r.sl_price == pytest.approx(100.0)  # SL = opening_high
        assert r.tp_price < 93.0

    def test_hold_inside_range(self):
        r = orb_signal(price=97.0, opening_high=100.0, opening_low=95.0,
                       volume=380_000, avg_volume=200_000)
        assert _is_hold(r)

    def test_hold_insufficient_volume(self):
        r = orb_signal(price=105.0, opening_high=100.0, opening_low=95.0,
                       volume=100_000, avg_volume=200_000)
        assert _is_hold(r)

    def test_hold_zero_opening_range(self):
        r = orb_signal(price=100.0, opening_high=0.0, opening_low=0.0,
                       volume=400_000, avg_volume=200_000)
        assert _is_hold(r)

    def test_custom_volume_threshold(self):
        params = ORBParams(volume_threshold=1.0)
        # volume strictly > 1.0× avg → use 1.01×
        r = orb_signal(price=105.0, opening_high=100.0, opening_low=95.0,
                       volume=210_000, avg_volume=200_000, params=params)
        assert _is_buy(r)


# ---------------------------------------------------------------------------
# Momentum Gap Signal
# ---------------------------------------------------------------------------

class TestMomentumSignal:
    """gap > 2 % + RSI > 60 + MACD bullish + volume → BUY; mirrored for SELL"""

    def _buy_inputs(self, **overrides):
        kwargs = dict(
            price=103.0, prev_close=100.0, rsi=65.0,
            macd_line=0.5, macd_signal_line=0.2,
            volume=300_000, avg_volume=200_000, atr=2.0,
        )
        kwargs.update(overrides)
        return kwargs

    def _sell_inputs(self, **overrides):
        kwargs = dict(
            price=97.0, prev_close=100.0, rsi=35.0,
            macd_line=-0.5, macd_signal_line=-0.2,
            volume=300_000, avg_volume=200_000, atr=2.0,
        )
        kwargs.update(overrides)
        return kwargs

    def test_buy_gap_up(self):
        r = momentum_signal(**self._buy_inputs())
        assert _is_buy(r)
        assert r.sl_price < self._buy_inputs()['price']

    def test_sell_gap_down(self):
        r = momentum_signal(**self._sell_inputs())
        assert _is_sell(r)

    def test_hold_gap_too_small(self):
        r = momentum_signal(**self._buy_inputs(prev_close=102.0))  # < 2 % gap
        assert _is_hold(r)

    def test_hold_rsi_too_low_for_long(self):
        r = momentum_signal(**self._buy_inputs(rsi=55.0))
        assert _is_hold(r)

    def test_hold_macd_bearish_on_long(self):
        r = momentum_signal(**self._buy_inputs(macd_line=-0.1, macd_signal_line=0.2))
        assert _is_hold(r)

    def test_hold_low_volume(self):
        r = momentum_signal(**self._buy_inputs(volume=100_000))
        assert _is_hold(r)

    def test_hold_no_prev_close(self):
        r = momentum_signal(**self._buy_inputs(prev_close=None))
        assert _is_hold(r)

    def test_tp_is_none_momentum_exits_on_rsi(self):
        r = momentum_signal(**self._buy_inputs())
        assert r.tp_price is None  # exits on RSI exhaustion, not fixed TP


# ---------------------------------------------------------------------------
# Mean Reversion (Bollinger Bands) Signal
# ---------------------------------------------------------------------------

class TestMeanReversionSignal:
    """price ≤ BB lower + RSI < 30 → BUY; price ≥ BB upper + RSI > 70 → SELL"""

    def test_buy_at_lower_band(self):
        r = mean_reversion_signal(
            price=95.0, bb_upper=110.0, bb_middle=100.0, bb_lower=95.0,
            rsi=28.0, volume=280_000, avg_volume=200_000,
        )
        assert _is_buy(r)
        assert r.tp_price == pytest.approx(100.0)  # TP = bb_middle

    def test_sell_at_upper_band(self):
        r = mean_reversion_signal(
            price=110.0, bb_upper=110.0, bb_middle=100.0, bb_lower=90.0,
            rsi=72.0, volume=280_000, avg_volume=200_000,
        )
        assert _is_sell(r)
        assert r.tp_price == pytest.approx(100.0)

    def test_hold_price_at_middle(self):
        r = mean_reversion_signal(
            price=100.0, bb_upper=110.0, bb_middle=100.0, bb_lower=90.0,
            rsi=50.0, volume=280_000, avg_volume=200_000,
        )
        assert _is_hold(r)

    def test_hold_rsi_not_extreme(self):
        # price at lower band but RSI not oversold
        r = mean_reversion_signal(
            price=90.0, bb_upper=110.0, bb_middle=100.0, bb_lower=90.0,
            rsi=45.0, volume=280_000, avg_volume=200_000,
        )
        assert _is_hold(r)

    def test_hold_insufficient_volume(self):
        r = mean_reversion_signal(
            price=90.0, bb_upper=110.0, bb_middle=100.0, bb_lower=90.0,
            rsi=25.0, volume=100_000, avg_volume=200_000,
        )
        assert _is_hold(r)

    def test_sl_outside_band_on_buy(self):
        r = mean_reversion_signal(
            price=90.0, bb_upper=110.0, bb_middle=100.0, bb_lower=90.0,
            rsi=25.0, volume=280_000, avg_volume=200_000,
        )
        assert r.sl_price < 90.0  # SL below lower band

    def test_sl_outside_band_on_sell(self):
        r = mean_reversion_signal(
            price=110.0, bb_upper=110.0, bb_middle=100.0, bb_lower=90.0,
            rsi=75.0, volume=280_000, avg_volume=200_000,
        )
        assert r.sl_price > 110.0  # SL above upper band


# ---------------------------------------------------------------------------
# Fibonacci Retracement Signal
# ---------------------------------------------------------------------------

class TestFibonacciSignal:
    """Price near 38.2/50/61.8 % retracement level + volume → BUY (uptrend) / SELL (downtrend)"""

    # Fib levels computed on a 80→110 range (high=110, low=80):
    #   0.236 → 110 - 0.236×30 = 102.92
    #   0.382 → 110 - 0.382×30 = 98.54
    #   0.500 → 110 - 0.500×30 = 95.00
    #   0.618 → 110 - 0.618×30 = 91.46
    #   0.786 → 110 - 0.786×30 = 86.42   ← stop (below entry for long)
    #   1.000 → 80.00
    #   1.618 → 110 + 0.618×30 = 128.54  ← target (above entry for long)
    def _fib_levels_str(self):
        return {
            '0_236': 102.92,
            '0_382': 98.54,
            '0_500': 95.00,
            '0_618': 91.46,
            '0_786': 86.42,
            '1_000': 80.00,
            '1_618': 128.54,
        }

    def _fib_levels_float(self):
        return {
            0.236: 102.92,
            0.382: 98.54,
            0.5:   95.00,
            0.618: 91.46,
            0.786: 86.42,
            1.0:   80.00,
            1.618: 128.54,
        }

    def test_buy_at_382_uptrend_string_keys(self):
        r = fibonacci_signal(
            price=98.8, fib_levels=self._fib_levels_str(),
            is_uptrend=True, volume=260_000, avg_volume=200_000,
        )
        assert _is_buy(r)

    def test_buy_at_382_uptrend_float_keys(self):
        r = fibonacci_signal(
            price=98.8, fib_levels=self._fib_levels_float(),
            is_uptrend=True, volume=260_000, avg_volume=200_000,
        )
        assert _is_buy(r)

    def test_sell_at_618_downtrend(self):
        r = fibonacci_signal(
            price=91.2, fib_levels=self._fib_levels_str(),
            is_uptrend=False, volume=260_000, avg_volume=200_000,
        )
        assert _is_sell(r)

    def test_hold_no_nearby_level(self):
        r = fibonacci_signal(
            price=84.0, fib_levels=self._fib_levels_str(),
            is_uptrend=True, volume=260_000, avg_volume=200_000,
        )
        assert _is_hold(r)

    def test_hold_empty_fib_levels(self):
        r = fibonacci_signal(
            price=98.8, fib_levels={},
            is_uptrend=True, volume=260_000, avg_volume=200_000,
        )
        assert _is_hold(r)

    def test_hold_insufficient_volume(self):
        r = fibonacci_signal(
            price=98.8, fib_levels=self._fib_levels_str(),
            is_uptrend=True, volume=100_000, avg_volume=200_000,
        )
        assert _is_hold(r)

    def test_sl_tp_geometry_on_buy(self):
        r = fibonacci_signal(
            price=98.8, fib_levels=self._fib_levels_str(),
            is_uptrend=True, volume=260_000, avg_volume=200_000,
        )
        if r.sl_price and r.tp_price:
            assert r.sl_price < 98.8 < r.tp_price

    def test_sl_tp_geometry_on_sell(self):
        r = fibonacci_signal(
            price=91.2, fib_levels=self._fib_levels_str(),
            is_uptrend=False, volume=260_000, avg_volume=200_000,
        )
        if r.sl_price and r.tp_price:
            assert r.tp_price < 91.2 < r.sl_price


# ---------------------------------------------------------------------------
# Breakout Signal
# ---------------------------------------------------------------------------

class TestBreakoutSignal:
    """price > resistance × (1 + threshold) + volume → BUY; below support → SELL"""

    # volume=420_000 / 200_000 = 2.1× — strictly above the 2.0× threshold
    def test_buy_above_resistance(self):
        r = breakout_signal(
            price=103.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=30.0,
        )
        assert _is_buy(r)
        assert r.sl_price == pytest.approx(100.0)  # SL = resistance level

    def test_sell_below_support(self):
        r = breakout_signal(
            price=87.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=30.0,
        )
        assert _is_sell(r)
        assert r.sl_price == pytest.approx(90.0)  # SL = support level

    def test_hold_inside_range(self):
        r = breakout_signal(
            price=95.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=30.0,
        )
        assert _is_hold(r)

    def test_hold_insufficient_adx(self):
        r = breakout_signal(
            price=103.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=20.0,
        )
        assert _is_hold(r)

    def test_hold_insufficient_volume(self):
        # volume=400_000 / 200_000 = exactly 2.0× — not strictly above threshold
        r = breakout_signal(
            price=103.0, resistance=100.0, support=90.0,
            volume=400_000, avg_volume=200_000, adx=30.0,
        )
        assert _is_hold(r)

    def test_hold_zero_resistance(self):
        r = breakout_signal(
            price=103.0, resistance=0.0, support=0.0,
            volume=420_000, avg_volume=200_000, adx=30.0,
        )
        assert _is_hold(r)

    def test_none_adx_skips_adx_check(self):
        # Live service passes adx=None — should still work on volume + price
        r = breakout_signal(
            price=103.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=None,
        )
        assert _is_buy(r)

    def test_tp_above_entry_on_buy(self):
        r = breakout_signal(
            price=103.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=None,
        )
        assert r.tp_price > 103.0

    def test_tp_below_entry_on_sell(self):
        r = breakout_signal(
            price=87.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=None,
        )
        assert r.tp_price < 87.0

    def test_custom_profit_multiplier(self):
        params = BreakoutParams(profit_multiplier=3.0)
        r = breakout_signal(
            price=103.0, resistance=100.0, support=90.0,
            volume=420_000, avg_volume=200_000, adx=None, params=params,
        )
        risk = 103.0 - 100.0  # price - resistance
        expected_tp = 103.0 + 3.0 * risk
        assert r.tp_price == pytest.approx(expected_tp)
