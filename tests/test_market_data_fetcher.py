"""
Unit tests for market data fetcher service.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import pandas as pd
from src.services.market_data_fetcher import (
    MarketDataFetcher, 
    get_stock_price, 
    get_vix_value, 
    get_market_data,
    get_stock_previous_close,
    get_vix_previous_close,
    get_enhanced_market_data
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


class TestPreviousCloseAndEnhancedData:
    """Test cases for previous close and enhanced data functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = MarketDataFetcher()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_previous_close_from_info(self, mock_ticker):
        """Test fetching stock previous close from info."""
        # Mock yfinance ticker with previousClose in info
        mock_stock = Mock()
        mock_stock.info = {'previousClose': 445.75}
        mock_ticker.return_value = mock_stock
        
        # Test the function
        prev_close = self.fetcher.fetch_stock_previous_close('SPY')
        
        # Assertions
        assert prev_close == 445.75
        mock_ticker.assert_called_once_with('SPY')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_previous_close_from_history(self, mock_ticker):
        """Test fetching stock previous close from history."""
        # Mock yfinance ticker with history but no previousClose in info
        mock_stock = Mock()
        mock_stock.info = {'someOtherField': 'value'}
        
        # Create a mock history DataFrame
        history_data = {'Close': [440.0, 445.0, 450.0]}
        mock_history = pd.DataFrame(history_data)
        mock_stock.history.return_value = mock_history
        
        mock_ticker.return_value = mock_stock
        
        # Test the function
        prev_close = self.fetcher.fetch_stock_previous_close('SPY')
        
        # Assertions
        assert prev_close == 445.0  # Second-to-last value in the history
        mock_ticker.assert_called_once_with('SPY')
        mock_stock.history.assert_called_once()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_previous_close_single_history_entry(self, mock_ticker):
        """Test fetching stock previous close with only one history entry."""
        # Mock yfinance ticker with only one history entry
        mock_stock = Mock()
        mock_stock.info = {'someOtherField': 'value'}
        
        # Create a mock history DataFrame with only one entry
        history_data = {'Close': [445.0]}
        mock_history = pd.DataFrame(history_data)
        mock_stock.history.return_value = mock_history
        
        mock_ticker.return_value = mock_stock
        
        # Test the function
        prev_close = self.fetcher.fetch_stock_previous_close('SPY')
        
        # Assertions
        assert prev_close == 445.0  # Only value in the history
        mock_ticker.assert_called_once_with('SPY')
        mock_stock.history.assert_called_once()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_previous_close_empty_history(self, mock_ticker):
        """Test fetching stock previous close with empty history."""
        # Mock yfinance ticker with empty history
        mock_stock = Mock()
        mock_stock.info = {'someOtherField': 'value'}
        
        # Create an empty mock history DataFrame
        mock_history = pd.DataFrame()
        mock_stock.history.return_value = mock_history
        
        mock_ticker.return_value = mock_stock
        
        # Test the function - should raise ValueError
        with pytest.raises(ValueError, match="No historical data available for ticker SPY"):
            self.fetcher.fetch_stock_previous_close('SPY')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_stock_previous_close_api_error(self, mock_ticker):
        """Test fetching stock previous close when API fails."""
        # Mock yfinance ticker to raise an exception
        mock_ticker.side_effect = Exception("API Error")
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch previous closing price for SPY"):
            self.fetcher.fetch_stock_previous_close('SPY')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_vix_previous_close_from_info(self, mock_ticker):
        """Test fetching VIX previous close from info."""
        # Mock yfinance ticker with previousClose in info
        mock_vix = Mock()
        mock_vix.info = {'previousClose': 17.85}
        mock_ticker.return_value = mock_vix
        
        # Test the function
        prev_close = self.fetcher.fetch_vix_previous_close()
        
        # Assertions
        assert prev_close == 17.85
        mock_ticker.assert_called_once_with('^VIX')
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_vix_previous_close_from_history(self, mock_ticker):
        """Test fetching VIX previous close from history."""
        # Mock yfinance ticker with history but no previousClose in info
        mock_vix = Mock()
        mock_vix.info = {'someOtherField': 'value'}
        
        # Create a mock history DataFrame
        history_data = {'Close': [16.0, 17.0, 18.0]}
        mock_history = pd.DataFrame(history_data)
        mock_vix.history.return_value = mock_history
        
        mock_ticker.return_value = mock_vix
        
        # Test the function
        prev_close = self.fetcher.fetch_vix_previous_close()
        
        # Assertions
        assert prev_close == 17.0  # Second-to-last value in the history
        mock_ticker.assert_called_once_with('^VIX')
        mock_vix.history.assert_called_once()
    
    @patch('src.services.market_data_fetcher.yf.Ticker')
    def test_fetch_vix_previous_close_api_error(self, mock_ticker):
        """Test fetching VIX previous close when API fails."""
        # Mock yfinance ticker to raise an exception
        mock_ticker.side_effect = Exception("API Error")
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch previous VIX data"):
            self.fetcher.fetch_vix_previous_close()
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher.fetch_stock_price')
    @patch('src.services.market_data_fetcher.MarketDataFetcher.fetch_stock_previous_close')
    @patch('src.services.market_data_fetcher.MarketDataFetcher.fetch_vix_value')
    @patch('src.services.market_data_fetcher.MarketDataFetcher.fetch_vix_previous_close')
    @patch('src.services.market_data_fetcher.calculate_percentage_change')
    def test_fetch_enhanced_market_data_success(self, mock_calc_pct, mock_vix_prev, mock_vix, mock_stock_prev, mock_stock_price):
        """Test successful fetching of enhanced market data."""
        # Mock return values
        stock_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        vix_timestamp = datetime(2025, 1, 16, 14, 30, 5, tzinfo=timezone.utc)
        
        mock_stock_price.return_value = (450.25, stock_timestamp)
        mock_stock_prev.return_value = 445.75
        mock_vix.return_value = (18.75, vix_timestamp)
        mock_vix_prev.return_value = 17.85
        
        # Mock percentage change calculations
        mock_calc_pct.side_effect = [1.01, 5.04]  # Stock and VIX percentage changes
        
        # Test the function
        enhanced_data = self.fetcher.fetch_enhanced_market_data('SPY')
        
        # Assertions
        assert enhanced_data['stock']['price'] == 450.25
        assert enhanced_data['stock']['previousClose'] == 445.75
        assert enhanced_data['stock']['percentChange'] == 1.01
        assert enhanced_data['stock']['timestamp'] == stock_timestamp
        
        assert enhanced_data['vix']['value'] == 18.75
        assert enhanced_data['vix']['previousClose'] == 17.85
        assert enhanced_data['vix']['percentChange'] == 5.04
        assert enhanced_data['vix']['timestamp'] == vix_timestamp
        
        # Verify all methods were called
        mock_stock_price.assert_called_once_with('SPY')
        mock_stock_prev.assert_called_once_with('SPY')
        mock_vix.assert_called_once()
        mock_vix_prev.assert_called_once()
        assert mock_calc_pct.call_count == 2
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher.fetch_stock_price')
    def test_fetch_enhanced_market_data_error(self, mock_stock_price):
        """Test enhanced market data fetching when an error occurs."""
        # Mock stock price to raise an exception
        mock_stock_price.side_effect = RuntimeError("Failed to fetch stock price")
        
        # Test the function - should raise RuntimeError
        with pytest.raises(RuntimeError, match="Failed to fetch enhanced market data"):
            self.fetcher.fetch_enhanced_market_data('SPY')


class TestConvenienceFunctionsForPreviousClose:
    """Test cases for convenience functions for previous close and enhanced data."""
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher')
    def test_get_stock_previous_close(self, mock_fetcher_class):
        """Test get_stock_previous_close convenience function."""
        # Mock the fetcher instance and method
        mock_fetcher = Mock()
        mock_fetcher.fetch_stock_previous_close.return_value = 445.75
        mock_fetcher_class.return_value = mock_fetcher
        
        # Test the function
        prev_close = get_stock_previous_close('SPY')
        
        # Assertions
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_stock_previous_close.assert_called_once_with('SPY')
        assert prev_close == 445.75
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher')
    def test_get_vix_previous_close(self, mock_fetcher_class):
        """Test get_vix_previous_close convenience function."""
        # Mock the fetcher instance and method
        mock_fetcher = Mock()
        mock_fetcher.fetch_vix_previous_close.return_value = 17.85
        mock_fetcher_class.return_value = mock_fetcher
        
        # Test the function
        prev_close = get_vix_previous_close()
        
        # Assertions
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_vix_previous_close.assert_called_once()
        assert prev_close == 17.85
    
    @patch('src.services.market_data_fetcher.MarketDataFetcher')
    def test_get_enhanced_market_data(self, mock_fetcher_class):
        """Test get_enhanced_market_data convenience function."""
        # Mock the fetcher instance and method
        mock_fetcher = Mock()
        mock_data = {
            'stock': {
                'price': 450.25,
                'previousClose': 445.75,
                'percentChange': 1.01,
                'timestamp': datetime.now(timezone.utc)
            },
            'vix': {
                'value': 18.75,
                'previousClose': 17.85,
                'percentChange': 5.04,
                'timestamp': datetime.now(timezone.utc)
            }
        }
        mock_fetcher.fetch_enhanced_market_data.return_value = mock_data
        mock_fetcher_class.return_value = mock_fetcher
        
        # Test the function
        enhanced_data = get_enhanced_market_data('SPY')
        
        # Assertions
        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_enhanced_market_data.assert_called_once_with('SPY')
        assert enhanced_data == mock_data


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