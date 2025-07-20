"""
Tests for expiration date selection and filtering.
"""
import unittest
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
from src.utils.expiration_selector import (
    select_target_expiration_dates,
    filter_expirations_by_target_periods
)
from src.models.option_data import ExpirationData, OptionData


class TestExpirationSelector(unittest.TestCase):
    """Test cases for expiration date selection and filtering."""
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_select_target_expiration_dates(self):
        """Test selecting target expiration dates."""
        # Available expiration dates
        all_expirations = [
            "2025-07-25",  # 1 week
            "2025-08-01",  # 2 weeks
            "2025-08-15",  # ~4 weeks
            "2025-09-05",  # ~7 weeks
            "2025-09-19"   # ~9 weeks
        ]
        
        target_dates = select_target_expiration_dates(all_expirations)
        
        # Expected closest dates
        expected = {
            "2w": ("2025-08-01", 14),  # Exact match for 2 weeks
            "1m": ("2025-08-15", 28),  # Closest to 1 month (30 days)
            "6w": ("2025-09-05", 49),  # Closest to 6 weeks (42 days)
            "2m": ("2025-09-19", 63)   # Closest to 2 months (60 days)
        }
        
        self.assertEqual(target_dates, expected)
    
    def test_select_target_expiration_dates_empty(self):
        """Test selecting target expiration dates with empty list."""
        with self.assertRaises(ValueError):
            select_target_expiration_dates([])
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_filter_expirations_by_target_periods(self):
        """Test filtering expiration dates by target periods."""
        # Create sample option data
        sample_option = OptionData(
            strike=100.0,
            last_price=5.0,
            implied_volatility=0.2,
            delta=0.5,
            option_type='c'
        )
        
        # Create sample expiration data objects
        expiration_data_list = [
            ExpirationData(expiration="2025-07-25", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-08-01", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-08-15", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-09-05", calls=[sample_option], puts=[sample_option]),
            ExpirationData(expiration="2025-09-19", calls=[sample_option], puts=[sample_option])
        ]
        
        filtered_expirations = filter_expirations_by_target_periods(expiration_data_list)
        
        # Should have 4 expirations (one for each target period)
        self.assertEqual(len(filtered_expirations), 4)
        
        # Check that each expiration has the correct label and days
        expected_labels = {
            "2025-08-01": "2w",
            "2025-08-15": "1m",
            "2025-09-05": "6w",
            "2025-09-19": "2m"
        }
        
        expected_days = {
            "2025-08-01": 14,
            "2025-08-15": 28,
            "2025-09-05": 49,
            "2025-09-19": 63
        }
        
        for exp_data in filtered_expirations:
            self.assertIn(exp_data.expiration, expected_labels)
            self.assertEqual(exp_data.expiration_label, expected_labels[exp_data.expiration])
            self.assertEqual(exp_data.days_to_expiration, expected_days[exp_data.expiration])
    
    def test_filter_expirations_by_target_periods_empty(self):
        """Test filtering expiration dates with empty list."""
        with self.assertRaises(ValueError):
            filter_expirations_by_target_periods([])


if __name__ == "__main__":
    unittest.main()