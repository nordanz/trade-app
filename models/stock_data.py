"""Data models for stock market data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict


@dataclass
class StockData:
    """Model for stock market data."""
    
    symbol: str
    current_price: float
    open_price: float
    high: float
    low: float
    volume: int
    change_percent: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    moving_averages: Optional[Dict[str, float]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "open_price": self.open_price,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "change_percent": self.change_percent,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "week_52_high": self.week_52_high,
            "week_52_low": self.week_52_low,
            "moving_averages": self.moving_averages,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
