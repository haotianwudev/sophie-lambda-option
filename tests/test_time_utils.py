"""
Unit tests for time utility functions.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from src.utils.time_utils import (
    get_current_utc_timestamp,
    calculate_time_to_expiration,
    format_timestamp_for_api,
    parse_expiration_date
)


class TestTimeUtils:
    """Test cases for time utility functions."""
    
    def test_get_current_utc_timestamp(self):
        """Test getting current UTC timestamp."""
        timestamp = get_current_utc_timestamp()
        
        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo == timezone.utc
        
        # Should be close to current time (within 1 second)
        now = datetime.now(timezone.utc)
        time_diff = abs((timestamp - now).total_seconds())
        assert time_diff < 1.0
    
    def test_calculate_time_to_expiration_string_input(self):
        """Test calculating time to expiration with string input."""
        # Mock current time to a known value
        mock_current = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        with patch('src.utils.time_utils.get_current_utc_timestamp', return_value=mock_current):
            # Test with expiration 2 days in the future
            expiration = "2025-01-17"
            time_to_exp = calculate_time_to_expiration(expiration)
            
            # Should be approximately 1.5 days (since expiration is at start of day)
            # 2025-01-17 00:00:00 - 2025-01-15 12:00:00 = 1.5 days
            expected = 1.5 / 365.25
            assert abs(time_to_exp - expected) < 0.001
    
    def test_calculate_time_to_expiration_datetime_input(self):
        """Test calculating time to expiration with datetime input."""
        mock_current = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        with patch('src.utils.time_utils.get_current_utc_timestamp', return_value=mock_current):
            # Test with expiration 7 days in the future
            expiration = datetime(2025, 1, 22, 12, 0, 0, tzinfo=timezone.utc)
            time_to_exp = calculate_time_to_expiration(expiration)
            
            # Should be approximately 7 days = 7/365.25 years
            expected = 7 / 365.25
            assert abs(time_to_exp - expected) < 0.001
    
    def test_calculate_time_to_expiration_minimum_time(self):
        """Test that minimum time is enforced."""
        # Mock current time
        mock_current = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        with patch('src.utils.time_utils.get_current_utc_timestamp', return_value=mock_current):
            # Test with expiration in the past
            expiration = "2025-01-14"
            time_to_exp = calculate_time_to_expiration(expiration)
            
            # Should return minimum time (1 day)
            expected_minimum = 1 / 365.25
            assert time_to_exp == expected_minimum
    
    def test_format_timestamp_for_api(self):
        """Test formatting timestamp for API response."""
        timestamp = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        formatted = format_timestamp_for_api(timestamp)
        
        assert formatted == "2025-01-16T14:30:00Z"
    
    def test_format_timestamp_for_api_naive_datetime(self):
        """Test formatting naive datetime (no timezone)."""
        timestamp = datetime(2025, 1, 16, 14, 30, 0)
        formatted = format_timestamp_for_api(timestamp)
        
        assert formatted == "2025-01-16T14:30:00Z"
    
    def test_parse_expiration_date(self):
        """Test parsing expiration date string."""
        date_str = "2025-01-17"
        parsed = parse_expiration_date(date_str)
        
        assert isinstance(parsed, datetime)
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 17
        assert parsed.tzinfo == timezone.utc
    
    def test_parse_expiration_date_invalid_format(self):
        """Test parsing invalid date format."""
        with pytest.raises(ValueError):
            parse_expiration_date("01/17/2025")
        
        with pytest.raises(ValueError):
            parse_expiration_date("invalid-date")