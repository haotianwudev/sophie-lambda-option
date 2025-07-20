"""
Market data fetcher service for options analytics API.
Handles fetching stock prices and VIX data from Yahoo Finance.
"""
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Dict, Any
from src.utils.time_utils import get_current_utc_timestamp
from src.utils.calculation_utils import calculate_percentage_change


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
            
    def fetch_stock_previous_close(self, ticker: str) -> float:
        """
        Fetch previous day's closing price for the given ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'SPY', 'AAPL')
            
        Returns:
            Previous closing price as float
            
        Raises:
            ValueError: If ticker is invalid or data cannot be fetched
            RuntimeError: If Yahoo Finance API fails
        """
        try:
            # Create yfinance ticker object
            stock = yf.Ticker(ticker)
            
            # Try to get previous close from info
            info = stock.info
            if 'previousClose' in info and info['previousClose'] is not None and float(info['previousClose']) > 0:
                return float(info['previousClose'])
            
            # If not available in info, try to get from history
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)  # Get a week of data to ensure we have the previous close
            
            history = stock.history(start=start_date, end=end_date)
            
            if history.empty:
                raise ValueError(f"No historical data available for ticker {ticker}")
            
            # Get the last available closing price (excluding today if available)
            if len(history) > 1:
                previous_close = history['Close'].iloc[-2]
            else:
                previous_close = history['Close'].iloc[-1]
            
            if previous_close <= 0:
                raise ValueError(f"Invalid previous closing price for ticker {ticker}")
            
            return float(previous_close)
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to fetch previous closing price for {ticker}: {str(e)}")
    
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
            
    def fetch_vix_previous_close(self) -> float:
        """
        Fetch previous day's VIX value.
        
        Returns:
            Previous VIX closing value as float
            
        Raises:
            RuntimeError: If VIX data cannot be fetched
        """
        try:
            # Create yfinance ticker object for VIX
            vix = yf.Ticker(self.vix_symbol)
            
            # Try to get previous close from info
            info = vix.info
            if 'previousClose' in info and info['previousClose'] is not None and float(info['previousClose']) > 0:
                return float(info['previousClose'])
            
            # If not available in info, try to get from history
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)  # Get a week of data to ensure we have the previous close
            
            history = vix.history(start=start_date, end=end_date)
            
            if history.empty:
                raise ValueError("No historical VIX data available")
            
            # Get the last available closing price (excluding today if available)
            if len(history) > 1:
                previous_close = history['Close'].iloc[-2]
            else:
                previous_close = history['Close'].iloc[-1]
            
            if previous_close <= 0:
                raise ValueError("Invalid previous VIX closing value")
            
            return float(previous_close)
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise RuntimeError(f"Failed to fetch previous VIX data: {str(e)}")
            raise RuntimeError(f"Failed to fetch previous VIX data: {str(e)}")
    
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
            
    def fetch_enhanced_market_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch enhanced market data including current prices, previous closing prices,
        and percentage changes for both stock and VIX.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with enhanced market data:
            {
                'stock': {
                    'price': float,
                    'previousClose': float,
                    'percentChange': float,
                    'timestamp': datetime
                },
                'vix': {
                    'value': float,
                    'previousClose': float,
                    'percentChange': float,
                    'timestamp': datetime
                }
            }
            
        Raises:
            RuntimeError: If market data cannot be fetched
        """
        try:
            # Fetch current stock price and timestamp
            stock_price, stock_timestamp = self.fetch_stock_price(ticker)
            
            # Fetch previous closing price for stock
            stock_prev_close = self.fetch_stock_previous_close(ticker)
            
            # Calculate percentage change for stock
            stock_pct_change = calculate_percentage_change(stock_price, stock_prev_close)
            
            # Fetch current VIX value and timestamp
            vix_value, vix_timestamp = self.fetch_vix_value()
            
            # Fetch previous closing value for VIX
            vix_prev_close = self.fetch_vix_previous_close()
            
            # Calculate percentage change for VIX
            vix_pct_change = calculate_percentage_change(vix_value, vix_prev_close)
            
            # Construct the enhanced market data dictionary
            enhanced_data = {
                'stock': {
                    'price': stock_price,
                    'previousClose': stock_prev_close,
                    'percentChange': stock_pct_change,
                    'timestamp': stock_timestamp
                },
                'vix': {
                    'value': vix_value,
                    'previousClose': vix_prev_close,
                    'percentChange': vix_pct_change,
                    'timestamp': vix_timestamp
                }
            }
            
            return enhanced_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch enhanced market data: {str(e)}")


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


def get_stock_previous_close(ticker: str) -> float:
    """
    Convenience function to fetch previous day's closing price for a stock.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Previous closing price as float
    """
    fetcher = MarketDataFetcher()
    return fetcher.fetch_stock_previous_close(ticker)


def get_vix_previous_close() -> float:
    """
    Convenience function to fetch previous day's VIX value.
    
    Returns:
        Previous VIX closing value as float
    """
    fetcher = MarketDataFetcher()
    return fetcher.fetch_vix_previous_close()


def get_enhanced_market_data(ticker: str) -> Dict[str, Any]:
    """
    Convenience function to fetch enhanced market data including current prices,
    previous closing prices, and percentage changes for both stock and VIX.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with enhanced market data
    """
    fetcher = MarketDataFetcher()
    return fetcher.fetch_enhanced_market_data(ticker)