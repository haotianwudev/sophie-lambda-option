"""
Market data fetcher service for options analytics API.
Handles fetching stock prices and VIX data from Yahoo Finance.
"""
import yfinance as yf
from datetime import datetime, timezone
from typing import Tuple, Optional
from src.utils.time_utils import get_current_utc_timestamp


class MarketDataFetcher:
    """Service for fetching market data from Yahoo Finance."""
    
    def __init__(self):
        """Initialize the market data fetcher."""
        self.vix_symbol = "^VIX"
    
    def fetch_stock_price(self, ticker: str) -> Tuple[float, datetime]:
        """
        Fetch current stock price for the given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'SPY', 'AAPL')
            
        Returns:
            Tuple of (stock_price, timestamp)
            
        Raises:
            ValueError: If ticker is invalid or data cannot be fetched
            RuntimeError: If Yahoo Finance API fails
        """
        try:
            # Create yfinance ticker object
            stock = yf.Ticker(ticker)
            
            # Get current stock info
            info = stock.info
            
            # Try to get current price from different fields
            current_price = None
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    current_price = float(info[field])
                    break
            
            if current_price is None or current_price <= 0:
                raise ValueError(f"Unable to fetch valid price for ticker {ticker}")
            
            timestamp = get_current_utc_timestamp()
            return current_price, timestamp
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to fetch stock price for {ticker}: {str(e)}")
    
    def fetch_vix_value(self) -> Tuple[float, datetime]:
        """
        Fetch current VIX value.
        
        Returns:
            Tuple of (vix_value, timestamp)
            
        Raises:
            RuntimeError: If VIX data cannot be fetched
        """
        try:
            # Create yfinance ticker object for VIX
            vix = yf.Ticker(self.vix_symbol)
            
            # Get current VIX info
            info = vix.info
            
            # Try to get current VIX value from different fields
            vix_value = None
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    vix_value = float(info[field])
                    break
            
            if vix_value is None or vix_value <= 0:
                raise ValueError("Unable to fetch valid VIX value")
            
            timestamp = get_current_utc_timestamp()
            return vix_value, timestamp
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise RuntimeError(f"Failed to fetch VIX data: {str(e)}")
            raise RuntimeError(f"Failed to fetch VIX data: {str(e)}")
    
    def fetch_market_data(self, ticker: str) -> Tuple[float, float, datetime, datetime]:
        """
        Fetch both stock price and VIX value.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Tuple of (stock_price, vix_value, stock_timestamp, vix_timestamp)
            
        Raises:
            RuntimeError: If either stock price or VIX data cannot be fetched
        """
        try:
            # Fetch stock price
            stock_price, stock_timestamp = self.fetch_stock_price(ticker)
            
            # Fetch VIX value
            vix_value, vix_timestamp = self.fetch_vix_value()
            
            return stock_price, vix_value, stock_timestamp, vix_timestamp
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch market data: {str(e)}")


# Convenience functions for direct usage
def get_stock_price(ticker: str) -> Tuple[float, datetime]:
    """
    Convenience function to fetch stock price.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (stock_price, timestamp)
    """
    fetcher = MarketDataFetcher()
    return fetcher.fetch_stock_price(ticker)


def get_vix_value() -> Tuple[float, datetime]:
    """
    Convenience function to fetch VIX value.
    
    Returns:
        Tuple of (vix_value, timestamp)
    """
    fetcher = MarketDataFetcher()
    return fetcher.fetch_vix_value()


def get_market_data(ticker: str) -> Tuple[float, float, datetime, datetime]:
    """
    Convenience function to fetch both stock price and VIX value.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (stock_price, vix_value, stock_timestamp, vix_timestamp)
    """
    fetcher = MarketDataFetcher()
    return fetcher.fetch_market_data(ticker)