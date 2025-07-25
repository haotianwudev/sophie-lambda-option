"""
Unit tests for data formatting utilities.
"""
import pytest
from datetime import datetime, timezone
from src.models.option_data import (
    OptionData, 
    ExpirationData, 
    MarketData, 
    StockData, 
    VixData
)
from src.utils.data_formatter import (
    format_option_for_response,
    format_expiration_for_response,
    format_stock_data_for_response,
    format_vix_data_for_response,
    format_market_data_for_response,
    validate_ticker_symbol,
    filter_valid_options
)


class TestDataFormatter:
    """Test cases for data formatting functions."""
    
    def test_format_option_for_response(self):
        """Test formatting OptionData for API response."""
        option = OptionData(
            strike=450.0,
            last_price=2.5678,
            implied_volatility=0.18567,
            delta=0.52345,
            option_type='c'
        )
        
        formatted = format_option_for_response(option)
        
        expected = {
            "strike": 450.0,
            "lastPrice": 2.57,
            "impliedVolatility": 0.1857,
            "delta": 0.5234
        }
        
        assert formatted == expected
    
    def test_format_option_for_response_with_none_values(self):
        """Test formatting OptionData with None values."""
        option = OptionData(
            strike=450.0,
            last_price=None,
            implied_volatility=None,
            delta=None,
            option_type='p'
        )
        
        formatted = format_option_for_response(option)
        
        expected = {
            "strike": 450.0,
            "lastPrice": None,
            "impliedVolatility": None,
            "delta": None
        }
        
        assert formatted == expected
    
    def test_format_expiration_for_response(self):
        """Test formatting ExpirationData for API response."""
        call = OptionData(450.0, 2.50, 0.185, 0.52, 'c')
        put = OptionData(450.0, 1.75, 0.190, -0.48, 'p')
        
        expiration = ExpirationData(
            expiration="2025-01-17",
            calls=[call],
            puts=[put]
        )
        
        formatted = format_expiration_for_response(expiration)
        
        assert formatted["expiration"] == "2025-01-17"
        assert len(formatted["calls"]) == 1
        assert len(formatted["puts"]) == 1
        assert formatted["calls"][0]["strike"] == 450.0
        assert formatted["puts"][0]["delta"] == -0.48
    
    def test_format_stock_data_for_response(self):
        """Test formatting StockData for API response."""
        timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        stock_data = StockData(
            price=450.25,
            previous_close=445.75,
            percent_change=1.01,
            timestamp=timestamp
        )
        
        formatted = format_stock_data_for_response(stock_data)
        
        expected = {
            "price": 450.25,
            "previousClose": 445.75,
            "percentChange": 1.01,
            "timestamp": "2025-01-16T14:30:00Z"
        }
        
        assert formatted == expected
    
    def test_format_vix_data_for_response(self):
        """Test formatting VixData for API response."""
        timestamp = datetime(2025, 1, 16, 14, 30, 5, tzinfo=timezone.utc)
        vix_data = VixData(
            value=18.75,
            previous_close=17.85,
            percent_change=5.04,
            timestamp=timestamp
        )
        
        formatted = format_vix_data_for_response(vix_data)
        
        expected = {
            "value": 18.75,
            "previousClose": 17.85,
            "percentChange": 5.04,
            "timestamp": "2025-01-16T14:30:05Z"
        }
        
        assert formatted == expected
    
    def test_format_market_data_for_response(self):
        """Test formatting complete MarketData for API response."""
        stock_timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        vix_timestamp = datetime(2025, 1, 16, 14, 30, 5, tzinfo=timezone.utc)
        call = OptionData(450.0, 2.50, 0.185, 0.52, 'c')
        expiration = ExpirationData("2025-01-17", [call], [])
        
        stock_data = StockData(
            price=450.25,
            previous_close=445.75,
            percent_change=1.01,
            timestamp=stock_timestamp
        )
        
        vix_data = VixData(
            value=18.75,
            previous_close=17.85,
            percent_change=5.04,
            timestamp=vix_timestamp
        )
        
        market_data = MarketData(
            ticker="spy",  # lowercase to test uppercase conversion
            stock=stock_data,
            vix=vix_data,
            expiration_dates=[expiration]
        )
        
        formatted = format_market_data_for_response(market_data)
        
        assert formatted["ticker"] == "SPY"
        assert formatted["stock"]["price"] == 450.25
        assert formatted["stock"]["previousClose"] == 445.75
        assert formatted["stock"]["percentChange"] == 1.01
        assert formatted["stock"]["timestamp"] == "2025-01-16T14:30:00Z"
        assert formatted["vix"]["value"] == 18.75
        assert formatted["vix"]["previousClose"] == 17.85
        assert formatted["vix"]["percentChange"] == 5.04
        assert formatted["vix"]["timestamp"] == "2025-01-16T14:30:05Z"
        assert len(formatted["expirationDates"]) == 1
    
    def test_validate_ticker_symbol_valid(self):
        """Test validating valid ticker symbols."""
        assert validate_ticker_symbol("SPY") == "SPY"
        assert validate_ticker_symbol("spy") == "SPY"
        assert validate_ticker_symbol("  AAPL  ") == "AAPL"
        assert validate_ticker_symbol("BRK.B") == "BRK.B"
        assert validate_ticker_symbol("BRK-B") == "BRK-B"
    
    def test_validate_ticker_symbol_invalid(self):
        """Test validating invalid ticker symbols."""
        with pytest.raises(ValueError, match="Ticker must be a non-empty string"):
            validate_ticker_symbol("")
        
        with pytest.raises(ValueError, match="Ticker must be a non-empty string"):
            validate_ticker_symbol(None)
        
        with pytest.raises(ValueError, match="Invalid ticker symbol"):
            validate_ticker_symbol("SPY@")
        
        with pytest.raises(ValueError, match="Invalid ticker symbol"):
            validate_ticker_symbol("SP Y")
    
    def test_filter_valid_options(self):
        """Test filtering valid options."""
        options = [
            # Valid option
            OptionData(450.0, 2.50, 0.185, 0.52, 'c'),
            # Invalid strike
            OptionData(0.0, 2.50, 0.185, 0.52, 'c'),
            # Invalid last price
            OptionData(450.0, None, 0.185, 0.52, 'c'),
            # Both IV and delta failed
            OptionData(450.0, 2.50, None, None, 'c'),
            # Valid option with only IV
            OptionData(455.0, 3.00, 0.190, None, 'c'),
            # Valid option with only delta
            OptionData(460.0, 3.50, None, 0.45, 'c'),
        ]
        
        valid_options = filter_valid_options(options)
        
        assert len(valid_options) == 3
        assert valid_options[0].strike == 450.0
        assert valid_options[1].strike == 455.0
        assert valid_options[2].strike == 460.0
    
    def test_filter_valid_options_empty_list(self):
        """Test filtering empty options list."""
        valid_options = filter_valid_options([])
        assert len(valid_options) == 0
    
    def test_filter_valid_options_all_invalid(self):
        """Test filtering when all options are invalid."""
        options = [
            OptionData(0.0, 2.50, 0.185, 0.52, 'c'),  # Invalid strike
            OptionData(450.0, None, None, None, 'c'),  # Invalid price and calculations
        ]
        
        valid_options = filter_valid_options(options)
        assert len(valid_options) == 0