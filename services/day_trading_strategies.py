"""
Day Trading Strategies - Intraday trading on 1-5 minute candles
Strategies hold positions for minutes to hours, closed by EOD
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Optional


class BaseDayTradingStrategy(Strategy):
    """Base class for all day trading strategies with common intraday logic"""
    
    # Common parameters for day trading
    risk_per_trade = 0.02  # 2% risk per trade
    max_daily_loss = 0.06  # 6% max daily loss
    position_size = 0.95   # 95% of capital per trade
    
    def init(self):
        """Initialize indicators common to all day trading strategies"""
        # ATR for position sizing and stops
        self.atr = self.I(self.calculate_atr, self.data.High, self.data.Low, self.data.Close, 14)
        
        # Track daily P&L for risk management
        self.daily_pnl = 0
        self.trade_start_equity = self.equity
        
    def calculate_atr(self, high, low, close, period=14):
        """Calculate Average True Range"""
        df = pd.DataFrame({'High': high, 'Low': low, 'Close': close})
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=period)
        return atr.bfill().values
    
    def is_market_open_hours(self):
        """Check if current bar is during market hours (9:30 AM - 4:00 PM ET)"""
        # This is a placeholder - in production, check actual timestamp
        return True
    
    def should_close_eod(self):
        """Close all positions before market close"""
        # Placeholder - in production, check if within last 15 mins of trading
        return False
    
    def check_daily_loss_limit(self):
        """Stop trading if daily loss limit is reached"""
        daily_loss = (self.equity - self.trade_start_equity) / self.trade_start_equity
        return daily_loss <= -self.max_daily_loss


class VWAPTradingStrategy(BaseDayTradingStrategy):
    """
    VWAP (Volume Weighted Average Price) Trading Strategy
    
    Entry Signals:
    - LONG: Price crosses above VWAP with volume > avg volume
    - SHORT: Price crosses below VWAP with volume > avg volume
    
    Exit Signals:
    - Take profit: Price reverts to VWAP (mean reversion)
    - Stop loss: 2x ATR from entry
    - EOD: Close all positions before market close
    
    Best for: Liquid stocks with high intraday volatility
    """
    
    # Strategy parameters
    volume_threshold = 1.5  # Volume must be 1.5x average
    vwap_distance = 0.003   # 0.3% distance from VWAP for entry
    tp_multiplier = 1.5     # Take profit at 1.5x ATR
    sl_multiplier = 2.0     # Stop loss at 2x ATR
    
    def init(self):
        super().init()
        
        # Calculate VWAP
        self.vwap = self.I(self.calculate_vwap, self.data.High, self.data.Low, 
                           self.data.Close, self.data.Volume)
        
        # Volume moving average
        self.avg_volume = self.I(lambda v: ta.sma(pd.Series(v), 20).bfill().values, self.data.Volume)
        
    def calculate_vwap(self, high, low, close, volume):
        """Calculate VWAP (Volume Weighted Average Price)"""
        typical_price = (high + low + close) / 3
        cumulative_tp_volume = np.cumsum(typical_price * volume)
        cumulative_volume = np.cumsum(volume)
        vwap = cumulative_tp_volume / cumulative_volume
        return pd.Series(vwap).bfill().values
    
    def next(self):
        """Trading logic executed on each bar"""
        
        # Check daily loss limit
        if self.check_daily_loss_limit():
            if self.position:
                self.position.close()
            return
        
        # Close positions at EOD
        if self.should_close_eod():
            if self.position:
                self.position.close()
            return
        
        price = self.data.Close[-1]
        vwap = self.vwap[-1]
        volume = self.data.Volume[-1]
        avg_vol = self.avg_volume[-1]
        atr = self.atr[-1]
        
        # Volume confirmation
        volume_confirmed = volume > self.volume_threshold * avg_vol
        
        if not self.position:
            # Entry logic
            if volume_confirmed:
                # LONG: Price crosses above VWAP
                if price > vwap and (price - vwap) / vwap < self.vwap_distance:
                    sl_price = price - self.sl_multiplier * atr
                    tp_price = price + self.tp_multiplier * atr
                    self.buy(sl=sl_price, tp=tp_price)
                
                # SHORT: Price crosses below VWAP
                elif price < vwap and (vwap - price) / vwap < self.vwap_distance:
                    sl_price = price + self.sl_multiplier * atr
                    tp_price = price - self.tp_multiplier * atr
                    self.sell(sl=sl_price, tp=tp_price)
        else:
            # Mean reversion exit - close when price returns to VWAP
            if self.position.is_long and price >= vwap:
                self.position.close()
            elif self.position.is_short and price <= vwap:
                self.position.close()


class OpeningRangeBreakoutStrategy(BaseDayTradingStrategy):
    """
    Opening Range Breakout (ORB) Strategy
    
    Entry Signals:
    - LONG: Price breaks above first N-minute high with volume
    - SHORT: Price breaks below first N-minute low with volume
    
    Exit Signals:
    - Take profit: 2x opening range size
    - Stop loss: Opposite side of opening range
    - EOD: Close all positions
    
    Best for: Stocks with morning volatility and clear directional moves
    """
    
    # Strategy parameters
    opening_range_bars = 6   # 30 minutes with 5-min bars
    volume_threshold = 1.8   # Volume must be 1.8x average for breakout
    profit_multiplier = 2.0  # Target = 2x opening range
    
    def init(self):
        super().init()
        
        self.opening_high = None
        self.opening_low = None
        self.opening_range = None
        self.bar_count = 0
        
        # Volume moving average
        self.avg_volume = self.I(lambda v: ta.sma(pd.Series(v), 20).bfill().values, self.data.Volume)
    
    def next(self):
        """Trading logic executed on each bar"""
        
        # Check daily loss limit
        if self.check_daily_loss_limit():
            if self.position:
                self.position.close()
            return
        
        # Close positions at EOD
        if self.should_close_eod():
            if self.position:
                self.position.close()
            return
        
        self.bar_count += 1
        price = self.data.Close[-1]
        volume = self.data.Volume[-1]
        avg_vol = self.avg_volume[-1]
        
        # Establish opening range (first N bars)
        if self.bar_count <= self.opening_range_bars:
            if self.opening_high is None:
                self.opening_high = self.data.High[-1]
                self.opening_low = self.data.Low[-1]
            else:
                self.opening_high = max(self.opening_high, self.data.High[-1])
                self.opening_low = min(self.opening_low, self.data.Low[-1])
                self.opening_range = self.opening_high - self.opening_low
            return
        
        # Volume confirmation for breakout
        volume_confirmed = volume > self.volume_threshold * avg_vol
        
        if not self.position and volume_confirmed and self.opening_range:
            # LONG: Breakout above opening high
            if price > self.opening_high:
                sl_price = self.opening_low
                tp_price = self.opening_high + self.profit_multiplier * self.opening_range
                self.buy(sl=sl_price, tp=tp_price)
            
            # SHORT: Breakdown below opening low
            elif price < self.opening_low:
                sl_price = self.opening_high
                tp_price = self.opening_low - self.profit_multiplier * self.opening_range
                self.sell(sl=sl_price, tp=tp_price)


class MomentumGapStrategy(BaseDayTradingStrategy):
    """
    Momentum/Gap-and-Go Strategy
    
    Entry Signals:
    - LONG: Gap up >2% + continued momentum (RSI > 60, MACD positive)
    - SHORT: Gap down >2% + continued momentum (RSI < 40, MACD negative)
    
    Exit Signals:
    - Momentum exhaustion: RSI overbought/oversold + divergence
    - Stop loss: 3x ATR
    - EOD: Close all positions
    
    Best for: Stocks with catalysts (earnings, news) causing gaps
    """
    
    # Strategy parameters
    gap_threshold = 0.02     # 2% gap required
    rsi_long_entry = 60      # RSI must be > 60 for long
    rsi_short_entry = 40     # RSI must be < 40 for short
    rsi_overbought = 75      # Exit long when RSI > 75
    rsi_oversold = 25        # Exit short when RSI < 25
    sl_multiplier = 3.0      # Stop loss at 3x ATR
    
    def init(self):
        super().init()
        
        # Momentum indicators
        self.rsi = self.I(lambda c: ta.rsi(pd.Series(c), 14).bfill().values, self.data.Close)
        
        # MACD
        macd_df = ta.macd(pd.Series(self.data.Close), fast=12, slow=26, signal=9)
        self.macd = self.I(lambda: macd_df['MACD_12_26_9'].bfill().values)
        self.macd_signal = self.I(lambda: macd_df['MACDs_12_26_9'].bfill().values)
        
        # Track previous close for gap detection
        self.prev_close = None
    
    def next(self):
        """Trading logic executed on each bar"""
        
        # Check daily loss limit
        if self.check_daily_loss_limit():
            if self.position:
                self.position.close()
            return
        
        # Close positions at EOD
        if self.should_close_eod():
            if self.position:
                self.position.close()
            return
        
        price = self.data.Close[-1]
        rsi = self.rsi[-1]
        macd = self.macd[-1]
        macd_sig = self.macd_signal[-1]
        atr = self.atr[-1]
        
        # Detect gap on first bar of the day
        if self.prev_close is None or len(self.data) == 1:
            self.prev_close = price
            return
        
        gap_size = (price - self.prev_close) / self.prev_close
        
        if not self.position:
            # LONG: Gap up with momentum
            if gap_size > self.gap_threshold and rsi > self.rsi_long_entry and macd > macd_sig:
                sl_price = price - self.sl_multiplier * atr
                self.buy(sl=sl_price)
            
            # SHORT: Gap down with momentum
            elif gap_size < -self.gap_threshold and rsi < self.rsi_short_entry and macd < macd_sig:
                sl_price = price + self.sl_multiplier * atr
                self.sell(sl=sl_price)
        else:
            # Exit on momentum exhaustion
            if self.position.is_long and rsi > self.rsi_overbought:
                self.position.close()
            elif self.position.is_short and rsi < self.rsi_oversold:
                self.position.close()
        
        # Update previous close for next bar
        self.prev_close = price


# Strategy registry for easy access
DAY_TRADING_STRATEGIES = {
    'vwap': VWAPTradingStrategy,
    'orb': OpeningRangeBreakoutStrategy,
    'momentum': MomentumGapStrategy,
}
