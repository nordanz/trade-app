"""Market data service for fetching live stock data."""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict
from datetime import datetime
from models.stock_data import StockData
from utils.indicators import calculate_moving_averages
from config.settings import settings


class MarketDataService:
    """Service for fetching and processing market data."""
    
    def __init__(self):
        """Initialize market data service."""
        self.cache = {}
        self.cache_timeout = 60  # seconds
    
    def get_stock_data(self, symbol: str) -> Optional[StockData]:
        """
        Fetch current stock data for a given symbol.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            StockData object or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current info
            info = ticker.info
            
            # Get recent history for calculations
            hist = ticker.history(period="1d")
            
            if hist.empty:
                print(f"No data available for {symbol}")
                return None
            
            # Get latest price data
            latest = hist.iloc[-1]
            current_price = latest['Close']
            
            # Calculate change percentage
            open_price = latest['Open']
            change_percent = ((current_price - open_price) / open_price * 100) if open_price > 0 else 0
            
            # Get additional data
            market_cap = info.get('marketCap')
            pe_ratio = info.get('trailingPE')
            week_52_high = info.get('fiftyTwoWeekHigh')
            week_52_low = info.get('fiftyTwoWeekLow')
            
            # Get historical data for moving averages
            hist_data = ticker.history(period=settings.HISTORICAL_PERIOD)
            moving_avgs = calculate_moving_averages(hist_data['Close']) if not hist_data.empty else {}
            
            stock_data = StockData(
                symbol=symbol.upper(),
                current_price=float(current_price),
                open_price=float(open_price),
                high=float(latest['High']),
                low=float(latest['Low']),
                volume=int(latest['Volume']),
                change_percent=float(change_percent),
                market_cap=float(market_cap) if market_cap else None,
                pe_ratio=float(pe_ratio) if pe_ratio else None,
                week_52_high=float(week_52_high) if week_52_high else None,
                week_52_low=float(week_52_low) if week_52_low else None,
                moving_averages=moving_avgs,
                timestamp=datetime.now()
            )
            
            return stock_data
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
        """
        Get historical price data.
        
        Args:
            symbol: Stock ticker symbol
            period: Data period (e.g., "1mo", "3mo", "1y")
            interval: Data interval (e.g., "1d", "1h")
        
        Returns:
            DataFrame with historical data
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            return hist
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_multiple_stocks(self, symbols: list) -> Dict[str, StockData]:
        """
        Fetch data for multiple stocks.
        
        Args:
            symbols: List of ticker symbols
        
        Returns:
            Dictionary mapping symbols to StockData objects
        """
        results = {}
        for symbol in symbols:
            stock_data = self.get_stock_data(symbol)
            if stock_data:
                results[symbol.upper()] = stock_data
        return results
    
    def get_company_info(self, symbol: str) -> Dict:
        """
        Get detailed company information.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dictionary with company info
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "description": info.get("longBusinessSummary", ""),
                "website": info.get("website", ""),
                "employees": info.get("fullTimeEmployees"),
                "country": info.get("country", "N/A")
            }
        except Exception as e:
            print(f"Error fetching company info for {symbol}: {str(e)}")
            return {}
    
    def search_ticker(self, query: str) -> list:
        """
        Search for ticker symbols.
        
        Args:
            query: Search query
        
        Returns:
            List of matching ticker symbols
        """
        # Note: yfinance doesn't have built-in search
        # This is a placeholder for future enhancement
        return [query.upper()]
    
    def get_market_status(self) -> Dict:
        """
        Get current market status.
        
        Returns:
            Dictionary with market status info
        """
        try:
            # Use SPY as proxy for market status
            spy = yf.Ticker("SPY")
            info = spy.info
            
            return {
                "is_open": info.get("marketState") == "REGULAR",
                "market_state": info.get("marketState", "UNKNOWN"),
                "timezone": info.get("timeZoneFullName", "America/New_York")
            }
        except Exception as e:
            print(f"Error fetching market status: {str(e)}")
            return {"is_open": False, "market_state": "UNKNOWN", "timezone": "Unknown"}
