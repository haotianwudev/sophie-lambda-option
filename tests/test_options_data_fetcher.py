"""
Unit tests for options data fetcher service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from src.services.options_data_fetcher import (
    OptionsDataFetcher,
    get_option_expiration_dates,
    get_option_chain_for_expiration,
    get_all_option_chains
)
from src.models.option_data import OptionData, ExpirationData


class TestOptionsDataFetcher:
    """Test cases for OptionsDataFetcher class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = OptionsDataFetcher()
    
    def test_validate_ticker_valid_cases(self):
        """Test ticker validation with valid inputs."""
        # Test basic ticker
        assert self.fetcher.validate_ticker("SPY") == "SPY"
        
        # Test lowercase conversion
        assert self.fetcher.validate_ticker("spy") == "SPY"
        
        # Test with whitespace
        assert self.fetcher.validate_ticker("  AAPL  ") == "AAPL"
        
        # Test with dots and hyphens
        assert self.fetcher.validate_ticker("BRK.A") == "BRK.A"
        assert self.fetcher.validate_ticker("BRK-A") == "BRK-A"
    
    def test_validate_ticker_invalid_cases(self):
        """Test ticker validation with invalid inputs."""
        # Test empty string
        with pytest.raises(ValueError, match="Ticker must be a non-empty string"):
            self.fetcher.validate_ticker("")
        
        # Test None
        with pytest.raises(ValueError, match="Ticker must be a non-empty string"):
            self.fetcher.validate_ticker(None)
        
        # Test non-string
        with pytest.raises(ValueError, match="Ticker must be a non-empty string"):
            self.fetcher.validate_ticker(123)
        
        # Test whitespace only
        with pytest.raises(ValueError, match="Ticker cannot be empty after formatting"):
            self.fetcher.validate_ticker("   ")
        
        # Test invalid characters
        with pytest.raises(ValueError, match="Invalid ticker format"):
            self.fetcher.validate_ticker("SPY@#$")
    
    @patch('src.services.options_data_fetcher.yf.Ticker')
    def test_fetch_option_expiration_dates_success(self, mock_ticker_class):
        """Test successful fetching of option expiration dates."""
        # Mock yfinance Ticker
        mock_ticker = Mock()
        mock_ticker.options = ['2025-01-17', '2025-01-24', '2025-02-21']
        mock_ticker_class.return_value = mock_ticker
        
        # Test fetching expiration dates
        result = self.fetcher.fetch_option_expiration_dates("SPY")
        
        assert result == ['2025-01-17', '2025-01-24', '2025-02-21']
        mock_ticker_class.assert_called_once_with("SPY")
    
    @patch('src.services.options_data_fetcher.yf.Ticker')
    def test_fetch_option_expiration_dates_no_options(self, mock_ticker_class):
        """Test fetching expiration dates when no options are available."""
        # Mock yfinance Ticker with no options
        mock_ticker = Mock()
        mock_ticker.options = []
        mock_ticker_class.return_value = mock_ticker
        
        # Test that RuntimeError is raised
        with pytest.raises(RuntimeError, match="No option expiration dates found"):
            self.fetcher.fetch_option_expiration_dates("INVALID")
    
    @patch('src.services.options_data_fetcher.yf.Ticker')
    def test_fetch_option_expiration_dates_api_error(self, mock_ticker_class):
        """Test fetching expiration dates when API fails."""
        # Mock yfinance Ticker to raise exception
        mock_ticker_class.side_effect = Exception("API Error")
        
        # Test that RuntimeError is raised
        with pytest.raises(RuntimeError, match="Failed to fetch expiration dates"):
            self.fetcher.fetch_option_expiration_dates("SPY")
    
    def test_parse_option_chain_valid_data(self):
        """Test parsing option chain with valid data."""
        # Create mock DataFrame
        option_data = {
            'strike': [450.0, 455.0, 460.0],
            'lastPrice': [2.50, 1.75, 1.25]
        }
        df = pd.DataFrame(option_data)
        
        # Parse option chain
        result = self.fetcher.parse_option_chain(df, 'c')
        
        assert len(result) == 3
        assert all(isinstance(option, OptionData) for option in result)
        assert result[0].strike == 450.0
        assert result[0].last_price == 2.50
        assert result[0].option_type == 'c'
        assert result[0].implied_volatility is None
        assert result[0].delta is None
    
    def test_parse_option_chain_empty_data(self):
        """Test parsing empty option chain."""
        df = pd.DataFrame()
        
        result = self.fetcher.parse_option_chain(df, 'c')
        
        assert result == []
    
    def test_parse_option_chain_invalid_data(self):
        """Test parsing option chain with invalid data."""
        # Create DataFrame with invalid data
        option_data = {
            'strike': [450.0, 0, -100.0, 455.0],
            'lastPrice': [2.50, 1.75, 0, -1.0]
        }
        df = pd.DataFrame(option_data)
        
        # Parse option chain - should skip invalid entries
        result = self.fetcher.parse_option_chain(df, 'c')
        
        # Only the first entry should be valid
        assert len(result) == 1
        assert result[0].strike == 450.0
        assert result[0].last_price == 2.50
    
    @patch('src.services.options_data_fetcher.yf.Ticker')
    def test_fetch_option_chain_for_expiration_success(self, mock_ticker_class):
        """Test successful fetching of option chain for specific expiration."""
        # Create mock option chain data
        calls_data = pd.DataFrame({
            'strike': [450.0, 455.0],
            'lastPrice': [2.50, 1.75]
        })
        puts_data = pd.DataFrame({
            'strike': [450.0, 455.0],
            'lastPrice': [1.25, 2.00]
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
        result = self.fetcher.fetch_option_chain_for_expiration("SPY", "2025-01-17")
        
        assert isinstance(result, ExpirationData)
        assert result.expiration == "2025-01-17"
        assert len(result.calls) == 2
        assert len(result.puts) == 2
        assert result.calls[0].option_type == 'c'
        assert result.puts[0].option_type == 'p'
        
        mock_ticker_class.assert_called_once_with("SPY")
        mock_ticker.option_chain.assert_called_once_with("2025-01-17")
    
    @patch('src.services.options_data_fetcher.yf.Ticker')
    def test_fetch_option_chain_for_expiration_api_error(self, mock_ticker_class):
        """Test fetching option chain when API fails."""
        # Mock yfinance Ticker to raise exception
        mock_ticker = Mock()
        mock_ticker.option_chain.side_effect = Exception("API Error")
        mock_ticker_class.return_value = mock_ticker
        
        # Test that RuntimeError is raised
        with pytest.raises(RuntimeError, match="Failed to fetch option chain"):
            self.fetcher.fetch_option_chain_for_expiration("SPY", "2025-01-17")
    
    @patch.object(OptionsDataFetcher, 'fetch_option_expiration_dates')
    @patch.object(OptionsDataFetcher, 'fetch_option_chain_for_expiration')
    def test_fetch_all_option_chains_success(self, mock_fetch_chain, mock_fetch_dates):
        """Test successful fetching of all option chains."""
        # Mock expiration dates
        mock_fetch_dates.return_value = ['2025-01-17', '2025-01-24']
        
        # Mock option chain data
        expiration_data_1 = ExpirationData(
            expiration='2025-01-17',
            calls=[OptionData(450.0, 2.50, None, None, 'c')],
            puts=[OptionData(450.0, 1.25, None, None, 'p')]
        )
        expiration_data_2 = ExpirationData(
            expiration='2025-01-24',
            calls=[OptionData(455.0, 1.75, None, None, 'c')],
            puts=[OptionData(455.0, 2.00, None, None, 'p')]
        )
        
        mock_fetch_chain.side_effect = [expiration_data_1, expiration_data_2]
        
        # Test fetching all option chains
        result = self.fetcher.fetch_all_option_chains("SPY")
        
        assert len(result) == 2
        assert all(isinstance(exp_data, ExpirationData) for exp_data in result)
        assert result[0].expiration == '2025-01-17'
        assert result[1].expiration == '2025-01-24'
        
        mock_fetch_dates.assert_called_once_with("SPY")
        assert mock_fetch_chain.call_count == 2
    
    @patch.object(OptionsDataFetcher, 'fetch_option_expiration_dates')
    @patch.object(OptionsDataFetcher, 'fetch_option_chain_for_expiration')
    def test_fetch_all_option_chains_partial_failure(self, mock_fetch_chain, mock_fetch_dates):
        """Test fetching all option chains with some failures."""
        # Mock expiration dates
        mock_fetch_dates.return_value = ['2025-01-17', '2025-01-24', '2025-02-21']
        
        # Mock option chain data - second call fails
        expiration_data_1 = ExpirationData(
            expiration='2025-01-17',
            calls=[OptionData(450.0, 2.50, None, None, 'c')],
            puts=[OptionData(450.0, 1.25, None, None, 'p')]
        )
        expiration_data_3 = ExpirationData(
            expiration='2025-02-21',
            calls=[OptionData(460.0, 1.00, None, None, 'c')],
            puts=[OptionData(460.0, 2.50, None, None, 'p')]
        )
        
        mock_fetch_chain.side_effect = [
            expiration_data_1,
            RuntimeError("API Error"),
            expiration_data_3
        ]
        
        # Test fetching all option chains - should skip failed expiration
        result = self.fetcher.fetch_all_option_chains("SPY")
        
        assert len(result) == 2
        assert result[0].expiration == '2025-01-17'
        assert result[1].expiration == '2025-02-21'
    
    @patch.object(OptionsDataFetcher, 'fetch_option_expiration_dates')
    @patch.object(OptionsDataFetcher, 'fetch_option_chain_for_expiration')
    def test_fetch_all_option_chains_no_valid_chains(self, mock_fetch_chain, mock_fetch_dates):
        """Test fetching all option chains when no valid chains are found."""
        # Mock expiration dates with some dates but empty option chains
        mock_fetch_dates.return_value = ['2025-01-17', '2025-01-24']
        
        # Mock empty option chain data
        empty_expiration_data = ExpirationData(
            expiration='2025-01-17',
            calls=[],
            puts=[]
        )
        
        mock_fetch_chain.return_value = empty_expiration_data
        
        # Test that RuntimeError is raised when no valid chains found
        with pytest.raises(RuntimeError, match="No valid option chains found"):
            self.fetcher.fetch_all_option_chains("INVALID")


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @patch.object(OptionsDataFetcher, 'fetch_option_expiration_dates')
    def test_get_option_expiration_dates(self, mock_method):
        """Test convenience function for getting expiration dates."""
        mock_method.return_value = ['2025-01-17', '2025-01-24']
        
        result = get_option_expiration_dates("SPY")
        
        assert result == ['2025-01-17', '2025-01-24']
        mock_method.assert_called_once_with("SPY")
    
    @patch.object(OptionsDataFetcher, 'fetch_option_chain_for_expiration')
    def test_get_option_chain_for_expiration(self, mock_method):
        """Test convenience function for getting option chain for expiration."""
        expected_data = ExpirationData(
            expiration='2025-01-17',
            calls=[OptionData(450.0, 2.50, None, None, 'c')],
            puts=[OptionData(450.0, 1.25, None, None, 'p')]
        )
        mock_method.return_value = expected_data
        
        result = get_option_chain_for_expiration("SPY", "2025-01-17")
        
        assert result == expected_data
        mock_method.assert_called_once_with("SPY", "2025-01-17")
    
    @patch.object(OptionsDataFetcher, 'fetch_all_option_chains')
    def test_get_all_option_chains(self, mock_method):
        """Test convenience function for getting all option chains."""
        expected_data = [
            ExpirationData(
                expiration='2025-01-17',
                calls=[OptionData(450.0, 2.50, None, None, 'c')],
                puts=[OptionData(450.0, 1.25, None, None, 'p')]
            )
        ]
        mock_method.return_value = expected_data
        
        result = get_all_option_chains("SPY")
        
        assert result == expected_data
        mock_method.assert_called_once_with("SPY")


if __name__ == "__main__":
    pytest.main([__file__])