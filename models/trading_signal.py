"""Data models for trading signals."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from enum import Enum


class SignalType(Enum):
    """Types of trading signals."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Sentiment(Enum):
    """Sentiment types."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


@dataclass
class TradingSignal:
    """Model for trading signals."""
    
    symbol: str
    signal: SignalType
    confidence: float  # 0-100
    entry_price: float
    target_price: float
    stop_loss: float
    holding_period: str
    reasoning: str
    indicators: Dict[str, any]
    news_analysis: Optional['NewsAnalysis'] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if isinstance(self.signal, str):
            self.signal = SignalType(self.signal)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "holding_period": self.holding_period,
            "reasoning": self.reasoning,
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class NewsAnalysis:
    """Model for news analysis."""
    
    symbol: str
    headline: str
    summary: str
    sentiment: Sentiment
    sentiment_score: float  # -1 to 1
    relevance: float  # 0-100
    source: str
    macro_impact: bool = False  # True if affects broader market
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if isinstance(self.sentiment, str):
            self.sentiment = Sentiment(self.sentiment)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "headline": self.headline,
            "summary": self.summary,
            "sentiment": self.sentiment.value,
            "sentiment_score": self.sentiment_score,
            "relevance": self.relevance,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
