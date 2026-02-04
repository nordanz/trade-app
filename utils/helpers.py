"""Helper utility functions."""

from datetime import datetime
from typing import Optional
import pandas as pd


def format_large_number(num: Optional[float]) -> str:
    """
    Format large numbers with K, M, B, T suffixes.
    
    Args:
        num: Number to format
    
    Returns:
        Formatted string
    """
    if num is None or pd.isna(num):
        return "N/A"
    
    num = float(num)
    
    if abs(num) >= 1_000_000_000_000:
        return f"${num/1_000_000_000_000:.2f}T"
    elif abs(num) >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif abs(num) >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif abs(num) >= 1_000:
        return f"${num/1_000:.2f}K"
    else:
        return f"${num:.2f}"


def format_percentage(value: Optional[float], decimal_places: int = 2) -> str:
    """
    Format percentage values.
    
    Args:
        value: Percentage value
        decimal_places: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    if value is None or pd.isna(value):
        return "N/A"
    
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimal_places}f}%"


def format_price(price: Optional[float], decimal_places: int = 2) -> str:
    """
    Format price values.
    
    Args:
        price: Price value
        decimal_places: Number of decimal places
    
    Returns:
        Formatted price string
    """
    if price is None or pd.isna(price):
        return "N/A"
    
    return f"${price:.{decimal_places}f}"


def get_price_color(change_percent: float) -> str:
    """
    Get color based on price change.
    
    Args:
        change_percent: Percentage change
    
    Returns:
        Color string (green/red)
    """
    return "green" if change_percent >= 0 else "red"


def calculate_risk_reward_ratio(entry: float, target: float, stop_loss: float) -> float:
    """
    Calculate risk/reward ratio.
    
    Args:
        entry: Entry price
        target: Target price
        stop_loss: Stop loss price
    
    Returns:
        Risk/reward ratio
    """
    potential_profit = target - entry
    potential_loss = entry - stop_loss
    
    if potential_loss == 0:
        return 0
    
    return potential_profit / potential_loss


def get_signal_emoji(signal: str) -> str:
    """
    Get emoji for trading signal.
    
    Args:
        signal: Signal type (BUY/SELL/HOLD)
    
    Returns:
        Emoji string
    """
    emojis = {
        "BUY": "🟢",
        "SELL": "🔴",
        "HOLD": "🟡"
    }
    return emojis.get(signal, "⚪")


def get_sentiment_emoji(sentiment: str) -> str:
    """
    Get emoji for sentiment.
    
    Args:
        sentiment: Sentiment type
    
    Returns:
        Emoji string
    """
    emojis = {
        "POSITIVE": "😊",
        "NEGATIVE": "😟",
        "NEUTRAL": "😐"
    }
    return emojis.get(sentiment, "🤔")


def timestamp_to_string(timestamp: datetime) -> str:
    """
    Convert timestamp to readable string.
    
    Args:
        timestamp: Datetime object
    
    Returns:
        Formatted string
    """
    if timestamp is None:
        return "N/A"
    
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division fails
    
    Returns:
        Result of division or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
