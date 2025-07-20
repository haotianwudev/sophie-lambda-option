"""
Tests for filtered options data fetcher functionality.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from freezegun import freeze_time
from src.services.options_data_fetcher import OptionsDataFetcher
from src.models.option_data import OptionData, ExpirationData


class TestOptionsDataFetcherFiltered(unittest.TestCase):
    """Test cases for filtered options data fetcher."""
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    @patch('src.services.options_data_fetcher.OptionsDataFetcher.fetch_all_option_chains')
    def test_fetch_filtered_option_chains(self, mock_fetch_all):
        """Test fetching filtered option chains."""
        # Create sample option data
        sample_option = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=0.2,
            delta=0.5,
            option_type='c'
        )
        
        # Create sample expiration data objects
        mock_expirations = [
            ExpirationData(expiration="2025-07-25", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-08-01", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-08-15", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-09-05", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-09-19", calls=[sample_option], puts=[sample_option])
        ]
        
        # Set up the mock to return our sample data
        mock_fetch_all.return_value = mock_expirations
        
        # Call the method under test
        fetcher = OptionsDataFetcher()
        filtered_chains = fetcher.fetch_filtered_option_chains("SPY")
        
        # Verify the results
        self.assertEqual(len(filtered_chains), 4)  # Should have 4 target periods
        
        # Check that each expiration has the correct label and days
        expected_labels = {
            "2025-08-01": "2w",
            "2025-08-15": "1m",
            "2025-09-05": "6w",
            "2025-09-19": "2m"
        }
        
        for exp_data in filtered_chains:
            self.assertIn(exp_data.expiration, expected_labels)
            self.assertEqual(exp_data.expiration_label, expected_labels[exp_data.expiration])
            self.assertIsNotNone(exp_data.days_to_expiration)
    
    @patch('src.services.options_data_fetcher.OptionsDataFetcher.fetch_all_option_chains')
    def test_fetch_filtered_option_chains_empty(self, mock_fetch_all):
        """Test fetching filtered option chains with empty result."""
        # Set up the mock to return empty list
        mock_fetch_all.return_value = []
        
        # Call the method under test
        fetcher = OptionsDataFetcher()
        
        # Should raise RuntimeError
        with self.assertRaises(RuntimeError):
            fetcher.fetch_filtered_option_chains("SPY")
    
    @patch('src.services.options_data_fetcher.OptionsDataFetcher.fetch_all_option_chains')
    def test_fetch_filtered_option_chains_error(self, mock_fetch_all):
        """Test fetching filtered option chains with error."""
        # Set up the mock to raise an exception
        mock_fetch_all.side_effect = RuntimeError("Test error")
        
        # Call the method under test
        fetcher = OptionsDataFetcher()
        
        # Should raise RuntimeError
        with self.assertRaises(RuntimeError):
            fetcher.fetch_filtered_option_chains("SPY")


if __name__ == "__main__":
    unittest.main()