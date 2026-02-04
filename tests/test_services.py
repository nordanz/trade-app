"""Simple tests for the services."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.market_data_service import MarketDataService
from services.trading_strategy_service import TradingStrategyService


def test_market_data_service():
    """Test market data service."""
    print("Testing Market Data Service...")
    service = MarketDataService()
    
    # Test single stock
    stock = service.get_stock_data("AAPL")
    if stock:
        print(f"✅ Successfully fetched data for AAPL")
        print(f"   Price: ${stock.current_price:.2f}")
        print(f"   Change: {stock.change_percent:+.2f}%")
    else:
        print("❌ Failed to fetch data for AAPL")
    
    print()


def test_trading_strategy_service():
    """Test trading strategy service."""
    print("Testing Trading Strategy Service...")
    service = TradingStrategyService()
    
    # Test indicators calculation
    indicators = service.calculate_all_indicators("AAPL")
    if indicators:
        print(f"✅ Successfully calculated indicators for AAPL")
        print(f"   RSI: {indicators.get('rsi', 'N/A')}")
        print(f"   Trend: {indicators.get('trend', 'N/A')}")
    else:
        print("❌ Failed to calculate indicators")
    
    print()
    
    # Test signal generation
    signal = service.generate_signal("AAPL")
    if signal:
        print(f"✅ Successfully generated signal for AAPL")
        print(f"   Signal: {signal.signal.value}")
        print(f"   Confidence: {signal.confidence:.0f}%")
        print(f"   Entry: ${signal.entry_price:.2f}")
    else:
        print("❌ Failed to generate signal")
    
    print()


def main():
    """Run all tests."""
    print("=" * 50)
    print("Running Tests for Stock Market Dashboard")
    print("=" * 50)
    print()
    
    test_market_data_service()
    test_trading_strategy_service()
    
    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
