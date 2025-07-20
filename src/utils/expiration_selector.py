"""
Utility functions for selecting and filtering option expiration dates.
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from src.models.option_data import ExpirationData
from src.utils.time_utils import (
    get_current_utc_timestamp,
    parse_expiration_date,
    calculate_days_to_expiration,
    find_closest_expiration_dates
)


def select_target_expiration_dates(
    all_expirations: List[str],
    base_date: Optional[datetime] = None
) -> Dict[str, Tuple[str, int]]:
    """
    Select target expiration dates based on predefined periods.
    
    Args:
        all_expirations: List of all available expiration dates as strings (YYYY-MM-DD)
        base_date: Base date to calculate from (defaults to current UTC date)
        
    Returns:
        Dictionary mapping period labels to tuples of (expiration_date, days_to_expiration)
        
    Raises:
        ValueError: If no valid expiration dates are provided
    """
    if not all_expirations:
        raise ValueError("No expiration dates provided")
    
    # Use the time_utils function to find closest expiration dates
    return find_closest_expiration_dates(all_expirations, base_date)


def filter_expirations_by_target_periods(
    expiration_data_list: List[ExpirationData]
) -> List[ExpirationData]:
    """
    Filter expiration dates to include only those closest to target periods.
    
    Args:
        expiration_data_list: List of ExpirationData objects
        
    Returns:
        Filtered list of ExpirationData objects with added labels and days to expiration
        
    Raises:
        ValueError: If no valid expiration dates are provided
    """
    if not expiration_data_list:
        raise ValueError("No expiration data provided")
    
    # Extract all expiration dates
    all_expirations = [exp.expiration for exp in expiration_data_list]
    
    # Find closest expiration dates to target periods
    target_expirations = select_target_expiration_dates(all_expirations)
    
    # Create a mapping of expiration date to label and days
    expiration_mapping = {}
    for label, (exp_date, days) in target_expirations.items():
        expiration_mapping[exp_date] = (label, days)
    
    # Filter and enhance expiration data
    filtered_expirations = []
    for exp_data in expiration_data_list:
        if exp_data.expiration in expiration_mapping:
            label, days = expiration_mapping[exp_data.expiration]
            exp_data.expiration_label = label
            exp_data.days_to_expiration = days
            filtered_expirations.append(exp_data)
    
    # Sort by days to expiration
    filtered_expirations.sort(key=lambda x: x.days_to_expiration)
    
    return filtered_expirations