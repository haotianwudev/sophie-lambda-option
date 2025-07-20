"""
Tests for time utility functions.
"""
import unittest
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
from src.utils.time_utils import (
    get_current_utc_timestamp,
    calculate_time_to_expiration,
    format_timestamp_for_api,
    parse_expiration_date,
    calculate_days_to_expiration,
    get_target_expiration_periods,
    calculate_target_dates,
    find_closest_expiration_dates,
    format_last_trade_date
)


class TestTimeUtils(unittest.TestCase):
    """Test cases for time utility functions."""
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_get_current_utc_timestamp(self):
        """Test getting current UTC timestamp."""
        timestamp = get_current_utc_timestamp()
        expected = datetime(2025, 7, 18, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(timestamp, expected)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_calculate_time_to_expiration_string(self):
        """Test calculating time to expiration from string date."""
        # Test with string date
        time_to_exp = calculate_time_to_expiration("2025-08-15")
        # Expected: ~28 days / 365.25 = ~0.0753 years
        self.assertAlmostEqual(time_to_exp, 0.0753, places=3)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_calculate_time_to_expiration_datetime(self):
        """Test calculating time to expiration from datetime."""
        # Test with datetime object
        exp_date = datetime(2025, 8, 15, tzinfo=timezone.utc)
        time_to_exp = calculate_time_to_expiration(exp_date)
        # Expected: ~28 days / 365.25 = ~0.0753 years
        self.assertAlmostEqual(time_to_exp, 0.0753, places=3)
    
    def test_format_timestamp_for_api(self):
        """Test formatting timestamp for API."""
        dt = datetime(2025, 7, 18, 12, 30, 45, 123456, tzinfo=timezone.utc)
        formatted = format_timestamp_for_api(dt)
        self.assertEqual(formatted, "2025-07-18T12:30:45.123456Z")
        
        # Test with naive datetime
        dt_naive = datetime(2025, 7, 18, 12, 30, 45, 123456)
        formatted_naive = format_timestamp_for_api(dt_naive)
        self.assertEqual(formatted_naive, "2025-07-18T12:30:45.123456Z")
    
    def test_parse_expiration_date(self):
        """Test parsing expiration date string."""
        dt = parse_expiration_date("2025-08-15")
        expected = datetime(2025, 8, 15, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(dt, expected)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_calculate_days_to_expiration(self):
        """Test calculating days to expiration."""
        # Test with string date
        days = calculate_days_to_expiration("2025-08-15")
        self.assertEqual(days, 28)
        
        # Test with datetime object
        exp_date = datetime(2025, 8, 15, tzinfo=timezone.utc)
        days = calculate_days_to_expiration(exp_date)
        self.assertEqual(days, 28)
        
        # Test with past date
        past_date = datetime(2025, 7, 15, tzinfo=timezone.utc)
        days = calculate_days_to_expiration(past_date)
        self.assertEqual(days, 0)  # Should return 0 for past dates
    
    def test_get_target_expiration_periods(self):
        """Test getting target expiration periods."""
        periods = get_target_expiration_periods()
        expected = {
            "2w": 14,
            "1m": 30,
            "6w": 42,
            "2m": 60
        }
        self.assertEqual(periods, expected)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_calculate_target_dates(self):
        """Test calculating target dates."""
        target_dates = calculate_target_dates()
        
        # Expected dates
        expected = {
            "2w": datetime(2025, 8, 1, 12, 0, 0, tzinfo=timezone.utc),
            "1m": datetime(2025, 8, 17, 12, 0, 0, tzinfo=timezone.utc),
            "6w": datetime(2025, 8, 29, 12, 0, 0, tzinfo=timezone.utc),
            "2m": datetime(2025, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
        }
        
        self.assertEqual(target_dates, expected)
        
        # Test with custom base date
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        target_dates = calculate_target_dates(base_date)
        
        # Expected dates with custom base
        expected = {
            "2w": datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            "1m": datetime(2025, 1, 31, 0, 0, 0, tzinfo=timezone.utc),
            "6w": datetime(2025, 2, 12, 0, 0, 0, tzinfo=timezone.utc),
            "2m": datetime(2025, 3, 2, 0, 0, 0, tzinfo=timezone.utc)
        }
        
        self.assertEqual(target_dates, expected)
    
    @freeze_time("2025-07-18 12:00:00", tz_offset=0)
    def test_find_closest_expiration_dates(self):
        """Test finding closest expiration dates."""
        # Available expiration dates
        all_expirations = [
            "2025-07-25",  # 1 week
            "2025-08-01",  # 2 weeks
            "2025-08-15",  # ~4 weeks
            "2025-09-05",  # ~7 weeks
            "2025-09-19"   # ~9 weeks
        ]
        
        closest_dates = find_closest_expiration_dates(all_expirations)
        
        # Expected closest dates
        expected = {
            "2w": ("2025-08-01", 14),  # Exact match for 2 weeks
            "1m": ("2025-08-15", 28),  # Closest to 1 month (30 days)
            "6w": ("2025-09-05", 49),  # Closest to 6 weeks (42 days)
            "2m": ("2025-09-19", 63)   # Closest to 2 months (60 days)
        }
        
        self.assertEqual(closest_dates, expected)
        
        # Test with empty list
        empty_result = find_closest_expiration_dates([])
        self.assertEqual(empty_result, {})
    
    def test_format_last_trade_date(self):
        """Test formatting last trade date."""
        # Test with ISO format string
        iso_str = "2025-07-18T12:30:45.123456+00:00"
        formatted = format_last_trade_date(iso_str)
        self.assertEqual(formatted, "2025-07-18T12:30:45.123456Z")
        
        # Test with datetime object
        dt = datetime(2025, 7, 18, 12, 30, 45, 123456, tzinfo=timezone.utc)
        formatted = format_last_trade_date(dt)
        self.assertEqual(formatted, "2025-07-18T12:30:45.123456Z")
        
        # Test with invalid string
        invalid_str = "invalid-date"
        formatted = format_last_trade_date(invalid_str)
        self.assertEqual(formatted, "invalid-date")


if __name__ == "__main__":
    unittest.main()