"""
Unit tests for additional option data fields.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from src.services.options_data_fetcher import OptionsDataFetcher
from src.models.option_data import OptionData


class TestAdditionalOptionFields:
    """Test cases for additional option data fields."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = OptionsDataFetcher()
    
    def test_option_data_model_has_additional_fields(self):
        """Test that OptionData model has the additional fields."""
        # Create an option data object with all fields
        option = OptionData(
            strike=450.0,
            last_price=2.50,
            implied_volatility=0.2,
            delta=0.65,
            option_type='c',
            contract_symbol='SPY250101C00450000',
            last_trade_date='2025-01-01T12:00:00Z',
            bid=2.45,
            ask=2.55,
            volume=1000,
            open_interest=5000
        )
        
        # Check that all fields are accessible
        assert option.strike == 450.0
        assert option.last_price == 2.50
        assert option.implied_volatility == 0.2
        assert option.delta == 0.65
        assert option.option_type == 'c'
        assert option.contract_symbol == 'SPY250101C00450000'
        assert option.last_trade_date == '2025-01-01T12:00:00Z'
        assert option.bid == 2.45
        assert option.ask == 2.55
        assert option.volume == 1000
        assert option.open_interest == 5000
    
    def test_parse_option_chain_extracts_additional_fields(self):
        """Test that parse_option_chain extracts additional fields from DataFrame."""
        # Create mock DataFrame with all fields
        option_data = {
            'strike': [450.0, 455.0],
            'lastPrice': [2.50, 1.75],
            'contractSymbol': ['SPY250101C00450000', 'SPY250101C00455000'],
            'lastTradeDate': ['2025-01-01T12:00:00Z', '2025-01-01T12:05:00Z'],
            'bid': [2.45, 1.70],
            'ask': [2.55, 1.80],
            'volume': [1000, 800],
            'openInterest': [5000, 4500]
        }
        df = pd.DataFrame(option_data)
        
        # Parse option chain
        result = self.fetcher.parse_option_chain(df, 'c')
        
        # Check that we have the expected number of options
        assert len(result) == 2
        
        # Check that all fields are extracted correctly for the first option
        option = result[0]
        assert option.strike == 450.0
        assert option.last_price == 2.50
        assert option.option_type == 'c'
        assert option.contract_symbol == 'SPY250101C00450000'
        assert option.last_trade_date == '2025-01-01T12:00:00Z'
        assert option.bid == 2.45
        assert option.ask == 2.55
        assert option.volume == 1000
        assert option.open_interest == 5000
        
        # Check the second option as well
        option = result[1]
        assert option.strike == 455.0
        assert option.last_price == 1.75
        assert option.option_type == 'c'
        assert option.contract_symbol == 'SPY250101C00455000'
        assert option.last_trade_date == '2025-01-01T12:05:00Z'
        assert option.bid == 1.70
        assert option.ask == 1.80
        assert option.volume == 800
        assert option.open_interest == 4500
    
    def test_parse_option_chain_handles_missing_fields(self):
        """Test that parse_option_chain handles missing additional fields."""
        # Create mock DataFrame with only required fields
        option_data = {
            'strike': [450.0],
            'lastPrice': [2.50]
        }
        df = pd.DataFrame(option_data)
        
        # Parse option chain
        result = self.fetcher.parse_option_chain(df, 'c')
        
        # Check that we have one option
        assert len(result) == 1
        
        # Check that required fields are present and additional fields are None
        option = result[0]
        assert option.strike == 450.0
        assert option.last_price == 2.50
        assert option.option_type == 'c'
        assert option.contract_symbol is None
        assert option.last_trade_date is None
        assert option.bid is None
        assert option.ask is None
        assert option.volume is None
        assert option.open_interest is None
    
    def test_parse_option_chain_handles_invalid_additional_fields(self):
        """Test that parse_option_chain handles invalid additional fields."""
        # Create mock DataFrame with invalid additional fields
        option_data = {
            'strike': [450.0],
            'lastPrice': [2.50],
            'contractSymbol': [None],
            'lastTradeDate': ['invalid_date'],
            'bid': ['not_a_number'],
            'ask': [None],
            'volume': ['not_a_number'],
            'openInterest': [None]
        }
        df = pd.DataFrame(option_data)
        
        # Parse option chain
        result = self.fetcher.parse_option_chain(df, 'c')
        
        # Check that we have one option
        assert len(result) == 1
        
        # Check that required fields are present and invalid additional fields are handled
        option = result[0]
        assert option.strike == 450.0
        assert option.last_price == 2.50
        assert option.option_type == 'c'
        assert option.contract_symbol is None  # None should remain None
        assert option.last_trade_date == 'invalid_date'  # String should be preserved
        assert option.bid is None  # Invalid number should be None
        assert option.ask is None  # None should remain None
        assert option.volume is None  # Invalid number should be None
        assert option.open_interest is None  # None should remain None
    
    @patch('src.services.options_data_fetcher.yf.Ticker')
    def test_fetch_option_chain_for_expiration_includes_additional_fields(self, mock_ticker_class):
        """Test that fetch_option_chain_for_expiration includes additional fields."""
        # Create mock option chain data with additional fields
        calls_data = pd.DataFrame({
            'strike': [450.0],
            'lastPrice': [2.50],
            'contractSymbol': ['SPY250101C00450000'],
            'lastTradeDate': ['2025-01-01T12:00:00Z'],
            'bid': [2.45],
            'ask': [2.55],
            'volume': [1000],
            'openInterest': [5000]
        })
        puts_data = pd.DataFrame({
            'strike': [450.0],
            'lastPrice': [1.25],
            'contractSymbol': ['SPY250101P00450000'],
            'lastTradeDate': ['2025-01-01T12:00:00Z'],
            'bid': [1.20],
            'ask': [1.30],
            'volume': [800],
            'openInterest': [4000]
        })
        
        # Mock option chain object
        mock_option_chain = Mock()
        mock_option_chain.calls = calls_data
        mock_option_chain.puts = puts_data
        
        # Mock yfinance Ticker
        mock_ticker = Mock()
        mock_ticker.option_chain.return_value = mock_option_chain
        mock_ticker_class.return_value = mock_ticker
        
        # Test fetching option chain
        result = self.fetcher.fetch_option_chain_for_expiration("SPY", "2025-01-01")
        
        # Check that we have the expected structure
        assert result.expiration == "2025-01-01"
        assert len(result.calls) == 1
        assert len(result.puts) == 1
        
        # Check call option fields
        call = result.calls[0]
        assert call.strike == 450.0
        assert call.last_price == 2.50
        assert call.option_type == 'c'
        assert call.contract_symbol == 'SPY250101C00450000'
        assert call.last_trade_date == '2025-01-01T12:00:00Z'
        assert call.bid == 2.45
        assert call.ask == 2.55
        assert call.volume == 1000
        assert call.open_interest == 5000
        
        # Check put option fields
        put = result.puts[0]
        assert put.strike == 450.0
        assert put.last_price == 1.25
        assert put.option_type == 'p'
        assert put.contract_symbol == 'SPY250101P00450000'
        assert put.last_trade_date == '2025-01-01T12:00:00Z'
        assert put.bid == 1.20
        assert put.ask == 1.30
        assert put.volume == 800
        assert put.open_interest == 4000


if __name__ == "__main__":
    pytest.main([__file__])