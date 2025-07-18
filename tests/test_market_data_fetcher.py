"""
Unit tests for market data fetcher service.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from src.services.market_data_fetcher import (
    MarketDataFetcher, 
    get_stock_price, 
    get_vix_value, 
    get_market_data
)


class TestMarketDataFetcher:
    """Test cases for MarketDataFetcher class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = MarketDataFetcher()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    @patch('src.services.market_data_fetcher.get_current_utc_timestamp')
    def test_fetch_stock_price_success(self, mock_timestamp, mock_ticker):
        """Test successful stock price fetching."""
        # Mock timestamp
        test_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = test_timestamp
        
        # Mock yfinance ticker
        mock_stock = Mock()
        mock_stock.info = {'currentPrice': 450.25}
        mock_ticker.return_value = mock_stock
        
        # Test the function
        price, timestamp = self.fetcher.fetch_stock_price('SPY')
        
        # Assertions
        assert price == 450.25
        assert timestamp == test_timestamp
        mock_ticker.assert_called_once_with('SPY')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    @patch('src.services.market_data_fetcher.get_current_utc_timestamp')
    def test_fetch_stock_price_fallback_fields(self, mock_timestamp, mock_ticker):
        """Test stock price fetching with fallback to different price fields."""
        # Mock timestamp
        test_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = test_timestamp
        
        # Mock yfinance ticker with regularMarketPrice instead of currentPrice
        mock_stock = Mock()
        mock_stock.info = {'regularMarketPrice': 451.75}
        mock_ticker.return_value = mock_stock
        
        # Test the function
        price, timestamp = self.fetcher.fetch_stock_price('AAPL')
        
        # Assertions
        assert price == 451.75
        assert timestamp == test_timestamp
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_price_no_valid_price(self, mock_ticker):
        """Test stock price fetching when no valid price is available."""
        # Mock yfinance ticker with no valid price fields
        mock_stock = Mock()
        mock_stock.info = {'someOtherField': 'value'}
        mock_ticker.return_value = mock_stock
        
        # Test the function - should raise ValueError
        with pytest.raises(ValueError, match="Unable to fetch valid price for ticker TEST"):
            self.fetcher.fetch_stock_price('TEST')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_price_zero_price(self, mock_ticker):
        """Test stock price fetching when price is zero."""
        # Mock yfinance ticker with zero price
        mock_stock = Mock()
        mock_stock.info = {'currentPrice': 0}
        mock_ticker.return_value = mock_stock
        
        # Test the function - should raise ValueError
        with pytest.raises(ValueError, match="Unable to fetch valid price for ticker TEST"):
            self.fetcher.fetch_stock_price('TEST')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_price_api_error(self, mock_ticker):
        """Test stock price fetching when yfinance API fails."""
        # Mock yfinance ticker to raise an exception
        mock_ticker.side_effect = Exception("API Error")
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch stock price for TEST"):
            self.fetcher.fetch_stock_price('TEST')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    @patch('src.services.market_data_fetcher.get_current_utc_timestamp')
    def test_fetch_vix_value_success(self, mock_timestamp, mock_ticker):
        """Test successful VIX value fetching."""
        # Mock timestamp
        test_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = test_timestamp
        
        # Mock yfinance ticker for VIX
        mock_vix = Mock()
        mock_vix.info = {'currentPrice': 18.75}
        mock_ticker.return_value = mock_vix
        
        # Test the function
        vix_value, timestamp = self.fetcher.fetch_vix_value()
        
        # Assertions
        assert vix_value == 18.75
        assert timestamp == test_timestamp
        mock_ticker.assert_called_once_with('^VIX')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_vix_value_no_valid_price(self, mock_ticker):
        """Test VIX value fetching when no valid price is available."""
        # Mock yfinance ticker with no valid price fields
        mock_vix = Mock()
        mock_vix.info = {'someOtherField': 'value'}
        mock_ticker.return_value = mock_vix
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch VIX data"):
            self.fetcher.fetch_vix_value()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_vix_value_api_error(self, mock_ticker):
        """Test VIX value fetching when yfinance API fails."""
        # Mock yfinance ticker to raise an exception
        mock_ticker.side_effect = Exception("API Error")
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch VIX data"):
            self.fetcher.fetch_vix_value()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    @patch('src.services.market_data_fetcher.get_current_utc_timestamp')
    def test_fetch_market_data_success(self, mock_timestamp, mock_ticker):
        """Test successful fetching of both stock price and VIX value."""
        # Mock timestamps
        stock_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        vix_timestamp = datetime(2025, 1, 16, 14, 30, 5, tzinfo=timezone.utc)
        mock_timestamp.side_effect = [stock_timestamp, vix_timestamp]
        
        # Mock yfinance ticker calls
        def mock_ticker_side_effect(symbol):
            if symbol == 'SPY':
                mock_stock = Mock()
                mock_stock.info = {'currentPrice': 450.25}
                return mock_stock
            elif symbol == '^VIX':
                mock_vix = Mock()
                mock_vix.info = {'currentPrice': 18.75}
                return mock_vix
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Test the function
        stock_price, vix_value, stock_ts, vix_ts = self.fetcher.fetch_market_data('SPY')
        
        # Assertions
        assert stock_price == 450.25
        assert vix_value == 18.75
        assert stock_ts == stock_timestamp
        assert vix_ts == vix_timestamp
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_market_data_stock_error(self, mock_ticker):
        """Test market data fetching when stock price fetch fails."""
        # Mock yfinance ticker to fail for stock but succeed for VIX
        def mock_ticker_side_effect(symbol):
            if symbol == 'SPY':
                raise Exception("Stock API Error")
            elif symbol == '^VIX':
                mock_vix = Mock()
                mock_vix.info = {'currentPrice': 18.75}
                return mock_vix
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch market data"):
            self.fetcher.fetch_market_data('SPY')


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher')
    def test_get_stock_price(self, mock_fetcher_class):
        """Test get_stock_price convenience function."""
        # Mock the fetcher instance and method
        mock_fetcher = Mock()
        mock_fetcher.fetch_stock_price.return_value = (450.25, datetime.now(timezone.utc))
        mock_fetcher_class.return_value = mock_fetcher
        
        # Test the function
        price, timestamp = get_stock_price('SPY')
        
        # Assertions
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_stock_price.assert_called_once_with('SPY')
        assert price == 450.25
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher')
    def test_get_vix_value(self, mock_fetcher_class):
        """Test get_vix_value convenience function."""
        # Mock the fetcher instance and method
        mock_fetcher = Mock()
        mock_fetcher.fetch_vix_value.return_value = (18.75, datetime.now(timezone.utc))
        mock_fetcher_class.return_value = mock_fetcher
        
        # Test the function
        vix_value, timestamp = get_vix_value()
        
        # Assertions
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_vix_value.assert_called_once()
        assert vix_value == 18.75
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher')
    def test_get_market_data(self, mock_fetcher_class):
        """Test get_market_data convenience function."""
        # Mock the fetcher instance and method
        mock_fetcher = Mock()
        test_timestamps = (datetime.now(timezone.utc), datetime.now(timezone.utc))
        mock_fetcher.fetch_market_data.return_value = (450.25, 18.75, *test_timestamps)
        mock_fetcher_class.return_value = mock_fetcher
        
        # Test the function
        stock_price, vix_value, stock_ts, vix_ts = get_market_data('SPY')
        
        # Assertions
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_market_data.assert_called_once_with('SPY')
        assert stock_price == 450.25
        assert vix_value == 18.75


class TestMarketDataFetcherEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = MarketDataFetcher()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    @patch('src.services.market_data_fetcher.get_current_utc_timestamp')
    def test_fetch_stock_price_with_previousClose(self, mock_timestamp, mock_ticker):
        """Test stock price fetching using previousClose as fallback."""
        # Mock timestamp
        test_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = test_timestamp
        
        # Mock yfinance ticker with only previousClose available
        mock_stock = Mock()
        mock_stock.info = {'previousClose': 449.80}
        mock_ticker.return_value = mock_stock
        
        # Test the function
        price, timestamp = self.fetcher.fetch_stock_price('SPY')
        
        # Assertions
        assert price == 449.80
        assert timestamp == test_timestamp
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    @patch('src.services.market_data_fetcher.get_current_utc_timestamp')
    def test_fetch_vix_value_with_regularMarketPrice(self, mock_timestamp, mock_ticker):
        """Test VIX value fetching using regularMarketPrice."""
        # Mock timestamp
        test_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = test_timestamp
        
        # Mock yfinance ticker with regularMarketPrice
        mock_vix = Mock()
        mock_vix.info = {'regularMarketPrice': 19.25}
        mock_ticker.return_value = mock_vix
        
        # Test the function
        vix_value, timestamp = self.fetcher.fetch_vix_value()
        
        # Assertions
        assert vix_value == 19.25
        assert timestamp == test_timestamp
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_price_negative_price(self, mock_ticker):
        """Test stock price fetching when price is negative."""
        # Mock yfinance ticker with negative price
        mock_stock = Mock()
        mock_stock.info = {'currentPrice': -10.0}
        mock_ticker.return_value = mock_stock
        
        # Test the function - should raise ValueError
        with pytest.raises(ValueError, match="Unable to fetch valid price for ticker TEST"):
            self.fetcher.fetch_stock_price('TEST')