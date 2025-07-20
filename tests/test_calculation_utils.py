"""
Tests for calculation utility functions.
"""
import unittest
from src.utils.calculation_utils import (
    calculate_percentage_change,
    calculate_mid_price,
    calculate_moneyness,
    is_within_moneyness_range,
    filter_options_by_moneyness,
    safe_float_conversion,
    calculate_implied_volatilities
)


class TestCalculationUtils(unittest.TestCase):
    """Test cases for calculation utility functions."""
    
    def test_calculate_percentage_change(self):
        """Test calculating percentage change."""
        # Test positive change
        self.assertEqual(calculate_percentage_change(110, 100), 10.0)
        
        # Test negative change
        self.assertEqual(calculate_percentage_change(90, 100), -10.0)
        
        # Test no change
        self.assertEqual(calculate_percentage_change(100, 100), 0.0)
        
        # Test with zero previous value
        self.assertEqual(calculate_percentage_change(100, 0), 0.0)
        
        # Test with decimal values
        self.assertEqual(calculate_percentage_change(105.5, 100), 5.5)
        
        # Test rounding
        self.assertEqual(calculate_percentage_change(100.123, 100), 0.12)
    
    def test_calculate_mid_price(self):
        """Test calculating mid price."""
        # Test normal case
        self.assertEqual(calculate_mid_price(10, 11), 10.5)
        
        # Test with zero bid
        self.assertEqual(calculate_mid_price(0, 10), 10)
        
        # Test with zero ask
        self.assertEqual(calculate_mid_price(10, 0), 10)
        
        # Test with both zero
        self.assertEqual(calculate_mid_price(0, 0), 0.0)
        
        # Test with None values
        self.assertEqual(calculate_mid_price(None, 10), 0.0)
        self.assertEqual(calculate_mid_price(10, None), 0.0)
        self.assertEqual(calculate_mid_price(None, None), 0.0)
    
    def test_calculate_moneyness(self):
        """Test calculating moneyness."""
        # Test at the money
        self.assertEqual(calculate_moneyness(100, 100), 1.0)
        
        # Test in the money (for calls)
        self.assertEqual(calculate_moneyness(90, 100), 0.9)
        
        # Test out of the money (for calls)
        self.assertEqual(calculate_moneyness(110, 100), 1.1)
        
        # Test with zero current price
        self.assertEqual(calculate_moneyness(100, 0), 0.0)
        
        # Test rounding
        self.assertEqual(calculate_moneyness(123.456, 100), 1.235)
    
    def test_is_within_moneyness_range(self):
        """Test checking if moneyness is within range."""
        # Test within default range
        self.assertTrue(is_within_moneyness_range(0.85))
        self.assertTrue(is_within_moneyness_range(1.0))
        self.assertTrue(is_within_moneyness_range(1.15))
        
        # Test outside default range
        self.assertFalse(is_within_moneyness_range(0.84))
        self.assertFalse(is_within_moneyness_range(1.16))
        
        # Test with custom range
        self.assertTrue(is_within_moneyness_range(0.9, min_moneyness=0.9, max_moneyness=1.1))
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
            {"no_strike": "invalid"}
        ]
        
        current_price = 100
        
        # Test with default range (0.85 to 1.15)
        filtered = filter_options_by_moneyness(options, current_price)
        
        # Should include strikes 85, 90, 100, 110, 115 (if it existed)
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
    
    def test_safe_float_conversion(self):
        """Test safe float conversion."""
        # Test with valid float
        self.assertEqual(safe_float_conversion(10.5), 10.5)
        
        # Test with valid int
        self.assertEqual(safe_float_conversion(10), 10.0)
        
        # Test with valid string
        self.assertEqual(safe_float_conversion("10.5"), 10.5)
        
        # Test with None
        self.assertEqual(safe_float_conversion(None), 0.0)
        
        # Test with invalid string
        self.assertEqual(safe_float_conversion("invalid"), 0.0)
        
        # Test with other types
        self.assertEqual(safe_float_conversion([]), 0.0)
        self.assertEqual(safe_float_conversion({}), 0.0)
    
    def test_calculate_implied_volatilities(self):
        """Test calculating implied volatilities."""
        # Test option with all fields
        option = {
            "strike": 100,
            "bid": 5.0,
            "ask": 5.5,
            "impliedVolatility": 0.2
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100,
            time_to_expiration=0.1,
            risk_free_rate=0.05,
            option_type="c"  # Use 'c' for call instead of "call"
        )
        
        # Check that all IV fields are present
        self.assertIn("impliedVolatilityYF", ivs)
        self.assertIn("impliedVolatilityBid", ivs)
        self.assertIn("impliedVolatilityMid", ivs)
        self.assertIn("impliedVolatilityAsk", ivs)
        
        # Check values - we're now using py_vollib for actual calculations
        # so we just check that the values are present and reasonable
        self.assertEqual(ivs["impliedVolatilityYF"], 0.2)
        self.assertIsNotNone(ivs["impliedVolatilityBid"])
        self.assertIsNotNone(ivs["impliedVolatilityMid"])
        self.assertIsNotNone(ivs["impliedVolatilityAsk"])
        
        # Test option with zero IV
        option = {
            "strike": 100,
            "bid": 5.0,
            "ask": 5.5,
            "impliedVolatility": 0.0
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100,
            time_to_expiration=0.1,
            risk_free_rate=0.05,
            option_type="c"
        )
        
        # Check that all IV fields are present but None or 0
        self.assertEqual(ivs["impliedVolatilityYF"], 0.0)
        # We should still get values for bid, mid, and ask IVs since we have valid prices
        self.assertIsNotNone(ivs["impliedVolatilityBid"])
        self.assertIsNotNone(ivs["impliedVolatilityMid"])
        self.assertIsNotNone(ivs["impliedVolatilityAsk"])
        
        # Test option with missing IV
        option = {
            "strike": 100,
            "bid": 5.0,
            "ask": 5.5
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100,
            time_to_expiration=0.1,
            risk_free_rate=0.05,
            option_type="c"
        )
        
        # Check that all IV fields are present with appropriate values
        self.assertEqual(ivs["impliedVolatilityYF"], 0.0)
        # We should still get values for bid, mid, and ask IVs since we have valid prices
        self.assertIsNotNone(ivs["impliedVolatilityBid"])
        self.assertIsNotNone(ivs["impliedVolatilityMid"])
        self.assertIsNotNone(ivs["impliedVolatilityAsk"])
        
        # Test with invalid inputs
        option = {
            "strike": 0,  # Invalid strike
            "bid": 5.0,
            "ask": 5.5,
            "impliedVolatility": 0.2
        }
        
        ivs = calculate_implied_volatilities(
            option,
            current_price=100,
            time_to_expiration=0.1,
            risk_free_rate=0.05,
            option_type="c"
        )
        
        # Check that YF IV is preserved but other IVs are None
        self.assertEqual(ivs["impliedVolatilityYF"], 0.2)
        self.assertIsNone(ivs["impliedVolatilityBid"])
        self.assertIsNone(ivs["impliedVolatilityMid"])
        self.assertIsNone(ivs["impliedVolatilityAsk"])


if __name__ == "__main__":
    unittest.main()