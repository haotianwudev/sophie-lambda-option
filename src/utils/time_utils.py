"""
Utility functions for time calculations in options analytics.
"""
from datetime import datetime, timezone, timedelta
from typing import Union, List, Dict, Tuple


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


def calculate_days_to_expiration(expiration_date: Union[str, datetime]) -> int:
    """
    Calculate days to expiration from current date.
    
    Args:
        expiration_date: Expiration date as string (YYYY-MM-DD) or datetime
        
    Returns:
        Days to expiration as integer
    """
    if isinstance(expiration_date, str):
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        exp_date = exp_date.replace(tzinfo=timezone.utc)
    else:
        exp_date = expiration_date
        if exp_date.tzinfo is None:
            exp_date = exp_date.replace(tzinfo=timezone.utc)
    
    current_time = get_current_utc_timestamp()
    # Set current time to start of day for consistent day calculations
    current_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    exp_day = exp_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate difference in days
    days_diff = (exp_day - current_day).days
    
    return max(days_diff, 0)  # Ensure non-negative


def get_target_expiration_periods() -> Dict[str, int]:
    """
    Get target expiration periods for option filtering.
    
    Returns:
        Dictionary mapping period labels to days
    """
    return {
        "2w": 14,  # 2 weeks in days
        "1m": 30,  # 1 month in days
        "6w": 42,  # 6 weeks in days
        "2m": 60   # 2 months in days
    }


def calculate_target_dates(base_date: datetime = None) -> Dict[str, datetime]:
    """
    Calculate target dates for each expiration period.
    
    Args:
        base_date: Base date to calculate from (defaults to current UTC date)
        
    Returns:
        Dictionary mapping period labels to target dates
    """
    if base_date is None:
        base_date = get_current_utc_timestamp()
    
    target_periods = get_target_expiration_periods()
    target_dates = {}
    
    for label, days in target_periods.items():
        target_dates[label] = base_date + timedelta(days=days)
    
    return target_dates


def find_closest_expiration_dates(
    all_expirations: List[str], 
    base_date: datetime = None
) -> Dict[str, Tuple[str, int]]:
    """
    Find closest expiration dates to target periods.
    
    Args:
        all_expirations: List of all available expiration dates as strings (YYYY-MM-DD)
        base_date: Base date to calculate from (defaults to current UTC date)
        
    Returns:
        Dictionary mapping period labels to tuples of (expiration_date, days_to_expiration)
    """
    if base_date is None:
        base_date = get_current_utc_timestamp()
    
    # Convert string dates to datetime objects
    exp_dates = [parse_expiration_date(exp) for exp in all_expirations]
    
    # Calculate target dates
    target_dates = calculate_target_dates(base_date)
    result = {}
    
    for label, target_date in target_dates.items():
        # Find closest expiration date to target date
        if not exp_dates:
            continue
            
        closest_exp = min(exp_dates, key=lambda x: abs((x - target_date).days))
        closest_exp_str = closest_exp.strftime("%Y-%m-%d")
        days_to_exp = calculate_days_to_expiration(closest_exp)
        
        result[label] = (closest_exp_str, days_to_exp)
    
    return result


def format_last_trade_date(last_trade_timestamp: Union[str, datetime]) -> str:
    """
    Format last trade date for API response.
    
    Args:
        last_trade_timestamp: Last trade timestamp as string or datetime
        
    Returns:
        ISO formatted timestamp string
    """
    if isinstance(last_trade_timestamp, str):
        try:
            # Try to parse as ISO format
            dt = datetime.fromisoformat(last_trade_timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Try to parse as Unix timestamp
            try:
                dt = datetime.fromtimestamp(float(last_trade_timestamp), tz=timezone.utc)
            except ValueError:
                # Return as is if parsing fails
                return last_trade_timestamp
    else:
        dt = last_trade_timestamp
        
    return format_timestamp_for_api(dt)