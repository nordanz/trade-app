"""Technical indicators calculation utilities."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        data: Price series
        period: RSI period (default: 14)
    
    Returns:
        RSI values as pandas Series
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        data: Price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
    
    Returns:
        Dictionary with MACD, signal, and histogram
    """
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return {
        "macd": macd,
        "signal": signal_line,
        "histogram": histogram
    }


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        data: Price series
        period: Moving average period
        std_dev: Number of standard deviations
    
    Returns:
        Dictionary with upper, middle, and lower bands
    """
    middle = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return {
        "upper": upper,
        "middle": middle,
        "lower": lower
    }


def calculate_moving_averages(data: pd.Series) -> Dict[str, float]:
    """
    Calculate multiple moving averages.
    
    Args:
        data: Price series
    
    Returns:
        Dictionary with MA20, MA50, MA200
    """
    return {
        "ma_20": data.rolling(window=20).mean().iloc[-1] if len(data) >= 20 else None,
        "ma_50": data.rolling(window=50).mean().iloc[-1] if len(data) >= 50 else None,
        "ma_200": data.rolling(window=200).mean().iloc[-1] if len(data) >= 200 else None
    }


def identify_support_resistance(data: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
    """
    Identify support and resistance levels.
    
    Args:
        data: DataFrame with OHLC data
        window: Lookback window
    
    Returns:
        Tuple of (support, resistance) levels
    """
    if len(data) < window:
        return None, None
    
    recent_data = data.tail(window)
    support = recent_data['Low'].min()
    resistance = recent_data['High'].max()
    
    return support, resistance


def calculate_volatility(data: pd.Series, period: int = 20) -> float:
    """
    Calculate historical volatility.
    
    Args:
        data: Price series
        period: Period for calculation
    
    Returns:
        Volatility as standard deviation
    """
    returns = data.pct_change()
    volatility = returns.rolling(window=period).std().iloc[-1]
    return volatility * 100 if not pd.isna(volatility) else 0


def detect_trend(data: pd.Series, short_period: int = 20, long_period: int = 50) -> str:
    """
    Detect price trend using moving averages.
    
    Args:
        data: Price series
        short_period: Short MA period
        long_period: Long MA period
    
    Returns:
        Trend: "UPTREND", "DOWNTREND", or "SIDEWAYS"
    """
    if len(data) < long_period:
        return "INSUFFICIENT_DATA"
    
    ma_short = data.rolling(window=short_period).mean().iloc[-1]
    ma_long = data.rolling(window=long_period).mean().iloc[-1]
    
    if ma_short > ma_long * 1.02:  # 2% threshold
        return "UPTREND"
    elif ma_short < ma_long * 0.98:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"


def calculate_volume_profile(data: pd.DataFrame, period: int = 20) -> Dict[str, any]:
    """
    Analyze volume patterns.
    
    Args:
        data: DataFrame with volume data
        period: Period for analysis
    
    Returns:
        Dictionary with volume metrics
    """
    recent_data = data.tail(period)
    avg_volume = recent_data['Volume'].mean()
    current_volume = data['Volume'].iloc[-1]
    
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    return {
        "current_volume": int(current_volume),
        "avg_volume": int(avg_volume),
        "volume_ratio": round(volume_ratio, 2),
        "volume_trend": "HIGH" if volume_ratio > 1.5 else "NORMAL" if volume_ratio > 0.5 else "LOW"
    }


def is_golden_cross(data: pd.Series) -> bool:
    """
    Check for golden cross (50-day MA crosses above 200-day MA).
    
    Args:
        data: Price series
    
    Returns:
        True if golden cross detected
    """
    if len(data) < 200:
        return False
    
    ma_50 = data.rolling(window=50).mean()
    ma_200 = data.rolling(window=200).mean()
    
    # Check if MA50 recently crossed above MA200
    if len(ma_50) >= 2 and len(ma_200) >= 2:
        crossed_above = ma_50.iloc[-2] <= ma_200.iloc[-2] and ma_50.iloc[-1] > ma_200.iloc[-1]
        return crossed_above
    
    return False


def is_death_cross(data: pd.Series) -> bool:
    """
    Check for death cross (50-day MA crosses below 200-day MA).
    
    Args:
        data: Price series
    
    Returns:
        True if death cross detected
    """
    if len(data) < 200:
        return False
    
    ma_50 = data.rolling(window=50).mean()
    ma_200 = data.rolling(window=200).mean()
    
    # Check if MA50 recently crossed below MA200
    if len(ma_50) >= 2 and len(ma_200) >= 2:
        crossed_below = ma_50.iloc[-2] >= ma_200.iloc[-2] and ma_50.iloc[-1] < ma_200.iloc[-1]
        return crossed_below
    
    return False


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    """
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr


def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """
    Calculate Volume Weighted Average Price (VWAP).
    """
    v = data['Volume']
    p = (data['High'] + data['Low'] + data['Close']) / 3
    return (p * v).cumsum() / v.cumsum()


def calculate_pivot_points(data: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate daily pivot points based on the last row (previous day).
    """
    if data.empty:
        return {}
    
    last = data.iloc[-1]
    h, l, c = last['High'], last['Low'], last['Close']
    
    p = (h + l + c) / 3
    r1 = (2 * p) - l
    s1 = (2 * p) - h
    r2 = p + (h - l)
    s2 = p - (h - l)
    
    return {
        "pivot": float(p),
        "r1": float(r1),
        "s1": float(s1),
        "r2": float(r2),
        "s2": float(s2)
    }


def calculate_fibonacci_levels(data: pd.DataFrame, window: int = 50) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels based on a lookback window.
    """
    if len(data) < window:
        return {}
    
    recent = data.tail(window)
    max_price = recent['High'].max()
    min_price = recent['Low'].min()
    diff = max_price - min_price
    
    return {
        "level_0": float(max_price),
        "level_236": float(max_price - 0.236 * diff),
        "level_382": float(max_price - 0.382 * diff),
        "level_500": float(max_price - 0.5 * diff),
        "level_618": float(max_price - 0.618 * diff),
        "level_100": float(min_price)
    }
