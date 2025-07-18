"""
Utility functions for time calculations in options analytics.
"""
from datetime import datetime, timezone
from typing import Union


def get_current_utc_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def calculate_time_to_expiration(expiration_date: Union[str, datetime]) -> float:
    """
    Calculate time to expiration in years.
    
    Args:
        expiration_date: Expiration date as string (YYYY-MM-DD) or datetime
        
    Returns:
        Time to expiration in years (float)
    """
    if isinstance(expiration_date, str):
        # Parse date string in format YYYY-MM-DD
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        exp_date = exp_date.replace(tzinfo=timezone.utc)
    else:
        exp_date = expiration_date
        if exp_date.tzinfo is None:
            exp_date = exp_date.replace(tzinfo=timezone.utc)
    
    current_time = get_current_utc_timestamp()
    time_diff = exp_date - current_time
    
    # Convert to years (365.25 days per year to account for leap years)
    years = time_diff.total_seconds() / (365.25 * 24 * 3600)
    
    # Ensure minimum time to avoid division by zero in calculations
    return max(years, 1/365.25)  # Minimum 1 day


def format_timestamp_for_api(timestamp: datetime) -> str:
    """
    Format timestamp for API response.
    
    Args:
        timestamp: Datetime object to format
        
    Returns:
        ISO formatted timestamp string
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    return timestamp.isoformat().replace('+00:00', 'Z')


def parse_expiration_date(expiration_str: str) -> datetime:
    """
    Parse expiration date string to datetime object.
    
    Args:
        expiration_str: Date string in format YYYY-MM-DD
        
    Returns:
        Datetime object with UTC timezone
    """
    parsed_date = datetime.strptime(expiration_str, "%Y-%m-%d")
    return parsed_date.replace(tzinfo=timezone.utc)