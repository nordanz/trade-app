"""
Swing Trading Strategies - Multi-day trading on daily candles.
Strategies hold positions for days to weeks.
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Optional

from services.signal_logic import (
    MeanReversionParams, mean_reversion_signal,
    FibonacciParams,     fibonacci_signal,
    BreakoutParams,      breakout_signal,
)


class BaseSwingTradingStrategy(Strategy):
    """Base class for all swing trading strategies with common multi-day logic"""
    
    # Common parameters for swing trading
    risk_per_trade = 0.02   # 2% risk per trade
    position_size = 0.95    # 95% of capital per trade
    max_positions = 1       # Number of concurrent positions
    
    def init(self):
        """Initialize indicators common to all swing trading strategies"""
        # ATR for position sizing and stops
        self.atr = self.I(self.calculate_atr, self.data.High, self.data.Low, self.data.Close, 14)
        
        # Volume moving average for confirmation
        self.avg_volume = self.I(lambda v: ta.sma(pd.Series(v), 20).bfill().values, self.data.Volume)
        
    def calculate_atr(self, high, low, close, period=14):
        """Calculate Average True Range"""
        df = pd.DataFrame({'High': high, 'Low': low, 'Close': close})
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=period)
        return atr.bfill().values
    
    def volume_confirmed(self, volume, avg_volume, threshold=1.2):
        """Check if volume confirms the signal"""
        return volume > threshold * avg_volume


class MeanReversionBBStrategy(BaseSwingTradingStrategy):
    """
    Mean Reversion using Bollinger Bands
    
    Entry Signals:
    - LONG: Price touches lower band + RSI < 30 + volume confirmation
    - SHORT: Price touches upper band + RSI > 70 + volume confirmation
    
    Exit Signals:
    - Take profit: Price reaches middle band (mean reversion)
    - Stop loss: Price breaks through opposite band
    - Trailing stop: Move stop to middle band once profitable
    
    Best for: Range-bound stocks with clear support/resistance
    """
    
    # Strategy parameters
    bb_period = 20          # Bollinger Band period
    bb_std = 2.0            # Standard deviations
    rsi_oversold = 30       # RSI threshold for long entry
    rsi_overbought = 70     # RSI threshold for short entry
    volume_threshold = 1.3  # Volume must be 1.3x average
    
    def init(self):
        super().init()
        
        # Bollinger Bands
        close_series = pd.Series(self.data.Close)
        bb = ta.bbands(close_series, length=self.bb_period, std=self.bb_std)
        # Find actual column names (pandas_ta naming varies by version)
        bb_cols = bb.columns.tolist()
        upper_col = [c for c in bb_cols if c.startswith('BBU')][0]
        middle_col = [c for c in bb_cols if c.startswith('BBM')][0]
        lower_col = [c for c in bb_cols if c.startswith('BBL')][0]
        self.bb_upper = self.I(lambda: bb[upper_col].bfill().values)
        self.bb_middle = self.I(lambda: bb[middle_col].bfill().values)
        self.bb_lower = self.I(lambda: bb[lower_col].bfill().values)
        
        # RSI for confirmation
        self.rsi = self.I(lambda c: ta.rsi(pd.Series(c), 14).bfill().values, self.data.Close)
    
    def next(self):
        """Trading logic executed on each bar."""

        price   = self.data.Close[-1]
        volume  = self.data.Volume[-1]
        avg_vol = self.avg_volume[-1]

        if not self.position:
            result = mean_reversion_signal(
                price=price,
                bb_upper=self.bb_upper[-1],
                bb_middle=self.bb_middle[-1],
                bb_lower=self.bb_lower[-1],
                rsi=self.rsi[-1],
                volume=volume,
                avg_volume=avg_vol,
                params=MeanReversionParams(
                    rsi_oversold=self.rsi_oversold,
                    rsi_overbought=self.rsi_overbought,
                    volume_threshold=self.volume_threshold,
                ),
            )
            if result.direction == 'BUY':
                self.buy(sl=result.sl_price, tp=result.tp_price)
            elif result.direction == 'SELL':
                self.sell(sl=result.sl_price, tp=result.tp_price)
        else:
            bb_middle = self.bb_middle[-1]
            bb_upper  = self.bb_upper[-1]
            bb_lower  = self.bb_lower[-1]
            # Take profit near middle band; hard stop if price breaks further
            if self.position.is_long:
                if price >= bb_middle:
                    self.position.close()
                elif price < bb_lower * 0.98:
                    self.position.close()
            elif self.position.is_short:
                if price <= bb_middle:
                    self.position.close()
                elif price > bb_upper * 1.02:
                    self.position.close()


class FibonacciRetracementStrategy(BaseSwingTradingStrategy):
    """
    Fibonacci Retracement Strategy
    
    Entry Signals:
    - LONG: Price retraces to 38.2%, 50%, or 61.8% Fib level in uptrend
    - SHORT: Price retraces to 38.2%, 50%, or 61.8% Fib level in downtrend
    
    Exit Signals:
    - Take profit: 1.618 Fibonacci extension
    - Stop loss: Below/above 78.6% retracement level
    - Trend break: Price crosses opposite direction
    
    Best for: Trending stocks with clear swing highs/lows
    """
    
    # Strategy parameters
    lookback_period = 50    # Bars to look back for swing high/low
    fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786, 1.618]
    entry_tolerance = 0.01  # 1% tolerance around Fib level
    trend_ema_period = 50   # EMA period for trend confirmation
    volume_threshold = 1.2
    
    def init(self):
        super().init()
        
        # Trend confirmation
        self.ema = self.I(lambda c: ta.ema(pd.Series(c), self.trend_ema_period).bfill().values, self.data.Close)
        
        # Track swing highs and lows
        self.swing_high = None
        self.swing_low = None
        self.fib_calculated = False
    
    def calculate_fib_levels(self, swing_high, swing_low, is_uptrend):
        """Calculate Fibonacci retracement levels"""
        levels = {}
        diff = swing_high - swing_low
        
        if is_uptrend:
            # Retracement levels from swing high
            for level in self.fib_levels:
                if level < 1.0:
                    levels[level] = swing_high - (diff * level)
                else:
                    # Extension levels
                    levels[level] = swing_high + (diff * (level - 1.0))
        else:
            # Retracement levels from swing low
            for level in self.fib_levels:
                if level < 1.0:
                    levels[level] = swing_low + (diff * level)
                else:
                    # Extension levels
                    levels[level] = swing_low - (diff * (level - 1.0))
        
        return levels
    
    def next(self):
        """Trading logic executed on each bar."""

        price   = self.data.Close[-1]
        volume  = self.data.Volume[-1]
        avg_vol = self.avg_volume[-1]
        ema     = self.ema[-1]
        is_uptrend = price > ema

        if len(self.data) >= self.lookback_period:
            self.swing_high = max(self.data.High[-self.lookback_period:])
            self.swing_low  = min(self.data.Low[-self.lookback_period:])
        else:
            return

        fib_levels = self.calculate_fib_levels(self.swing_high, self.swing_low, is_uptrend)

        if not self.position:
            result = fibonacci_signal(
                price=price,
                fib_levels=fib_levels,
                is_uptrend=is_uptrend,
                volume=volume,
                avg_volume=avg_vol,
                params=FibonacciParams(
                    entry_tolerance=self.entry_tolerance,
                    volume_threshold=self.volume_threshold,
                    entry_levels=tuple(self.fib_levels[:3]),   # 0.236, 0.382, 0.5
                    stop_level=0.786,
                    target_level=1.618,
                ),
            )
            if result.direction == 'BUY':
                self.buy(sl=result.sl_price, tp=result.tp_price)
            elif result.direction == 'SELL':
                self.sell(sl=result.sl_price, tp=result.tp_price)
        else:
            # Exit if trend reverses
            if self.position.is_long and not is_uptrend:
                self.position.close()
            elif self.position.is_short and is_uptrend:
                self.position.close()


class BreakoutTradingStrategy(BaseSwingTradingStrategy):
    """
    Breakout Trading Strategy
    
    Entry Signals:
    - LONG: Price breaks above resistance + volume spike + ADX > 25
    - SHORT: Price breaks below support + volume spike + ADX > 25
    
    Exit Signals:
    - Take profit: 2x risk distance
    - Stop loss: Back below/above breakout level
    - Trailing stop: ATR-based trailing stop
    
    Best for: Stocks consolidating before strong directional moves
    """
    
    # Strategy parameters
    resistance_lookback = 20   # Bars to identify resistance
    support_lookback = 20      # Bars to identify support
    breakout_threshold = 0.02  # 2% above resistance or below support
    volume_threshold = 2.0     # Volume must be 2x average for breakout
    adx_threshold = 25         # ADX must be > 25 for trend strength
    profit_multiplier = 2.0    # Risk:Reward = 1:2
    trailing_atr_mult = 2.0    # Trailing stop at 2x ATR
    
    def init(self):
        super().init()
        
        # ADX for trend strength
        high_s = pd.Series(self.data.High)
        low_s = pd.Series(self.data.Low)
        close_s = pd.Series(self.data.Close)
        adx_df = ta.adx(high_s, low_s, close_s, length=14)
        self.adx = self.I(lambda: adx_df['ADX_14'].bfill().values)
        
        # Track resistance and support levels
        self.resistance = None
        self.support = None
    
    def next(self):
        """Trading logic executed on each bar."""

        price   = self.data.Close[-1]
        volume  = self.data.Volume[-1]
        avg_vol = self.avg_volume[-1]
        adx     = self.adx[-1]

        if len(self.data) >= self.resistance_lookback:
            self.resistance = max(self.data.High[-self.resistance_lookback:])
            self.support    = min(self.data.Low[-self.support_lookback:])
        else:
            return

        if not self.position:
            result = breakout_signal(
                price=price,
                resistance=self.resistance,
                support=self.support,
                volume=volume,
                avg_volume=avg_vol,
                adx=adx,
                params=BreakoutParams(
                    breakout_threshold=self.breakout_threshold,
                    volume_threshold=self.volume_threshold,
                    adx_threshold=self.adx_threshold,
                    profit_multiplier=self.profit_multiplier,
                ),
            )
            if result.direction == 'BUY':
                self.buy(sl=result.sl_price, tp=result.tp_price)
            elif result.direction == 'SELL':
                self.sell(sl=result.sl_price, tp=result.tp_price)
        else:
            # Exit if price reverses back through breakout level
            if self.position.is_long and price < self.resistance:
                self.position.close()
            elif self.position.is_short and price > self.support:
                self.position.close()


# Strategy registry for easy access
SWING_TRADING_STRATEGIES = {
    'mean_reversion': MeanReversionBBStrategy,
    'fibonacci': FibonacciRetracementStrategy,
    'breakout': BreakoutTradingStrategy,
}
