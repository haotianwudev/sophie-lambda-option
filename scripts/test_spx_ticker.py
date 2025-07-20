"""
Test script to verify that the ^SPX ticker symbol works.
"""
import sys
sys.path.append('.')

from src.utils.data_formatter import validate_ticker_symbol
from src.services.options_data_fetcher import OptionsDataFetcher
from src.services.market_data_fetcher import MarketDataFetcher

def test_ticker_validation():
    """Test ticker symbol validation."""
    print("Testing ticker symbol validation...")
    
    # Test regular ticker
    try:
        ticker = validate_ticker_symbol("SPY")
        print(f"✓ Regular ticker validation passed: {ticker}")
    except ValueError as e:
        print(f"✗ Regular ticker validation failed: {e}")
    
    # Test index ticker with caret
    try:
        ticker = validate_ticker_symbol("^SPX")
        print(f"✓ Index ticker validation passed: {ticker}")
    except ValueError as e:
        print(f"✗ Index ticker validation failed: {e}")

def test_options_data_fetcher():
    """Test options data fetcher with ^SPX ticker."""
    print("\nTesting options data fetcher...")
    
    fetcher = OptionsDataFetcher()
    
    # Test ticker validation
    try:
        ticker = fetcher.validate_ticker("^SPX")
        print(f"✓ Options fetcher ticker validation passed: {ticker}")
    except ValueError as e:
        print(f"✗ Options fetcher ticker validation failed: {e}")
    
    # Test fetching expiration dates
    try:
        expiration_dates = fetcher.fetch_option_expiration_dates("^SPX")
        print(f"✓ Fetched {len(expiration_dates)} expiration dates for ^SPX")
        print(f"  First few dates: {expiration_dates[:3]}")
    except Exception as e:
        print(f"✗ Failed to fetch expiration dates: {e}")

def test_market_data_fetcher():
    """Test market data fetcher with ^SPX ticker."""
    print("\nTesting market data fetcher...")
    
    fetcher = MarketDataFetcher()
    
    # Test fetching stock price
    try:
        price, timestamp = fetcher.fetch_stock_price("^SPX")
        print(f"✓ Fetched ^SPX price: {price} at {timestamp}")
    except Exception as e:
        print(f"✗ Failed to fetch ^SPX price: {e}")

if __name__ == "__main__":
    print("Testing ^SPX ticker symbol support...\n")
    
    # Run tests
    test_ticker_validation()
    test_options_data_fetcher()
    test_market_data_fetcher()
    
    print("\nTests completed.")