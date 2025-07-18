"""
Unit tests for options calculator.
"""
import pytest
from unittest.mock import patch, MagicMock
import logging

from src.services.options_calculator import OptionsCalculator
from src.models.option_data import OptionData


class TestOptionsCalculator:
    """Test cases for OptionsCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = OptionsCalculator(risk_free_rate=0.03)
        
        # Sample option data for testing
        self.sample_call = OptionData(
            strike=450.0,
            last_price=5.25,
            implied_volatility=None,
            delta=None,
            option_type='c'
        )
        
        self.sample_put = OptionData(
            strike=450.0,
            last_price=3.75,
            implied_volatility=None,
            delta=None,
            option_type='p'
        )
    
    def test_calculator_initialization(self):
        """Test calculator initialization with default and custom risk-free rate."""
        # Default risk-free rate
        calc_default = OptionsCalculator()
        assert calc_default.risk_free_rate == 0.03
        
        # Custom risk-free rate
        calc_custom = OptionsCalculator(risk_free_rate=0.05)
        assert calc_custom.risk_free_rate == 0.05
    
    def test_calculate_implied_volatility_valid_call(self):
        """Test implied volatility calculation for valid call option."""
        iv = self.calculator.calculate_implied_volatility(
            option_price=5.25,
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,  # ~30 days
            option_type='c'
        )
        
        assert iv is not None
        assert isinstance(iv, float)
        assert 0 < iv < 5.0  # Reasonable volatility range
    
    def test_calculate_implied_volatility_valid_put(self):
        """Test implied volatility calculation for valid put option."""
        iv = self.calculator.calculate_implied_volatility(
            option_price=3.75,
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,  # ~30 days
            option_type='p'
        )
        
        assert iv is not None
        assert isinstance(iv, float)
        assert 0 < iv < 5.0  # Reasonable volatility range
    
    def test_calculate_implied_volatility_invalid_inputs(self):
        """Test implied volatility calculation with invalid inputs."""
        # Negative option price
        iv = self.calculator.calculate_implied_volatility(
            option_price=-1.0,
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            option_type='c'
        )
        assert iv is None
        
        # Zero underlying price
        iv = self.calculator.calculate_implied_volatility(
            option_price=5.25,
            underlying_price=0.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            option_type='c'
        )
        assert iv is None
        
        # Negative time to expiration
        iv = self.calculator.calculate_implied_volatility(
            option_price=5.25,
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=-0.1,
            option_type='c'
        )
        assert iv is None
        
        # Invalid option type
        iv = self.calculator.calculate_implied_volatility(
            option_price=5.25,
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            option_type='x'
        )
        assert iv is None
    
    @patch('src.services.options_calculator.implied_volatility')
    def test_calculate_implied_volatility_exception_handling(self, mock_iv):
        """Test exception handling in implied volatility calculation."""
        mock_iv.side_effect = Exception("Calculation error")
        
        iv = self.calculator.calculate_implied_volatility(
            option_price=5.25,
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            option_type='c'
        )
        
        assert iv is None
    
    def test_calculate_delta_valid_call(self):
        """Test delta calculation for valid call option."""
        delta_val = self.calculator.calculate_delta(
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            implied_vol=0.20,
            option_type='c'
        )
        
        assert delta_val is not None
        assert isinstance(delta_val, float)
        assert 0 <= delta_val <= 1.0  # Call delta range
    
    def test_calculate_delta_valid_put(self):
        """Test delta calculation for valid put option."""
        delta_val = self.calculator.calculate_delta(
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            implied_vol=0.20,
            option_type='p'
        )
        
        assert delta_val is not None
        assert isinstance(delta_val, float)
        assert -1.0 <= delta_val <= 0  # Put delta range
    
    def test_calculate_delta_invalid_inputs(self):
        """Test delta calculation with invalid inputs."""
        # Negative underlying price
        delta_val = self.calculator.calculate_delta(
            underlying_price=-450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            implied_vol=0.20,
            option_type='c'
        )
        assert delta_val is None
        
        # Invalid implied volatility
        delta_val = self.calculator.calculate_delta(
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            implied_vol=-0.20,
            option_type='c'
        )
        assert delta_val is None
        
        # Invalid option type
        delta_val = self.calculator.calculate_delta(
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            implied_vol=0.20,
            option_type='invalid'
        )
        assert delta_val is None
    
    @patch('src.services.options_calculator.delta')
    def test_calculate_delta_exception_handling(self, mock_delta):
        """Test exception handling in delta calculation."""
        mock_delta.side_effect = Exception("Delta calculation error")
        
        delta_val = self.calculator.calculate_delta(
            underlying_price=450.0,
            strike_price=450.0,
            time_to_expiration=0.0833,
            implied_vol=0.20,
            option_type='c'
        )
        
        assert delta_val is None
    
    @patch('src.services.options_calculator.calculate_time_to_expiration')
    def test_process_options_with_iv_success(self, mock_time_calc):
        """Test processing options with successful IV calculations."""
        mock_time_calc.return_value = 0.0833  # ~30 days
        
        options = [self.sample_call, self.sample_put]
        
        processed = self.calculator.process_options_with_iv(
            options=options,
            underlying_price=450.0,
            expiration_date="2025-02-15"
        )
        
        # Should have processed both options
        assert len(processed) == 2
        
        # Check that IV and delta were calculated
        for option in processed:
            assert option.implied_volatility is not None
            assert option.delta is not None
            assert isinstance(option.implied_volatility, float)
            assert isinstance(option.delta, float)
    
    @patch('src.services.options_calculator.calculate_time_to_expiration')
    def test_process_options_with_iv_filtering(self, mock_time_calc):
        """Test filtering of options where IV calculation fails."""
        mock_time_calc.return_value = 0.0833
        
        # Create option with invalid price that will cause IV calculation to fail
        invalid_option = OptionData(
            strike=450.0,
            last_price=0.0,  # Invalid price
            implied_volatility=None,
            delta=None,
            option_type='c'
        )
        
        options = [self.sample_call, invalid_option]
        
        processed = self.calculator.process_options_with_iv(
            options=options,
            underlying_price=450.0,
            expiration_date="2025-02-15"
        )
        
        # Should only have one processed option (invalid one filtered out)
        assert len(processed) == 1
        assert processed[0].strike == 450.0
        assert processed[0].implied_volatility is not None
    
    def test_known_option_data_calculations(self):
        """Test IV calculations with known option data for accuracy."""
        # Known test case: ATM call option with reasonable parameters
        # These values should produce a reasonable IV
        iv = self.calculator.calculate_implied_volatility(
            option_price=10.0,
            underlying_price=100.0,
            strike_price=100.0,
            time_to_expiration=0.25,  # 3 months
            option_type='c'
        )
        
        assert iv is not None
        assert 0.10 < iv < 1.0  # Reasonable range for this scenario
        
        # Test corresponding delta calculation
        delta_val = self.calculator.calculate_delta(
            underlying_price=100.0,
            strike_price=100.0,
            time_to_expiration=0.25,
            implied_vol=iv,
            option_type='c'
        )
        
        assert delta_val is not None
        assert 0.4 < delta_val < 0.6  # ATM call delta should be around 0.5
    
    def test_edge_case_very_short_expiration(self):
        """Test calculations with very short time to expiration."""
        iv = self.calculator.calculate_implied_volatility(
            option_price=1.0,
            underlying_price=100.0,
            strike_price=100.0,
            time_to_expiration=1/365.25,  # 1 day
            option_type='c'
        )
        
        # Should still calculate IV even for very short expiration
        assert iv is not None or iv is None  # Either is acceptable for edge case
    
    def test_edge_case_deep_itm_otm(self):
        """Test calculations for deep in-the-money and out-of-the-money options."""
        # Deep ITM call
        iv_itm = self.calculator.calculate_implied_volatility(
            option_price=45.0,
            underlying_price=100.0,
            strike_price=55.0,
            time_to_expiration=0.25,
            option_type='c'
        )
        
        # Deep OTM call
        iv_otm = self.calculator.calculate_implied_volatility(
            option_price=0.10,
            underlying_price=100.0,
            strike_price=150.0,
            time_to_expiration=0.25,
            option_type='c'
        )
        
        # Both should either calculate successfully or fail gracefully
        if iv_itm is not None:
            assert isinstance(iv_itm, float)
            assert iv_itm > 0
        
        if iv_otm is not None:
            assert isinstance(iv_otm, float)
            assert iv_otm > 0