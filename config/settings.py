"""Configuration settings for the Stock Market Dashboard."""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """Application settings and configuration."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    
    # Default configuration
    DEFAULT_TICKERS: list = os.getenv("DEFAULT_TICKERS", "AAPL,GOOGL,MSFT,TSLA,NVDA").split(",")
    REFRESH_INTERVAL: int = int(os.getenv("REFRESH_INTERVAL", "60"))
    
    # Trading Strategy Parameters
    RSI_OVERSOLD: int = int(os.getenv("RSI_OVERSOLD", "30"))
    RSI_OVERBOUGHT: int = int(os.getenv("RSI_OVERBOUGHT", "70"))
    MACD_FAST: int = int(os.getenv("MACD_FAST", "12"))
    MACD_SLOW: int = int(os.getenv("MACD_SLOW", "26"))
    MACD_SIGNAL: int = int(os.getenv("MACD_SIGNAL", "9"))
    
    # Risk Management
    STOP_LOSS_PERCENT: float = 0.05  # 5% stop loss
    TARGET_PROFIT_PERCENT: float = 0.10  # 10% target profit
    MIN_CONFIDENCE: float = 60.0  # Minimum confidence for signals
    
    # Data fetch parameters
    HISTORICAL_PERIOD: str = "3mo"  # 3 months of historical data
    DATA_INTERVAL: str = "1d"  # Daily intervals
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required settings are present."""
        if not cls.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. AI features will be disabled.")
            return False
        return True


settings = Settings()
