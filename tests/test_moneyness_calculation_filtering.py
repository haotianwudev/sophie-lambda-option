"""
Tests for moneyness calculation and filtering functionality.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from freezegun import freeze_time
from src.services.data_processor import DataProcessor
from src.models.option_data import OptionData, ExpirationData
from src.utils.calculation_utils import (
    calculate_moneyness,
    is_within_moneyness_range,
    filter_options_by_moneyness
)


class TestMoneynessCalculationFiltering(unittest.TestCase):
    """Test cases for moneyness calculation and filtering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()
        
        # Sample options data
        self.sample_options = [
            OptionData(
                strike=85.0,
                last_price=15.0,
                implied_volatility=0.2,
                delta=0.8,
                option_type='c'
            ),
            OptionData(
                strike=90.0,
                last_price=10.0,
                implied_volatility=0.2,
                delta=0.7,
                option_type='c'
            ),
            OptionData(
                strike=100.0,
                last_price=5.0,
                implied_volatility=0.2,
                delta=0.5,
                option_type='c'
            ),
            OptionData(
                strike=110.0,
                last_price=2.0,
                implied_volatility=0.2,
                delta=0.3,
                option_type='c'
            ),
            OptionData(
                strike=120.0,
                last_price=1.0,
                implied_volatility=0.2,
                delta=0.2,
                option_type='c'
            ),
        ]
        
        # Sample raw options data for data processor
        self.raw_options_data = {
            '2025-08-01': [
                {'strike': 85.0, 'last_price': 15.0, 'option_type': 'c'},
                {'strike': 90.0, 'last_price': 10.0, 'option_type': 'c'},
                {'strike': 100.0, 'last_price': 5.0, 'option_type': 'c'},
                {'strike': 110.0, 'last_price': 2.0, 'option_type': 'c'},
                {'strike': 120.0, 'last_price': 1.0, 'option_type': 'c'},
                {'strike': 85.0, 'last_price': 1.0, 'option_type': 'p'},
                {'strike': 90.0, 'last_price': 2.0, 'option_type': 'p'},
                {'strike': 100.0, 'last_price': 5.0, 'option_type': 'p'},
                {'strike': 110.0, 'last_price': 10.0, 'option_type': 'p'},
                {'strike': 120.0, 'last_price': 15.0, 'option_type': 'p'},
            ]
        }
    
    def test_moneyness_calculation(self):
        """Test moneyness calculation for options."""
        current_price = 100.0
        
        # Test moneyness calculation for different strikes
        self.assertEqual(calculate_moneyness(85.0, current_price), 0.85)
        self.assertEqual(calculate_moneyness(90.0, current_price), 0.9)
        self.assertEqual(calculate_moneyness(100.0, current_price), 1.0)
        self.assertEqual(calculate_moneyness(110.0, current_price), 1.1)
        self.assertEqual(calculate_moneyness(120.0, current_price), 1.2)
        
        # Test with different current price
        current_price = 200.0
        self.assertEqual(calculate_moneyness(100.0, current_price), 0.5)
        self.assertEqual(calculate_moneyness(200.0, current_price), 1.0)
        self.assertEqual(calculate_moneyness(300.0, current_price), 1.5)
    
    def test_is_within_moneyness_range(self):
        """Test checking if moneyness is within range."""
        # Test with default range (0.85 to 1.15)
        self.assertTrue(is_within_moneyness_range(0.85))
        self.assertTrue(is_within_moneyness_range(1.0))
        self.assertTrue(is_within_moneyness_range(1.15))
        
        self.assertFalse(is_within_moneyness_range(0.84))
        self.assertFalse(is_within_moneyness_range(1.16))
        
        # Test with custom range
        self.assertTrue(is_within_moneyness_range(0.9, min_moneyness=0.9, max_moneyness=1.1))
        self.assertTrue(is_within_moneyness_range(1.1, min_moneyness=0.9, max_moneyness=1.1))
        
        self.assertFalse(is_within_moneyness_range(0.89, min_moneyness=0.9, max_moneyness=1.1))
        self.assertFalse(is_within_moneyness_range(1.11, min_moneyness=0.9, max_moneyness=1.1))
    
    def test_filter_options_by_moneyness(self):
        """Test filtering options by moneyness."""
        options = [
            {"strike": 85, "other_field": "value1"},
            {"strike": 90, "other_field": "value2"},
            {"strike": 100, "other_field": "value3"},
            {"strike": 110, "other_field": "value4"},
            {"strike": 120, "other_field": "value5"},
        ]
        
        current_price = 100.0
        
        # Test with default range (0.85 to 1.15)
        filtered = filter_options_by_moneyness(options, current_price)
        
        # Should include strikes 85, 90, 100, 110
        self.assertEqual(len(filtered), 4)
        
        # Check moneyness values were added
        self.assertEqual(filtered[0]["moneyness"], 0.85)
        self.assertEqual(filtered[1]["moneyness"], 0.9)
        self.assertEqual(filtered[2]["moneyness"], 1.0)
        self.assertEqual(filtered[3]["moneyness"], 1.1)
        
        # Test with custom range (0.9 to 1.1)
        filtered = filter_options_by_moneyness(options, current_price, 0.9, 1.1)
        
        # Should include strikes 90, 100, 110
        self.assertEqual(len(filtered), 3)
        
        # Check moneyness values
        self.assertEqual(filtered[0]["moneyness"], 0.9)
        self.assertEqual(filtered[1]["moneyness"], 1.0)
        self.assertEqual(filtered[2]["moneyness"], 1.1)
    
    @patch('src.utils.data_formatter.filter_valid_options')
    @patch('src.services.options_calculator.OptionsCalculator.process_options_with_iv')
    def test_data_processor_moneyness_filtering(self, mock_process_iv, mock_filter_valid):
        """Test moneyness calculation and filtering in data processor."""
        # Create sample options for the test
        calls = [
            OptionData(strike=85.0, last_price=15.0, implied_volatility=0.2, delta=0.8, option_type='c'),
            OptionData(strike=90.0, last_price=10.0, implied_volatility=0.2, delta=0.7, option_type='c'),
            OptionData(strike=100.0, last_price=5.0, implied_volatility=0.2, delta=0.5, option_type='c'),
            OptionData(strike=110.0, last_price=2.0, implied_volatility=0.2, delta=0.3, option_type='c'),
            OptionData(strike=120.0, last_price=1.0, implied_volatility=0.2, delta=0.2, option_type='c'),
        ]
        
        puts = [
            OptionData(strike=85.0, last_price=1.0, implied_volatility=0.2, delta=-0.2, option_type='p'),
            OptionData(strike=90.0, last_price=2.0, implied_volatility=0.2, delta=-0.3, option_type='p'),
            OptionData(strike=100.0, last_price=5.0, implied_volatility=0.2, delta=-0.5, option_type='p'),
            OptionData(strike=110.0, last_price=10.0, implied_volatility=0.2, delta=-0.7, option_type='p'),
            OptionData(strike=120.0, last_price=15.0, implied_volatility=0.2, delta=-0.8, option_type='p'),
        ]
        
        # Set up the mocks
        mock_process_iv.side_effect = lambda options, price, exp: options
        mock_filter_valid.side_effect = lambda options: options
        
        # Patch the _convert_raw_options_to_objects method to return our sample options
        with patch.object(self.processor, '_convert_raw_options_to_objects') as mock_convert:
            mock_convert.side_effect = lambda options: calls if options[0].get('option_type') == 'c' else puts
            
            # Call the method under test with default moneyness range (0.85 to 1.15)
            current_price = 100.0
            expiration_data_list = self.processor.structure_options_by_expiration(
                self.raw_options_data, current_price
            )
            
            # Verify the results
            self.assertEqual(len(expiration_data_list), 1)
            expiration_data = expiration_data_list[0]
            
            # Should include strikes 85, 90, 100, 110 for both calls and puts
            self.assertEqual(len(expiration_data.calls), 4)
            self.assertEqual(len(expiration_data.puts), 4)
            
            # Check moneyness values for calls
            call_strikes = sorted([call.strike for call in expiration_data.calls])
            self.assertEqual(call_strikes, [85.0, 90.0, 100.0, 110.0])
            
            # Check moneyness values for puts
            put_strikes = sorted([put.strike for put in expiration_data.puts])
            self.assertEqual(put_strikes, [85.0, 90.0, 100.0, 110.0])
            
            # Test with custom moneyness range (0.9 to 1.1)
            expiration_data_list = self.processor.structure_options_by_expiration(
                self.raw_options_data, current_price, min_moneyness=0.9, max_moneyness=1.1
            )
            
            # Verify the results
            expiration_data = expiration_data_list[0]
            
            # Should include strikes 90, 100, 110 for both calls and puts
            self.assertEqual(len(expiration_data.calls), 3)
            self.assertEqual(len(expiration_data.puts), 3)
            
            # Check strikes for calls
            call_strikes = sorted([call.strike for call in expiration_data.calls])
            self.assertEqual(call_strikes, [90.0, 100.0, 110.0])
            
            # Check strikes for puts
            put_strikes = sorted([put.strike for put in expiration_data.puts])
            self.assertEqual(put_strikes, [90.0, 100.0, 110.0])
    
    @patch('src.services.data_processor.DataProcessor.structure_options_by_expiration')
    def test_create_market_data_response_with_moneyness(self, mock_structure):
        """Test creating market data response with moneyness filtering."""
        # Create sample expiration data with moneyness
        sample_call = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=0.2,
            delta=0.5,
            option_type='c',
            moneyness=1.0
        )
        
        sample_put = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=0.2,
            delta=-0.5,
            option_type='p',
            moneyness=1.0
        )
        
        sample_expiration = ExpirationData(
            expiration="2025-08-01",
            calls=[sample_call],
            puts=[sample_put]
        )
        
        # Set up the mock for structure_options_by_expiration
        mock_structure.return_value = [sample_expiration]
        
        # Call the method under test
        market_data = self.processor.create_market_data_response(
            ticker="SPY",
            stock_price=100.0,
            vix_value=20.0,
            raw_options_data=self.raw_options_data
        )
        
        # Verify the results
        self.assertEqual(len(market_data.expiration_dates), 1)
        self.assertEqual(len(market_data.expiration_dates[0].calls), 1)
        self.assertEqual(len(market_data.expiration_dates[0].puts), 1)
        
        # Check that moneyness is preserved
        self.assertEqual(market_data.expiration_dates[0].calls[0].moneyness, 1.0)
        self.assertEqual(market_data.expiration_dates[0].puts[0].moneyness, 1.0)


if __name__ == "__main__":
    unittest.main()