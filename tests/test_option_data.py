"""
Unit tests for option data models.
"""
import pytest
from datetime import datetime, timezone
from src.models.option_data import OptionData, ExpirationData, MarketData


class TestOptionData:
    """Test cases for OptionData model."""
    
    def test_option_data_creation(self):
        """Test creating OptionData instance."""
        option = OptionData(
            strike=450.0,
            last_price=2.50,
            implied_volatility=0.185,
            delta=0.52,
            option_type='c'
        )
        
        assert option.strike == 450.0
        assert option.last_price == 2.50
        assert option.implied_volatility == 0.185
        assert option.delta == 0.52
        assert option.option_type == 'c'
    
    def test_option_data_with_none_values(self):
        """Test OptionData with None values for optional fields."""
        option = OptionData(
            strike=450.0,
            last_price=2.50,
            implied_volatility=None,
            delta=None,
            option_type='p'
        )
        
        assert option.strike == 450.0
        assert option.last_price == 2.50
        assert option.implied_volatility is None
        assert option.delta is None
        assert option.option_type == 'p'


class TestExpirationData:
    """Test cases for ExpirationData model."""
    
    def test_expiration_data_creation(self):
        """Test creating ExpirationData instance."""
        call_option = OptionData(450.0, 2.50, 0.185, 0.52, 'c')
        put_option = OptionData(450.0, 1.75, 0.190, -0.48, 'p')
        
        expiration = ExpirationData(
            expiration="2025-01-17",
            calls=[call_option],
            puts=[put_option]
        )
        
        assert expiration.expiration == "2025-01-17"
        assert len(expiration.calls) == 1
        assert len(expiration.puts) == 1
        assert expiration.calls[0] == call_option
        assert expiration.puts[0] == put_option
    
    def test_expiration_data_empty_lists(self):
        """Test ExpirationData with empty option lists."""
        expiration = ExpirationData(
            expiration="2025-01-17",
            calls=[],
            puts=[]
        )
        
        assert expiration.expiration == "2025-01-17"
        assert len(expiration.calls) == 0
        assert len(expiration.puts) == 0


class TestMarketData:
    """Test cases for MarketData model."""
    
    def test_market_data_creation(self):
        """Test creating MarketData instance."""
        timestamp = datetime.now(timezone.utc)
        call_option = OptionData(450.0, 2.50, 0.185, 0.52, 'c')
        expiration = ExpirationData("2025-01-17", [call_option], [])
        
        market_data = MarketData(
            ticker="SPY",
            stock_price=450.25,
            vix_value=18.75,
            data_timestamp=timestamp,
            vix_timestamp=timestamp,
            expiration_dates=[expiration]
        )
        
        assert market_data.ticker == "SPY"
        assert market_data.stock_price == 450.25
        assert market_data.vix_value == 18.75
        assert market_data.data_timestamp == timestamp
        assert market_data.vix_timestamp == timestamp
        assert len(market_data.expiration_dates) == 1
        assert market_data.expiration_dates[0] == expiration