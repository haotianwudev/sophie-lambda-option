"""
Tests for enhanced implied volatility calculations.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.models.option_data import OptionData
from src.services.options_calculator import OptionsCalculator
from src.utils.calculation_utils import calculate_implied_volatilities


class TestEnhancedIVCalculations(unittest.TestCase):
    """Test cases for enhanced implied volatility calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = OptionsCalculator(risk_free_rate=0.03)
    
    def test_option_data_model_has_new_fields(self):
        """Test that OptionData model has the new IV fields."""
        option = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=0.2,
            delta=0.5,
            option_type='c',
            bid=4.8,
            ask=5.2,
            mid_price=5.0,
            implied_volatility_bid=0.19,
            implied_volatility_mid=0.2,
            implied_volatility_ask=0.21
        )
        
        # Check that the new fields exist and have the correct values
        self.assertEqual(option.mid_price, 5.0)
        self.assertEqual(option.implied_volatility_bid, 0.19)
        self.assertEqual(option.implied_volatility_mid, 0.2)
        self.assertEqual(option.implied_volatility_ask, 0.21)
    
    @patch('py_vollib.black_scholes.implied_volatility.implied_volatility')
    def test_calculate_implied_volatilities_with_valid_inputs(self, mock_iv):
        """Test calculating implied volatilities with valid inputs."""
        # Mock the implied_volatility function to return predictable values
        mock_iv.side_effect = [0.19, 0.2, 0.21]
        
        option = {
            "strike": 100.0,
            "bid": 4.8,
            "ask": 5.2,
            "impliedVolatility": 0.2
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100.0,
            time_to_expiration=0.1,
            risk_free_rate=0.03,
            option_type='c'
        )
        
        # Check that all IV fields are present with the expected values
        self.assertEqual(ivs["impliedVolatilityYF"], 0.2)
        self.assertEqual(ivs["impliedVolatilityBid"], 0.19)
        self.assertEqual(ivs["impliedVolatilityMid"], 0.2)
        self.assertEqual(ivs["impliedVolatilityAsk"], 0.21)
        
        # Check that implied_volatility was called with the correct arguments
        mock_iv.assert_any_call(price=4.8, S=100.0, K=100.0, t=0.1, r=0.03, flag='c')  # Bid
        mock_iv.assert_any_call(price=5.0, S=100.0, K=100.0, t=0.1, r=0.03, flag='c')  # Mid
        mock_iv.assert_any_call(price=5.2, S=100.0, K=100.0, t=0.1, r=0.03, flag='c')  # Ask
    
    @patch('py_vollib.black_scholes.implied_volatility.implied_volatility')
    def test_calculate_implied_volatilities_with_zero_bid(self, mock_iv):
        """Test calculating implied volatilities with zero bid."""
        # Mock the implied_volatility function to return predictable values
        mock_iv.side_effect = [0.2, 0.21]
        
        option = {
            "strike": 100.0,
            "bid": 0.0,  # Zero bid
            "ask": 5.2,
            "impliedVolatility": 0.2
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100.0,
            time_to_expiration=0.1,
            risk_free_rate=0.03,
            option_type='c'
        )
        
        # Check that bid IV is None but other IVs are calculated
        self.assertEqual(ivs["impliedVolatilityYF"], 0.2)
        self.assertIsNone(ivs["impliedVolatilityBid"])
        self.assertEqual(ivs["impliedVolatilityMid"], 0.2)
        self.assertEqual(ivs["impliedVolatilityAsk"], 0.21)
        
        # Check that implied_volatility was called with the correct arguments
        # Should not be called for bid
        mock_iv.assert_any_call(price=5.2, S=100.0, K=100.0, t=0.1, r=0.03, flag='c')  # Ask
        mock_iv.assert_any_call(price=5.2, S=100.0, K=100.0, t=0.1, r=0.03, flag='c')  # Mid (same as ask when bid is 0)
    
    @patch('py_vollib.black_scholes.implied_volatility.implied_volatility')
    def test_calculate_implied_volatilities_with_exception(self, mock_iv):
        """Test calculating implied volatilities when an exception occurs."""
        # Mock the implied_volatility function to raise an exception
        mock_iv.side_effect = ValueError("Test exception")
        
        option = {
            "strike": 100.0,
            "bid": 4.8,
            "ask": 5.2,
            "impliedVolatility": 0.2
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100.0,
            time_to_expiration=0.1,
            risk_free_rate=0.03,
            option_type='c'
        )
        
        # Check that YF IV is preserved but other IVs are None
        self.assertEqual(ivs["impliedVolatilityYF"], 0.2)
        self.assertIsNone(ivs["impliedVolatilityBid"])
        self.assertIsNone(ivs["impliedVolatilityMid"])
        self.assertIsNone(ivs["impliedVolatilityAsk"])
    
    def test_process_options_with_iv_includes_new_fields(self):
        """Test that process_options_with_iv includes the new IV fields."""
        # Create a test option
        option = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=None,
            delta=None,
            option_type='c',
            bid=4.8,
            ask=5.2
        )
        
        # Mock the calculate_implied_volatility method to return a predictable value
        self.calculator.calculate_implied_volatility = MagicMock(return_value=0.2)
        self.calculator.calculate_delta = MagicMock(return_value=0.5)
        
        # Mock the calculate_implied_volatilities function
        with patch('src.utils.calculation_utils.calculate_implied_volatilities') as mock_calc_ivs:
            mock_calc_ivs.return_value = {
                'impliedVolatilityYF': 0.2,
                'impliedVolatilityBid': 0.19,
                'impliedVolatilityMid': 0.2,
                'impliedVolatilityAsk': 0.21
            }
            
            # Process the option
            processed_options = self.calculator.process_options_with_iv(
                options=[option],
                underlying_price=100.0,
                expiration_date='2025-08-01'
            )
        
        # Check that we have one processed option
        self.assertEqual(len(processed_options), 1)
        processed_option = processed_options[0]
        
        # Check that the processed option has the new IV fields
        self.assertEqual(processed_option.implied_volatility, 0.2)  # YF IV
        self.assertEqual(processed_option.implied_volatility_bid, 0.19)
        self.assertEqual(processed_option.implied_volatility_mid, 0.2)
        self.assertEqual(processed_option.implied_volatility_ask, 0.21)
        self.assertEqual(processed_option.mid_price, 5.0)  # (4.8 + 5.2) / 2


if __name__ == "__main__":
    unittest.main()