"""
Tests for data processor with filtered expirations.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from freezegun import freeze_time
from src.services.data_processor import DataProcessor
from src.models.option_data import OptionData, ExpirationData, MarketData


class TestDataProcessorFilteredExpirations(unittest.TestCase):
    """Test cases for data processor with filtered expirations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()
        
        # Sample option data
        self.sample_option = {
            'strike': 100.0,
            'last_price': 5.0,
            'option_type': 'c'
        }
        
        # Sample raw options data
        self.raw_options_data = {
            '2025-07-25': [self.sample_option],
            '2025-08-01': [self.sample_option],
            '2025-08-15': [self.sample_option],
            '2025-09-05': [self.sample_option],
            '2025-09-19': [self.sample_option]
        }
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    @patch('src.services.options_calculator.OptionsCalculator.process_options_with_iv')
    @patch('src.utils.expiration_selector.filter_expirations_by_target_periods')
    def test_create_market_data_response_with_filtering(self, mock_filter, mock_process_iv):
        """Test creating market data response with expiration filtering."""
        # Set up the mock for process_options_with_iv to return the input options
        mock_process_iv.side_effect = lambda options, price, exp: options
        
        # Create sample expiration data objects for the filter mock
        sample_option_obj = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=0.2,
            delta=0.5,
            option_type='c'
        )
        
        # Expected filtered expirations
        filtered_expirations = [
            ExpirationData(
                expiration="2025-08-01",
                calls=[sample_option_obj],
                puts=[],
                days_to_expiration=14,
                expiration_label="2w"
            ),
            ExpirationData(
                expiration="2025-08-15",
                calls=[sample_option_obj],
                puts=[],
                days_to_expiration=28,
                expiration_label="1m"
            ),
            ExpirationData(
                expiration="2025-09-05",
                calls=[sample_option_obj],
                puts=[],
                days_to_expiration=49,
                expiration_label="6w"
            ),
            ExpirationData(
                expiration="2025-09-19",
                calls=[sample_option_obj],
                puts=[],
                days_to_expiration=63,
                expiration_label="2m"
            )
        ]
        
        # Set up the mock for filter_expirations_by_target_periods
        mock_filter.return_value = filtered_expirations
        
        # Call the method under test
        market_data = self.processor.create_market_data_response(
            ticker="SPY",
            stock_price=100.0,
            vix_value=20.0,
            raw_options_data=self.raw_options_data,
            filter_expirations=True
        )
        
        # Verify the results
        self.assertEqual(len(market_data.expiration_dates), 4)
        self.assertTrue(mock_filter.called)
        
        # Check that the filtered expirations are used
        self.assertEqual(market_data.expiration_dates, filtered_expirations)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    @patch('src.services.options_calculator.OptionsCalculator.process_options_with_iv')
    def test_create_market_data_response_without_filtering(self, mock_process_iv):
        """Test creating market data response without expiration filtering."""
        # Set up the mock for process_options_with_iv to return the input options
        mock_process_iv.side_effect = lambda options, price, exp: options
        
        # Call the method under test
        market_data = self.processor.create_market_data_response(
            ticker="SPY",
            stock_price=100.0,
            vix_value=20.0,
            raw_options_data=self.raw_options_data,
            filter_expirations=False
        )
        
        # Verify the results
        self.assertEqual(len(market_data.expiration_dates), 5)  # All 5 expirations should be included
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    @patch('src.services.options_calculator.OptionsCalculator.process_options_with_iv')
    @patch('src.utils.expiration_selector.filter_expirations_by_target_periods')
    def test_create_market_data_response_filter_error(self, mock_filter, mock_process_iv):
        """Test creating market data response when filtering raises an error."""
        # Set up the mock for process_options_with_iv to return the input options
        mock_process_iv.side_effect = lambda options, price, exp: options
        
        # Set up the mock for filter_expirations_by_target_periods to raise an exception
        mock_filter.side_effect = ValueError("Test error")
        
        # Call the method under test
        market_data = self.processor.create_market_data_response(
            ticker="SPY",
            stock_price=100.0,
            vix_value=20.0,
            raw_options_data=self.raw_options_data,
            filter_expirations=True
        )
        
        # Verify the results - should fall back to all expirations
        self.assertEqual(len(market_data.expiration_dates), 5)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    @patch('src.services.data_processor.DataProcessor.create_market_data_response')
    def test_format_api_response_with_filtering(self, mock_create):
        """Test formatting API response with expiration filtering."""
        # Create a mock MarketData object
        mock_market_data = MagicMock()
        mock_market_data.ticker = "SPY"
        mock_market_data.expiration_dates = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        
        # Set up the mock for create_market_data_response
        mock_create.return_value = mock_market_data
        
        # Call the method under test
        self.processor.format_api_response(
            ticker="SPY",
            stock_price=100.0,
            vix_value=20.0,
            raw_options_data=self.raw_options_data,
            filter_expirations=True
        )
        
        # Verify that create_market_data_response was called with filter_expirations=True
        mock_create.assert_called_once()
        self.assertTrue(mock_create.call_args[1]['filter_expirations'])
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    @patch('src.services.data_processor.DataProcessor.create_market_data_response')
    def test_format_api_response_without_filtering(self, mock_create):
        """Test formatting API response without expiration filtering."""
        # Create a mock MarketData object
        mock_market_data = MagicMock()
        mock_market_data.ticker = "SPY"
        mock_market_data.expiration_dates = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        
        # Set up the mock for create_market_data_response
        mock_create.return_value = mock_market_data
        
        # Call the method under test
        self.processor.format_api_response(
            ticker="SPY",
            stock_price=100.0,
            vix_value=20.0,
            raw_options_data=self.raw_options_data,
            filter_expirations=False
        )
        
        # Verify that create_market_data_response was called with filter_expirations=False
        mock_create.assert_called_once()
        self.assertFalse(mock_create.call_args[1]['filter_expirations'])


if __name__ == "__main__":
    unittest.main()